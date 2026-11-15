# asistido por SI: Claude Code (Anthropic), migración de límites GADM a CGAZ (T-D1): lectura, ids, jerarquía y GPKG
import json
import sqlite3
import subprocess
import time
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
import pyogrio
import shapely
from pyproj import Geod
from shapely.geometry.polygon import orient

from simulacion.config import CRS_AREA, CRS_SALIDA, CRUDOS, PROCESADOS
from simulacion.geo.descargas import sha256_archivo
from simulacion.geo.normalizar import normalizar_nombre

# CGAZ de geoBoundaries, fijado por commit del repositorio oficial wmgeolab/geoBoundaries
CGAZ_COMMIT = "4004e96433a2bdc54cac2b88d7d2e694c89cb818"
CGAZ_URL = ("https://media.githubusercontent.com/media/wmgeolab/geoBoundaries/"
            f"{CGAZ_COMMIT}/releaseData/CGAZ/geoBoundariesCGAZ_ADM{{n}}.gpkg")
# sha256 que el propio repositorio publica en el puntero Git LFS de cada archivo
CGAZ_SHA256 = {
    0: "6bdeb27072cf3759edfe9d31e037ebaf2481d9e0fa5ad18c1036346e42b4c41a",
    1: "d2f2f7854e887c99a23f2ad1c9e7627c05db15ecc4d9f94972c0d193d255a63d",
    2: "6bc948cdd84575b733573d7983cf2503e1c71d66d2434db04502ae5fba60eec1",
}
# tolerancia de area_proyectada / area_geodesica por unidad (0,5 %); medido: 99,996 % de las unidades dentro de 0,1 %
TOLERANCIA_AREA = 0.005
# separación máxima (grados) entre vértices al calcular áreas: sin ella los bordes largos difieren hasta 4,5 %
SEGMENTO_GRADOS = 0.1
# WGS 84 / NSIDC EASE-Grid 2.0 Global: cilíndrica de igual área sobre el elipsoide
CRS_AREA_UNIDADES = "EPSG:6933"
# ancho (grados, ~1 m) del polígono mínimo que reemplaza a un degenerado de área cero
DEGENERADO_GRADOS = 1e-5
INVALIDOS = {"", "na", "n.a.", "?"}
CODIGOS_DISPUTA = frozenset({*(str(i) for i in range(111, 130)), "ESH"})
COLUMNAS = ["unidad_id", "nivel", "nivel_real", "iso3", "padre_id", "nombre", "nombre_ascii", "area_km2",
            "es_disputa", "punto_lat", "punto_lon", "cruce_ambiguo", "bbox_oeste", "bbox_sur", "bbox_este",
            "bbox_norte", "fuente"]


def nombre_valido(s: str | None) -> bool:
    return isinstance(s, str) and s.strip().lower() not in INVALIDOS


def verificar_hash(ruta: Path, esperado: str) -> str:
    h = sha256_archivo(ruta)
    if h != esperado:
        raise ValueError(f"hash distinto en {ruta}: {h} != {esperado}")
    return h


def descargar_cgaz(destino: Path) -> dict[int, Path]:
    # descarga una sola vez a .parcial, verifica el hash del repositorio y renombra
    import requests
    destino = Path(destino)
    destino.mkdir(parents=True, exist_ok=True)
    rutas = {}
    for n, esperado in CGAZ_SHA256.items():
        ruta = destino / f"geoBoundariesCGAZ_ADM{n}.gpkg"
        if not ruta.exists():
            tmp = ruta.with_name(ruta.name + ".parcial")
            with requests.get(CGAZ_URL.format(n=n), stream=True, timeout=60) as r, open(tmp, "wb") as f:
                r.raise_for_status()
                for bloque in r.iter_content(1 << 20):
                    f.write(bloque)
            verificar_hash(tmp, esperado)
            tmp.replace(ruta)
        rutas[n] = ruta
    return rutas


def construir_ids(iso3, nivel, shape_id) -> pd.Series:
    # nivel 0: {iso3}-ADM0 (CGAZ ADM0 no trae shapeID); niveles 1 y 2: {iso3}-ADM{n}-{shapeID}
    iso3, nivel, sid = (pd.Series(x).reset_index(drop=True) for x in (iso3, nivel, shape_id))
    base = iso3.astype(str) + "-ADM" + nivel.astype(str)
    return base.where(nivel == 0, base + "-" + sid.astype(str))


def duplicados(t: pd.DataFrame) -> int:
    # un id repetido en cualquier nivel cuenta: el id es único en todo el conjunto
    return int(t["unidad_id"].duplicated().sum())


def leer_cgaz(ruta: Path, nivel: int) -> gpd.GeoDataFrame:
    g = pyogrio.read_dataframe(ruta)
    # el GPKG trae un SRS sin nombre con elipsoide WGS84: se declara EPSG:4326
    g = g.set_crs(CRS_SALIDA, allow_override=True)
    sid = g["shapeID"] if "shapeID" in g else pd.Series(None, index=g.index, dtype=object)
    return gpd.GeoDataFrame({"iso3": g["shapeGroup"], "nivel_real": g["shapeType"], "shape_id": sid,
                             "nombre": g["shapeName"], "nivel": nivel}, geometry=g.geometry, crs=CRS_SALIDA)


def asignar_padre_espacial(hijos: gpd.GeoDataFrame, padres: gpd.GeoDataFrame) -> pd.DataFrame:
    puntos = gpd.GeoDataFrame(geometry=hijos.geometry.representative_point(), crs=hijos.crs)
    puntos["i"] = range(len(puntos))
    union = gpd.sjoin(puntos, padres[["unidad_id", "geometry"]], how="left", predicate="within")
    por_hijo = union.groupby("i")["unidad_id"].agg(lambda s: list(s.dropna()))
    padre = [p[0] if len(p) == 1 else None for p in por_hijo.reindex(range(len(puntos)))]
    return pd.DataFrame({"padre_id": padre,
                         "cruce_ambiguo": [0 if p is not None else 1 for p in padre]}, index=hijos.index)


def corregir_padres(hijos: gpd.GeoDataFrame, padres: gpd.GeoDataFrame):
    # sin padre o con padre de otro país: se pasa al padre más cercano del mismo país (en Mollweide)
    iso_padre = padres.set_index("unidad_id")["iso3"]
    sin = hijos["padre_id"].isna()
    distinto = ~sin & (hijos["padre_id"].map(iso_padre).to_numpy() != hijos["iso3"].to_numpy())
    mal = (sin | distinto).to_numpy()
    out = hijos.copy()
    for iso in hijos.loc[mal, "iso3"].unique():  # un bucle por país con casos, no por fila
        cand = padres[padres["iso3"] == iso]
        idx = hijos.index[mal & (hijos["iso3"] == iso).to_numpy()]
        if cand.empty:
            continue
        pts = gpd.GeoDataFrame(geometry=hijos.loc[idx].geometry.representative_point(),
                               crs=hijos.crs).to_crs(CRS_AREA)
        j = gpd.sjoin_nearest(pts, cand.to_crs(CRS_AREA)[["unidad_id", "geometry"]], how="left")
        out.loc[idx, "padre_id"] = j[~j.index.duplicated()]["unidad_id"]
    return out, {"distinto_pais": int(distinto.sum()), "sin_padre": int(sin.sum())}


def _geometria_derivada(gdf: gpd.GeoDataFrame):
    # punto interior en EPSG:4326 y área en EPSG:6933 (igual área)
    pts = gdf.geometry.representative_point()
    densa = gdf.geometry.segmentize(SEGMENTO_GRADOS)
    area = densa.to_crs(CRS_AREA_UNIDADES).area / 1e6
    return (pd.Series(pts.y.values, index=gdf.index), pd.Series(pts.x.values, index=gdf.index),
            pd.Series(area.values, index=gdf.index))


def area_geodesica_km2(geoms) -> np.ndarray:
    # control independiente del área proyectada: área sobre el elipsoide WGS84, por polígono orientado
    geod = Geod(ellps="WGS84")
    return np.array([sum(geod.geometry_area_perimeter(orient(p))[0] for p in shapely.get_parts(g))
                     for g in shapely.segmentize(np.asarray(geoms, dtype=object), SEGMENTO_GRADOS)]) / 1e6


def _solo_poligonos(geoms: np.ndarray) -> np.ndarray:
    # make_valid puede devolver colecciones con líneas: se conservan solo las partes poligonales.
    # Lo que queda sin polígono (degenerado de área cero) pasa a un polígono mínimo, para no perder la unidad.
    sin_linea = geoms.copy()
    col = np.flatnonzero(~np.isin(shapely.get_type_id(geoms), (3, 6)))
    if len(col) == 0:
        return sin_linea
    partes, idx = shapely.get_parts(geoms[col], return_index=True)
    partes, sub = shapely.get_parts(partes, return_index=True)  # MultiPolygon dentro de la colección
    idx = idx[sub]
    es_pol = shapely.get_type_id(partes) == 3
    for k, i in enumerate(col):
        pol = partes[(idx == k) & es_pol]
        sin_linea[i] = shapely.multipolygons(pol) if len(pol) else shapely.buffer(geoms[i], DEGENERADO_GRADOS)
    return sin_linea


def _reparar(gdf: gpd.GeoDataFrame) -> int:
    # vectorizado con shapely 2: solo se repara lo inválido y se dejan solo polígonos
    geoms = gdf.geometry.values.copy()
    malas = ~shapely.is_valid(geoms)
    if malas.any():
        geoms[malas] = _solo_poligonos(shapely.make_valid(geoms[malas]))
        gdf["geometry"] = geoms
    return int(malas.sum())


def _gid(gid, iso3, nivel):
    # heredado de GADM; estaticos.py lo usa hasta que T-D4 lo migre
    return gid if nombre_valido(gid) else f"{iso3}.sin_gid_{nivel}"


def codigos_huerfanos(t: pd.DataFrame) -> set[str]:
    # países de nivel 1 o 2 que no existen en el nivel 0 (el caso Kosovo XKO/XKX de la fase previa)
    con = sqlite3.connect(":memory:")
    try:
        t[["unidad_id", "nivel", "iso3"]].to_sql("unidad", con, index=False)
        filas = con.execute("SELECT DISTINCT iso3 FROM unidad WHERE nivel > 0 AND iso3 NOT IN "
                            "(SELECT iso3 FROM unidad WHERE nivel = 0)").fetchall()
    finally:
        con.close()
    return {f[0] for f in filas}


def paises_sin_nivel2(adm2: pd.DataFrame) -> list[str]:
    # países de la capa ADM2 sin ningún polígono que sea ADM2 de verdad (repiten el nivel 1 o el 0)
    return sorted(set(adm2["iso3"]) - set(adm2.loc[adm2["nivel_real"] == "ADM2", "iso3"]))


def construir_unidades(dir_cgaz: Path) -> gpd.GeoDataFrame:
    stats = {"reparadas": 0, "tiempos_s": {}}
    partes = []
    for nivel in (0, 1, 2):
        t0 = time.time()
        ruta = Path(dir_cgaz) / f"geoBoundariesCGAZ_ADM{nivel}.gpkg"
        g = leer_cgaz(ruta, nivel)
        stats["reparadas"] += _reparar(g)
        g["unidad_id"] = construir_ids(g.iso3, g.nivel, g.shape_id).to_numpy()
        sin_nombre = ~g["nombre"].map(nombre_valido)
        g.loc[sin_nombre, "nombre"] = "Sin nombre " + g.loc[sin_nombre, "shape_id"].astype(str)
        stats[f"sin_nombre_adm{nivel}"] = int(sin_nombre.sum())
        lat, lon, area = _geometria_derivada(g)
        b = g.geometry.bounds
        g = g.assign(nombre_ascii=[normalizar_nombre(n) for n in g["nombre"]], area_km2=area.values,
                     punto_lat=lat.values, punto_lon=lon.values, es_disputa=(g.nivel_real == "DISP").astype(int),
                     bbox_oeste=b.minx.values, bbox_sur=b.miny.values, bbox_este=b.maxx.values,
                     bbox_norte=b.maxy.values, padre_id=None, cruce_ambiguo=0,
                     fuente=f"{ruta.name} (geoBoundaries, commit {CGAZ_COMMIT[:7]})")
        if nivel > 0:
            padres = partes[nivel - 1]
            p = asignar_padre_espacial(g, padres)
            g["padre_id"], g["cruce_ambiguo"] = p.padre_id, p.cruce_ambiguo
            g, stats[f"padres_adm{nivel}"] = corregir_padres(g, padres)
        stats["tiempos_s"][f"adm{nivel}"] = round(time.time() - t0, 1)
        partes.append(g)
    out = pd.concat(partes, ignore_index=True)
    stats["paises_sin_nivel2"] = paises_sin_nivel2(partes[2])
    out = gpd.GeoDataFrame(out[COLUMNAS + ["geometry"]], geometry="geometry", crs=CRS_SALIDA)
    out.attrs.update(stats)
    return out


def escribir_gpkg(unidades: gpd.GeoDataFrame, ruta: Path) -> Path:
    # una sola vez, a .parcial y renombrando al final; capa adm{n} con índice espacial (rtree) y de unidad_id
    ruta = Path(ruta)
    ruta.parent.mkdir(parents=True, exist_ok=True)
    tmp = ruta.with_name(ruta.stem + ".parcial.gpkg")
    tmp.unlink(missing_ok=True)
    for n in (0, 1, 2):
        unidades[unidades["nivel"] == n].to_file(tmp, driver="GPKG", layer=f"adm{n}")
    con = sqlite3.connect(tmp)
    try:
        for n in (0, 1, 2):
            con.execute(f"CREATE INDEX idx_adm{n}_unidad_id ON adm{n}(unidad_id)")
        con.commit()
    finally:
        con.close()
    tmp.replace(ruta)
    return ruta


def exportar_niveles(unidades: gpd.GeoDataFrame, dir_salida: Path) -> dict[int, Path]:
    # GeoJSON de entrada para mapshaper y tippecanoe; solo los atributos que van a las teselas
    dir_salida = Path(dir_salida)
    dir_salida.mkdir(parents=True, exist_ok=True)
    if "es_disputa" not in unidades.columns:
        unidades = unidades.assign(es_disputa=unidades["iso3"].astype(str).isin(CODIGOS_DISPUTA).astype(int))
    rutas = {}
    for nivel in (0, 1, 2):
        ruta = dir_salida / f"adm{nivel}.geojson"
        sub = unidades[unidades["nivel"] == nivel][
            ["unidad_id", "nombre", "nivel", "iso3", "padre_id", "es_disputa", "geometry"]
        ]
        sub.to_file(ruta, driver="GeoJSON")
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
    descargar_cgaz(CRUDOS / "cgaz")
    for n, h in CGAZ_SHA256.items():
        verificar_hash(CRUDOS / f"cgaz/geoBoundariesCGAZ_ADM{n}.gpkg", h)
    u = construir_unidades(CRUDOS / "cgaz")
    escribir_gpkg(u, PROCESADOS / "unidades.gpkg")
    exportar_niveles(u, PROCESADOS / "limites_crudos")
    informe = {**u.attrs, "conteos": {str(k): int(v) for k, v in u.groupby("nivel").size().items()},
               "huerfanos": sorted(codigos_huerfanos(u)), "commit_codigo": commit_actual()}
    (PROCESADOS / "unidades_informe.json").write_text(json.dumps(informe, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(informe, ensure_ascii=False, indent=1))
