# asistido por SI: Claude Code (Anthropic), escritura y revisión de código; base del prototipo migrada en el hackatón
import argparse
import os
import pickle
import sqlite3
import time
from datetime import datetime, timezone
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import geopandas as gpd
import pandas as pd
import shapely
import pyogrio

from simulacion.config import CRUDOS, GEO_SQLITE
from simulacion.geo.descargas import MANIFIESTO, cargar_manifiesto
from simulacion.geo.unidades import _gid, _reparar, escribir_metadatos
from simulacion.geo.zonal import (_CORTES, extremos, fracciones_clase, media_ponderada,
                                  medias_ponderadas, ponderar_profundidad)

# La ruta raster corre en WSL: rasterio y exactextract no cargan en Windows (Control de aplicaciones)
# GADM_GPKG permite apuntar a una copia en el disco de WSL (leer por /mnt/c es unas 10 veces mas lento)
GPKG = Path(os.environ.get("GADM_GPKG", CRUDOS / "gadm_extraido/gadm_410-levels.gpkg"))
PROPIEDADES = {"soc": (10, "g/kg"), "phh2o": (10, "pH"), "clay": (10, "%"), "sand": (10, "%"),
               "silt": (10, "%"), "bdod": (100, "kg/dm3"), "cec": (10, "cmol(c)/kg"),
               "nitrogen": (100, "g/kg")}
PROFUNDIDADES = ("0-5cm", "5-15cm", "15-30cm")
RUTA_SOIL = CRUDOS / "soilgrids/{prop}_{prof}_mean_1000.tif"
# GMTED con el mar (0) declarado como NoData; lo crea gmted_tierra.py
RUTA_ELEV = CRUDOS / "gmted_extraido/mn30_tierra.tif"
RUTA_SQL_ESQUEMA = Path(__file__).parent / "esquema_geo.sql"

FUENTES = [
    ("soilgrids2", "Poggio et al. 2021, SoilGrids 2.0 agregado (ISRIC), media a 1000 m",
     "https://files.isric.org/soilgrids/latest/data_aggregated/", "CC BY 4.0", "datos/fichas/soilgrids2.md"),
    ("gmted2010", "Danielson y Gesch 2011, GMTED2010 mn30 (USGS), DOI 10.5066/F7J38R2N",
     "https://edcintl.cr.usgs.gov/downloads/sciweb1/shared/topo/downloads/GMTED/Grid_ZipFiles/mn30_grd.zip",
     "Dominio publico (USGS)", "datos/fichas/elevacion.md"),
]


# Rangos físicos (valido_min, valido_max): pH, textura, bdod y elevación son los de las pruebas datos_reales.
# SUPUESTO (cota física amplia, no del producto): soc 0-1000 g/kg (turba pura ~500), cec 0-500 cmol(c)/kg,
# nitrogen 0-50 g/kg (orgánicos ~20).
RANGOS = {"soc": (0, 1000), "phh2o": (3, 11), "clay": (0, 100), "sand": (0, 100), "silt": (0, 100),
          "bdod": (0.1, 2.0), "cec": (0, 500), "nitrogen": (0, 50), "elev": (-500, 9000)}


def _variable(id_, nombre, unidad, prod, version, doi, res, crs, fuente, etiqueta):
    vmin, vmax = RANGOS[id_.split("_")[0]]
    return (id_, nombre, unidad, None, None, None, vmin, vmax, prod, version, doi, res, crs,
            None, None, "real_contexto", etiqueta, fuente)


COMPONENTES = ("suelo", "relieve")
PRIMEROS = ["RUS", "CAN", "USA", "BRA", "CHN", "AUS"]  # los más pesados arrancan primero
TAM_LOTE = 1000


def indice_tareas(gpkg: Path, ids_validos: set, iso3: str | None = None, tam: int = TAM_LOTE):
    # una lectura sin geometría por capa: FID -> id (mismos _gid que unidades.py). Cada tarea es un
    # trozo de FID de un país, así los workers leen solo sus geometrías (por fids, sin escanear la capa)
    tareas = []
    for nivel in (0, 1, 2):
        col = f"GID_{nivel}"
        cols = list(dict.fromkeys(["GID_0", col]))
        t = pyogrio.read_dataframe(gpkg, layer=f"ADM_{nivel}", columns=cols, read_geometry=False, fid_as_index=True)
        t["id"] = [_gid(a, i, nivel) for a, i in zip(t[col], t["GID_0"])]
        t = t[t["id"].isin(ids_validos)]
        if iso3:
            t = t[t["GID_0"] == iso3]
        for iso, g in t.groupby("GID_0"):
            for k in range(0, len(g), tam):
                sub = g.iloc[k:k + tam]
                tareas.append((f"ADM_{nivel}", iso, [int(f) for f in sub.index], list(sub["id"])))
    return tareas


def ordenar_tareas(tareas: list) -> list:
    pri = {i: n for n, i in enumerate(PRIMEROS)}
    return sorted(tareas, key=lambda t: (pri.get(t[1], 99), -len(t[2])))


def geometrias_tarea(gpkg: Path, tarea) -> gpd.GeoDataFrame:
    capa, _, fids, ids = tarea
    g = pyogrio.read_dataframe(gpkg, layer=capa, columns=[], fids=fids, fid_as_index=True)
    _reparar(g)
    g["id"] = ids
    return g[["id", "geometry"]]


def lotes_gbopen(dir_gb: Path, ids_validos: set, isos: set):
    for iso in sorted(isos):
        ruta = dir_gb / f"gbopen_{iso}_adm2.geojson"
        g = pyogrio.read_dataframe(ruta, columns=["shapeID"]).to_crs("EPSG:4326")
        _reparar(g)
        g["id"] = ["gb:" + s for s in g["shapeID"]]
        g = g[g["id"].isin(ids_validos)]
        if len(g):
            yield g[["id", "geometry"]]


def _soilgrids_lote(u: gpd.GeoDataFrame) -> list[tuple]:
    # los rasters comparten grilla: una sola llamada por lote y una sola reproyección de las unidades
    rutas = {(p, f): Path(str(RUTA_SOIL).format(prop=p, prof=f)) for p in PROPIEDADES for f in PROFUNDIDADES}
    rutas = {k: r for k, r in rutas.items() if r.exists()}
    claves = list(rutas)
    res = medias_ponderadas([rutas[k] for k in claves], u,
                            [PROPIEDADES[p][0] for p, _ in claves]) if claves else {}
    filas = []
    for prop in PROPIEDADES:
        try:
            a, b, c = (res[rutas[(prop, f)]].set_index("id") for f in PROFUNDIDADES)
        except KeyError:
            continue
        for i in a.index:
            vs = [a.valor[i], b.valor[i], c.valor[i]]
            ok = all(v is not None for v in vs)
            v = float(ponderar_profundidad(*[float(x) for x in vs])) if ok else None
            fr = float(min(a.fraccion_valida[i], b.fraccion_valida[i], c.fraccion_valida[i]))
            filas.append((i, f"{prop}_0_30", None, None, None, v, fr))
    return filas


def _relieve_lote(u: gpd.GeoDataFrame) -> list[tuple]:
    m = media_ponderada(RUTA_ELEV, u, 1.0).set_index("id")
    e = extremos(RUTA_ELEV, u).set_index("id")
    filas = []
    for i in m.index:
        fr = float(m.fraccion_valida[i])
        filas += [(i, "elev_media", None, None, None, m.valor[i], fr),
                  (i, "elev_min", None, None, None, e.minimo[i] if fr > 0 else None, fr),
                  (i, "elev_max", None, None, None, e.maximo[i] if fr > 0 else None, fr)]
    return filas


def _variables() -> list[tuple]:
    vs = []
    for prop, (_, um) in PROPIEDADES.items():
        vs.append(_variable(f"{prop}_0_30", f"{prop} 0-30 cm", um, "SoilGrids agregado, media", "2.0",
                            "10.5194/soil-7-217-2021", "1000 m", "ESRI:54052 (Homolosine)", "soilgrids2",
                            "real_contexto; media ponderada por profundidad 5/10/15 cm, la columna media"))
    for id_, n in (("elev_media", "Elevacion media"), ("elev_min", "Elevacion minima"),
                   ("elev_max", "Elevacion maxima")):
        vs.append(_variable(id_, n, "m", "GMTED2010 mn30", "2010", "10.5066/F7J38R2N", "30 segundos de arco",
                            "EPSG:4326", "gmted2010", "real_contexto"))
    return vs


def calcular(u: gpd.GeoDataFrame, comps=COMPONENTES, solo_cruzan: bool = False) -> dict:
    # solo_cruzan: solo las unidades que cortan una interrupción de la Homolosine (recálculo de suelo)
    if solo_cruzan:
        u = u[shapely.intersects(u.geometry.values, _CORTES)]
    est = (_soilgrids_lote(u) if "suelo" in comps and len(u) else [])
    est += (_relieve_lote(u) if "relieve" in comps and len(u) else [])
    return {"estatico": est, "n": len(u)}


def _trabajo(args):
    # corre en un proceso hijo: lee, calcula y deja el resultado en un pickle propio
    k, tarea, partes, comps, solo_cruzan = args
    salida = Path(partes) / f"{k}.pkl"
    if salida.exists():
        return k, 0
    u = geometrias_tarea(GPKG, tarea) if tarea[0] != "gb" else tarea[2]
    r = calcular(u, comps, solo_cruzan)
    tmp = salida.with_suffix(".tmp")
    tmp.write_bytes(pickle.dumps(r))
    tmp.replace(salida)
    return k, r["n"]


def _tareas_gb(un, validos):
    tareas = []
    for iso in sorted(set(un[un.id.str.startswith("gb:")].iso3)):
        for u in lotes_gbopen(CRUDOS / "gbopen", validos, {iso}):
            for k in range(0, len(u), TAM_LOTE):
                tareas.append(("gb", iso, u.iloc[k:k + TAM_LOTE], []))
    return tareas


def unir_partes(ruta_sqlite: Path, partes: Path, comps=COMPONENTES) -> dict:
    # une todo en una transacción: reemplaza estatico (relieve y suelo),
    # variable y fuente
    est = []
    for f in sorted(Path(partes).glob("*.pkl")):
        r = pickle.loads(f.read_bytes())
        est += r["estatico"]
    con = sqlite3.connect(ruta_sqlite)
    try:
        con.executescript(RUTA_SQL_ESQUEMA.read_text(encoding="utf-8"))
        con.execute("BEGIN")
        # se borran solo las filas de las unidades recalculadas y de los componentes pedidos
        con.execute("CREATE TEMP TABLE recalc(id TEXT PRIMARY KEY)")
        con.executemany("INSERT OR IGNORE INTO recalc VALUES (?)", {(f[0],) for f in est})
        for comp, patron in (("suelo", "*_0_30"), ("relieve", "elev_*")):
            if comp in comps:
                con.execute("DELETE FROM estatico WHERE variable_id GLOB ? AND unidad_id IN (SELECT id FROM recalc)", (patron,))
        con.executemany("INSERT OR REPLACE INTO estatico VALUES (?,?,?,?,?,?,?)", est)
        con.executemany("INSERT OR REPLACE INTO variable VALUES (" + ",".join("?" * 18) + ")", _variables())
        con.executemany("INSERT OR REPLACE INTO fuente VALUES (?,?,?,?,?)", FUENTES)
        con.commit()
    finally:
        con.close()
    return {"estatico": len(est), "clase_fraccion": len(kop)}


def limpiar_partes(partes: Path) -> int:
    # partes viejas de otra corrida (otra geo.sqlite u otros ids) contaminarían la unión
    n = 0
    for f in Path(partes).glob("*.pkl"):
        f.unlink()
        n += 1
    for f in Path(partes).glob("*.tmp"):
        f.unlink()
    return n


def construir_estaticos(ruta_sqlite: Path, iso3: str | None = None, workers: int = 1,
                        partes: Path | None = None, comps=COMPONENTES, solo_cruzan: bool = False,
                        reanudar: bool = False) -> dict:
    # lee unidad de la sqlite, reparte tareas por trozos de países entre procesos y une al final.
    # iso3 limita a un país (muestras)
    partes = Path(partes or Path.home() / "tmp/partes_estaticos")
    partes.mkdir(parents=True, exist_ok=True)
    if not reanudar:  # solo --reanudar explícito reutiliza las partes ya calculadas
        limpiar_partes(partes)
    con = sqlite3.connect(ruta_sqlite)
    q = "SELECT id, iso3 FROM unidad" + (" WHERE iso3 = ?" if iso3 else "")
    un = pd.read_sql(q, con, params=[iso3] if iso3 else None)
    con.close()
    validos = set(un.id)
    tareas = ordenar_tareas(indice_tareas(GPKG, validos, iso3))
    gb = _tareas_gb(un, validos)
    todas = tareas + gb
    total = len(validos)
    print(f"{len(todas)} tareas, {total} unidades, {workers} procesos", flush=True)
    t0, hechas = time.time(), 0
    trabajos = [(k, t, partes, comps, solo_cruzan) for k, t in enumerate(todas)]
    with ProcessPoolExecutor(workers) as ex:
        for k, n in ex.map(_trabajo, trabajos):
            hechas += n
            print(f"tarea {k + 1}/{len(todas)}: {hechas}/{total} unidades, {time.time() - t0:.0f} s", flush=True)
    r = unir_partes(ruta_sqlite, partes, comps)
    insumos = {x.id: x.sha256 for x in cargar_manifiesto(MANIFIESTO)
               if x.id.startswith("soilgrids_") or x.id in ("gmted2010_mn30",)}
    escribir_metadatos(ruta_sqlite, {"estaticos_fecha": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                                     "estaticos_workers": workers, "estaticos_componentes": list(comps),
                                     "estaticos_sha256_insumos": insumos})
    return r


if __name__ == "__main__":
    # uso: python -m simulacion.geo.estaticos [--sqlite R] [--iso3 X] [--workers N] [--partes D]
    ap = argparse.ArgumentParser()
    ap.add_argument("--sqlite", type=Path, default=GEO_SQLITE)
    ap.add_argument("--iso3")
    ap.add_argument("--workers", type=int, default=1)
    ap.add_argument("--partes", type=Path)
    ap.add_argument("--componentes", default="suelo,relieve")
    ap.add_argument("--solo-cruzan", action="store_true")
    ap.add_argument("--reanudar", action="store_true", help="reutiliza las partes ya calculadas (por defecto se vacían)")
    a = ap.parse_args()
    print(construir_estaticos(a.sqlite, a.iso3, a.workers, a.partes,
                              tuple(a.componentes.split(",")), a.solo_cruzan, a.reanudar))
