# asistido por SI: Claude Code (Anthropic), escritura y revisión de código; base del prototipo migrada en el hackatón
import json
import re
from dataclasses import replace
import sqlite3
import subprocess
import zipfile
from datetime import datetime, timezone
from pathlib import Path

import geopandas as gpd
import pandas as pd
import pyogrio
import requests
import shapely

from simulacion.config import CRUDOS, CRS_AREA, CRS_SALIDA, GEO_SQLITE, PROCESADOS
from simulacion.geo.descargas import (MANIFIESTO, Recurso, cargar_manifiesto,
                                      registrar_hash, sha256_archivo, _descargar)
from simulacion.geo.normalizar import normalizar_nombre

COLUMNAS = ["id", "nivel", "iso3", "padre_id", "nombre", "nombre_ascii", "nombre_es",
            "nombre_en", "area_km2", "punto_lat", "punto_lon", "fuente_limite",
            "licencia_limite", "cruce_ambiguo", "bbox_oeste", "bbox_sur", "bbox_este", "bbox_norte"]
# gbOpen usa XKX para Kosovo y GADM XKO: sin alias, gbOpen volvería a rellenar Kosovo
ALIAS_ISO = {"XKX": "XKO"}
INVALIDOS = {"", "na", "n.a.", "?"}


def nombre_valido(s: str | None) -> bool:
    return isinstance(s, str) and s.strip().lower() not in INVALIDOS


def leer_gadm_nivel(ruta_zip: Path, nivel: int) -> gpd.GeoDataFrame:
    # vsizip sobre el zip completo es lentísimo; con el .gpkg extraído se lee directo
    ruta = Path(ruta_zip).as_posix()
    if not ruta.endswith(".gpkg"):
        ruta = f"/vsizip/{ruta}/gadm_410-levels.gpkg"
    return pyogrio.read_dataframe(ruta, layer=f"ADM_{nivel}")


def asignar_padre_espacial(hijos: gpd.GeoDataFrame, padres: gpd.GeoDataFrame) -> pd.DataFrame:
    puntos = gpd.GeoDataFrame(geometry=hijos.geometry.representative_point(), crs=hijos.crs)
    puntos["i"] = range(len(puntos))
    union = gpd.sjoin(puntos, padres[["id", "geometry"]], how="left", predicate="within")
    por_hijo = union.groupby("i")["id"].agg(lambda s: list(s.dropna()))
    padre = [p[0] if len(p) == 1 else None for p in por_hijo.reindex(range(len(puntos)))]
    return pd.DataFrame({"padre_id": padre,
                         "cruce_ambiguo": [0 if p is not None else 1 for p in padre]},
                        index=hijos.index)


def _geometria_derivada(gdf: gpd.GeoDataFrame):
    # punto interior en EPSG:4326 y área en Mollweide (igual área)
    pts = gdf.geometry.representative_point()
    area = gdf.geometry.to_crs(CRS_AREA).area / 1e6
    return (pd.Series(pts.y.values, index=gdf.index), pd.Series(pts.x.values, index=gdf.index),
            pd.Series(area.values, index=gdf.index))


def _reparar(gdf: gpd.GeoDataFrame) -> int:
    # vectorizado con shapely 2: solo se repara lo inválido
    geoms = gdf.geometry.values.copy()
    malas = ~shapely.is_valid(geoms)
    if malas.any():
        geoms[malas] = shapely.make_valid(geoms[malas])
        gdf["geometry"] = geoms
    return int(malas.sum())


def _gid_padre(gid1, gid2, iso3):
    # GADM trae GID_1 = "NA" en 2 ADM2 de GBR; el padre sale del propio GID_2 ("GBR.1.6_1" -> "GBR.1_1")
    if nombre_valido(gid1):
        return gid1
    p = gid2.split(".") if nombre_valido(gid2) else []
    return f"{p[0]}.{p[1].split('_')[0]}_1" if len(p) >= 3 else _gid(gid1, iso3, 1)


def _gid(gid, iso3, nivel):
    # GADM trae un GID "?" en una astilla de UKR; se le da un id propio y único por país y nivel
    return gid if nombre_valido(gid) else f"{iso3}.sin_gid_{nivel}"


def _nombre(s, tipo, id_):
    return s if nombre_valido(s) else f"{tipo if nombre_valido(tipo) else 'Unidad'} {id_}"


def marcar_disputadas(t: pd.DataFrame) -> int:
    # zonas en disputa de GADM (GID_0 = Z01..Z09): nivel 9 según INICIAR 8.3
    m = t["id"].str.match(r"^Z\d{2}$")
    t.loc[m, "nivel"] = 9
    if "nombre" in t:  # nombre neutro: el original de GADM no se muestra
        t.loc[m, "nombre"] = "Zona en disputa (" + t.loc[m, "id"] + ")"
        t.loc[m, "nombre_ascii"] = t.loc[m, "nombre"].map(normalizar_nombre)
    return int(m.sum())


def filtrar_hijas_validas(g: pd.DataFrame, ids_paises: set):
    # descarta filas cuyo GID_0 no es un país de nivel 0: las de GID_0 "NA" (sin país en ADM0)
    # y las hijas de zonas en disputa (nivel 9 no puede ser padre). Devuelve (filas, n_na, n_disputa)
    huerfanas = ~g["GID_0"].isin(ids_paises)
    disputa = huerfanas & g["GID_0"].str.match(r"^Z\d{2}$")
    return g[~huerfanas].reset_index(drop=True), int((huerfanas & ~disputa).sum()), int(disputa.sum())


def asegurar_gpkg(ruta_zip: Path, ruta_gpkg: Path) -> Path:
    # extrae una sola vez el .gpkg del zip; /vsizip/ sobre 2,7 GB es órdenes de magnitud más lento
    ruta_gpkg = Path(ruta_gpkg)
    if not ruta_gpkg.exists():
        ruta_gpkg.parent.mkdir(parents=True, exist_ok=True)
        tmp = ruta_gpkg.with_name(ruta_gpkg.name + ".parcial")
        with zipfile.ZipFile(ruta_zip) as z, z.open(ruta_gpkg.name) as src, open(tmp, "wb") as dst:
            while b := src.read(1 << 24):
                dst.write(b)
        tmp.replace(ruta_gpkg)
    return ruta_gpkg


def _tabla(gdf, nivel, ids, padre, nombres, iso3, fuente, licencia) -> gpd.GeoDataFrame:
    lat, lon, area = _geometria_derivada(gdf)
    # EPSG:4326; las unidades que cruzan el antimeridiano dan -180..180
    b = gdf.geometry.bounds
    return gpd.GeoDataFrame({
        "id": list(ids), "nivel": nivel, "iso3": list(iso3), "padre_id": padre,
        "nombre": nombres, "nombre_ascii": [normalizar_nombre(n) for n in nombres],
        "nombre_es": None, "nombre_en": None, "area_km2": area.values,
        "punto_lat": lat.values, "punto_lon": lon.values, "fuente_limite": fuente,
        "licencia_limite": licencia, "cruce_ambiguo": 0,
        "bbox_oeste": b.minx.values, "bbox_sur": b.miny.values,
        "bbox_este": b.maxx.values, "bbox_norte": b.maxy.values,
    }, geometry=gdf.geometry.values, crs=CRS_SALIDA)


def _nombres_ne(ruta_ne1: Path) -> dict:
    ne = pyogrio.read_dataframe(f"/vsizip/{Path(ruta_ne1).as_posix()}",
                                columns=["adm0_a3", "name", "name_es", "name_en"],
                                read_geometry=False)
    claves = {}
    for r in ne.itertuples():
        claves.setdefault((r.adm0_a3, normalizar_nombre(r.name)), (r.name_es, r.name_en))
    return claves


def _registrar_gb(meta: dict) -> Recurso:
    id_ = f"gbopen_{meta['boundaryISO']}_adm2"
    lic = f"gbOpen {meta['boundaryLicense']}"
    texto = MANIFIESTO.read_text(encoding="utf-8")
    if f"- id: {id_}\n" not in texto:
        bloque = (f"- id: {id_}\n  url: {meta['gjDownloadURL']}\n  archivo: {id_}.geojson\n"
                  f"  licencia: {lic}\n  ficha: datos/fichas/gbopen_adm2.md\n"
                  f"  sha256: null\n  bytes_esperados: null\n")
        MANIFIESTO.write_text(texto.rstrip("\n") + "\n" + bloque, encoding="utf-8")
    return next(r for r in cargar_manifiesto(MANIFIESTO) if r.id == id_)


def descargar_con_alterna(r: Recurso, dir_gb: Path, alt: str | None = None, esquemas=("https",)) -> Path:
    # github.com/raw da 5xx persistente en archivos grandes; media.githubusercontent.com sirve el mismo commit.
    # Solo se reintenta ante 5xx (un 404 se propaga) y el manifiesto conserva la URL original.
    try:
        return _descargar(r, dir_gb, esquemas)
    except requests.HTTPError as e:
        if e.response is None or e.response.status_code < 500:
            raise
        alt = alt or r.url.replace("https://github.com/", "https://media.githubusercontent.com/media/").replace("/raw/", "/")
        return _descargar(replace(r, url=alt), dir_gb, esquemas)


def _relleno_gb(meta: dict, adm1: gpd.GeoDataFrame, dir_gb: Path):
    iso = meta["boundaryISO"]
    r = _registrar_gb(meta)
    ruta = descargar_con_alterna(r, dir_gb)
    if r.sha256 is None:
        registrar_hash(MANIFIESTO, r.id, sha256_archivo(ruta))
    g = pyogrio.read_dataframe(ruta).to_crs(CRS_SALIDA)
    n = _reparar(g)
    ids = ["gb:" + s for s in g["shapeID"]]
    t = _tabla(g, 2, ids, None, [_nombre(s, None, i) for s, i in zip(g["shapeName"], ids)],
               [iso] * len(g), "geoBoundaries gbOpen ADM2", meta["boundaryLicense"])
    padres = adm1[adm1.iso3 == iso]
    if len(padres):
        p = asignar_padre_espacial(t, padres)
        t["padre_id"], t["cruce_ambiguo"] = p.padre_id, p.cruce_ambiguo
    else:
        t["cruce_ambiguo"] = 1
    return t, n


def construir_unidades(ruta_gadm: Path, ruta_ne1: Path, ruta_gb_meta: Path, dir_gb: Path) -> gpd.GeoDataFrame:
    reparadas, descartadas, descartadas_disputa, partes, stats = 0, 0, 0, [], {}
    for nivel in (0, 1, 2):
        g = leer_gadm_nivel(ruta_gadm, nivel).to_crs(CRS_SALIDA)
        reparadas += _reparar(g)
        gid = f"GID_{nivel}"
        if nivel > 0:
            # se descartan filas sin país en ADM0 y las hijas de zonas en disputa (ver filtrar_hijas_validas)
            g, n_na, n_disp = filtrar_hijas_validas(g, set(partes[0].id[partes[0].nivel == 0]))
            descartadas += n_na
            descartadas_disputa += n_disp
            if nivel == 2:
                g["GID_1"] = [_gid_padre(a, b, i) for a, b, i in zip(g.GID_1, g.GID_2, g.GID_0)]
                g[gid] = [_gid(a, i, 2) for a, i in zip(g[gid], g.GID_0)]
            else:
                g[gid] = [_gid(a, i, 1) for a, i in zip(g[gid], g.GID_0)]
        if nivel == 0:
            t = _tabla(g, 0, g[gid], None,
                       [_nombre(s, None, i) for s, i in zip(g["COUNTRY"], g[gid])],
                       g[gid], "GADM 4.1", "GADM, no comercial")
            stats["disputadas"] = marcar_disputadas(t)
        else:
            t = _tabla(g, nivel, g[gid], list(g["GID_0" if nivel == 1 else "GID_1"]),
                       [_nombre(s, ty, i) for s, ty, i in zip(g[f"NAME_{nivel}"], g[f"TYPE_{nivel}"], g[gid])],
                       g["GID_0"], "GADM 4.1", "GADM, no comercial")
        if nivel == 1:
            ne = _nombres_ne(ruta_ne1)
            pares = [ne.get((i, normalizar_nombre(n))) for i, n in zip(t.iso3, g["NAME_1"])]
            t["nombre_es"] = [p[0] if p else None for p in pares]
            t["nombre_en"] = [p[1] if p else None for p in pares]
            stats["ne_coinciden"] = sum(p is not None for p in pares)
            stats["ne_total"] = len(pares)
        partes.append(t)
        del g
    adm1 = partes[1]
    metas = json.loads(Path(ruta_gb_meta).read_text(encoding="utf-8"))
    con_gadm = set(partes[2].iso3)
    rellenados = []
    for m in metas:
        if ALIAS_ISO.get(m["boundaryISO"], m["boundaryISO"]) not in con_gadm:
            t, n = _relleno_gb(m, adm1, dir_gb)
            partes.append(t)
            reparadas += n
            rellenados.append(m["boundaryISO"])
    out = pd.concat(partes, ignore_index=True)
    out = gpd.GeoDataFrame(out[COLUMNAS + ["geometry"]], geometry="geometry", crs=CRS_SALIDA)
    out.attrs.update(stats, rellenados=rellenados, reparadas=reparadas, descartadas=descartadas, descartadas_disputa=descartadas_disputa)
    return out


def escribir_geo_sqlite(unidades: gpd.GeoDataFrame, ruta: Path) -> None:
    Path(ruta).parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(ruta)
    try:
        con.executescript((Path(__file__).parent / "esquema_geo.sql").read_text(encoding="utf-8"))
        pd.DataFrame(unidades[COLUMNAS]).to_sql("unidad", con, if_exists="append", index=False)
        con.commit()
    finally:
        con.close()


def exportar_niveles(unidades: gpd.GeoDataFrame, dir_salida: Path) -> dict[int, Path]:
    dir_salida = Path(dir_salida)
    dir_salida.mkdir(parents=True, exist_ok=True)
    rutas = {}
    gpkg = dir_salida.parent / "unidades.gpkg"  # lecturas filtradas rápidas; una capa por nivel
    gpkg.unlink(missing_ok=True)
    for nivel in (0, 1, 2):
        ruta = dir_salida / f"adm{nivel}.geojson"
        # las zonas en disputa (nivel 9) van dentro de adm0 para que el globo no tenga huecos
        niveles = (0, 9) if nivel == 0 else (nivel,)
        sub = unidades[unidades.nivel.isin(niveles)][["id", "nivel", "iso3", "padre_id", "nombre", "geometry"]]
        sub.to_file(ruta, driver="GeoJSON")
        sub.to_file(gpkg, driver="GPKG", layer=f"adm{nivel}")
        rutas[nivel] = ruta
    return rutas


def escribir_metadatos(ruta_sqlite: Path, datos: dict) -> None:
    con = sqlite3.connect(ruta_sqlite)
    try:
        con.executemany("INSERT OR REPLACE INTO metadatos VALUES (?,?)",
                        [(k, v if isinstance(v, str) else json.dumps(v, ensure_ascii=False)) for k, v in datos.items()])
        con.commit()
    finally:
        con.close()


def commit_actual() -> str | None:
    try:
        return subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True, check=True,
                              cwd=Path(__file__).parent).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return None


if __name__ == "__main__":
    gpkg = asegurar_gpkg(CRUDOS / "gadm_410-levels.zip", CRUDOS / "gadm_extraido/gadm_410-levels.gpkg")
    u = construir_unidades(gpkg, CRUDOS / "ne_10m_admin_1_states_provinces.zip",
                           CRUDOS / "gbopen_meta_adm2.json", CRUDOS / "gbopen")
    GEO_SQLITE.unlink(missing_ok=True)
    escribir_geo_sqlite(u, GEO_SQLITE)
    exportar_niveles(u, PROCESADOS / "limites_crudos")
    a = u.attrs
    usados = {"gadm41_levels", "ne_admin1_10m", "gbopen_meta_adm2", *(f"gbopen_{i}_adm2" for i in a["rellenados"])}
    escribir_metadatos(GEO_SQLITE, {
        "unidades_gadm_version": "4.1", "unidades_commit": commit_actual(),
        "unidades_fecha": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "unidades_sha256_insumos": {r.id: r.sha256 for r in cargar_manifiesto(MANIFIESTO) if r.id in usados},
        "unidades_conteos": {str(k): v for k, v in u.groupby("nivel").size().to_dict().items()}})
    print("conteo por nivel:", u.groupby("nivel").size().to_dict())
    print(f"coincidencia NE ADM1: {a['ne_coinciden']}/{a['ne_total']} = {a['ne_coinciden'] / a['ne_total']:.1%}")
    print("cruce_ambiguo:", int(u.cruce_ambiguo.sum()))
    print("rellenados con gbOpen:", a["rellenados"])
    print("geometrías reparadas:", a["reparadas"])
    print("zonas en disputa (nivel 9):", a["disputadas"])
    print("filas GADM con GID_0 'NA' descartadas:", a["descartadas"])
    print("filas hijas de zonas en disputa descartadas:", a["descartadas_disputa"])
