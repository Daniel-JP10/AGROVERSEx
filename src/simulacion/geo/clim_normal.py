# asistido por SI: Claude Code (Anthropic), escritura y revisión de código; base del prototipo migrada en el hackatón
"""Normales WorldClim 2.1 (1970-2000, 2,5 min) por unidad -> clim_normal.sqlite.

Extraer los zips corre en cualquier lado; la zonal solo en WSL (rasterio y exactextract, D-011).
Uso WSL: PYTHONPATH=src python -m simulacion.geo.clim_normal zonal --gpkg ~/tmp/unidades.gpkg --tifs ~/tmp/wc --salida ~/tmp/clim_normal.sqlite
"""
import argparse
import sqlite3
import time
import zipfile
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import pandas as pd

VARS = ("tavg", "tmin", "tmax", "prec", "srad")
TAM = {"adm0": 10, "adm1": 100, "adm2": 400}  # unidades por tarea; los polígonos de país son enormes

ESQUEMA = """CREATE TABLE clim_normal(unidad_id TEXT NOT NULL, mes INTEGER NOT NULL, tavg REAL, tmin REAL, tmax REAL,
prec REAL, srad REAL, fraccion_valida REAL, PRIMARY KEY(unidad_id, mes))"""


def extraer(dir_zips: Path, destino: Path) -> int:
    destino.mkdir(parents=True, exist_ok=True)
    n = 0
    for v in VARS:
        with zipfile.ZipFile(Path(dir_zips) / f"wc2.1_2.5m_{v}.zip") as z:
            for m in z.namelist():
                if m.endswith(".tif") and not (destino / Path(m).name).exists():
                    (destino / Path(m).name).write_bytes(z.read(m))
                    n += 1
    return n


def escribir(ruta: Path, filas: pd.DataFrame) -> None:
    ruta = Path(ruta)
    ruta.unlink(missing_ok=True)
    con = sqlite3.connect(ruta)
    try:
        con.execute(ESQUEMA)
        cols = ["unidad_id", "mes", *VARS, "fraccion_valida"]
        con.executemany("INSERT INTO clim_normal VALUES (?,?,?,?,?,?,?,?)",
                        filas[cols].astype(object).where(filas[cols].notna(), None).itertuples(index=False))
        con.commit()
    finally:
        con.close()


def _tarea(args):
    from simulacion.geo.zonal import medias_ponderadas  # solo WSL
    import pyogrio
    gpkg, capa, ini, tifs = args
    t0 = time.time()
    u =pyogrio.read_dataframe(gpkg, layer=capa, columns=["id"], skip_features=ini, max_features=TAM[capa])
    cols = []
    for v in VARS:
        rutas = [Path(tifs) / f"wc2.1_2.5m_{v}_{m:02d}.tif" for m in range(1, 13)]
        res = medias_ponderadas(rutas, u, [1.0] * 12)  # una llamada por variable
        d = pd.concat([res[r].assign(mes=m) for m, r in enumerate(rutas, 1)]).set_index(["id", "mes"])
        cols.append(pd.DataFrame({v: pd.to_numeric(d["valor"], errors="coerce"), f"fr_{v}": d["fraccion_valida"]}))
    out = pd.concat(cols, axis=1)
    out["fraccion_valida"] = out[[f"fr_{v}" for v in VARS]].min(axis=1)
    out = out[[*VARS, "fraccion_valida"]].reset_index()
    print(f"  {capa} desde {ini}: {len(u)} unidades en {time.time() - t0:.0f} s", flush=True)
    return out.rename(columns={"id": "unidad_id"})


def zonal(gpkg: Path, tifs: Path, salida: Path, workers: int = 4, limite: int | None = None,
          capas=("adm2", "adm1", "adm0")) -> pd.DataFrame:
    import pyogrio
    tareas = []
    for capa in capas:
        n = pyogrio.read_info(gpkg, layer=capa)["features"]
        n = min(n, limite) if limite else n
        tareas += [(str(gpkg), capa, i, str(tifs)) for i in range(0, n, TAM[capa])]
    t0, partes = time.time(), []
    with ProcessPoolExecutor(workers) as ex:
        for k, p in enumerate(ex.map(_tarea, tareas), 1):
            partes.append(p)
            print(f"tarea {k}/{len(tareas)}, {time.time() - t0:.0f} s", flush=True)
    todo = pd.concat(partes, ignore_index=True)
    escribir(salida, todo)
    return todo


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("modo", choices=["extraer", "zonal"])
    ap.add_argument("--zips", type=Path)
    ap.add_argument("--gpkg", type=Path)
    ap.add_argument("--tifs", type=Path)
    ap.add_argument("--salida", type=Path)
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--limite", type=int)
    ap.add_argument("--capas", default="adm2,adm1,adm0")
    a = ap.parse_args()
    if a.modo == "extraer":
        print(extraer(a.zips, a.tifs), "tifs")
    else:
        r = zonal(a.gpkg, a.tifs, a.salida, a.workers, a.limite, tuple(a.capas.split(",")))
        print(len(r), "filas;", int(r.tavg.isna().groupby(r.unidad_id).all().sum()), "unidades sin normales")
