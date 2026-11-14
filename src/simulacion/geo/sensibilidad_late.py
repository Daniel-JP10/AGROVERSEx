# asistido por SI: Claude Code (Anthropic), sensibilidad 70/80/90 de la regla de días válidos de IMERG Late en Colombia (D-011)
import calendar
import glob
import json
import os
import re
import sys
import warnings
from collections import defaultdict
from pathlib import Path

import numpy as np

from simulacion.geo.imerg_late import mensual_late, unidades_validas

UMBRALES = (0.7, 0.8, 0.9)
CAJA = (-81.8, -4.3, -66.8, 13.4)  # lon_min, lat_min, lon_max, lat_max de Colombia (CGAZ ADM2)
PASO = 0.1


def indices_caja():
    # shortcut: se asume la grilla IMERG de 0,1 grados con celdas centradas en -179,95 y -89,95; el resultado se contrasta con lluvia conocida
    i0, i1 = int((CAJA[0] + 180) / PASO), int(np.ceil((CAJA[2] + 180) / PASO))
    j0, j1 = int((CAJA[1] + 90) / PASO), int(np.ceil((CAJA[3] + 90) / PASO))
    return i0, i1, j0, j1


def leer_dia(ruta, i0, i1, j0, j1):
    import rasterio
    with rasterio.open(ruta) as d:
        sub = next(s for s in d.subdatasets if s.endswith(":precipitation"))
    with rasterio.open(sub) as v:
        a = v.read(1)  # forma (lon, lat) tal como la entrega el archivo
    return a[i0:i1, j0:j1]


def celdas_por_unidad(gpkg, i0, i1, j0, j1):
    import geopandas as gpd
    from shapely.geometry import box
    g = gpd.read_file(gpkg, where="shapeGroup='COL'")
    ni, nj = i1 - i0, j1 - j0
    cajas, idx = [], []
    for i in range(ni):
        for j in range(nj):
            x, y = -180 + (i0 + i) * PASO, -90 + (j0 + j) * PASO
            cajas.append(box(x, y, x + PASO, y + PASO))
            idx.append(i * nj + j)
    celdas = gpd.GeoDataFrame({"k": idx}, geometry=cajas, crs=g.crs)
    r = gpd.sjoin(celdas, g[["geometry"]].reset_index(drop=True), predicate="intersects")
    por = defaultdict(list)
    for k, u in zip(r["k"], r["index_right"]):
        por[u].append(k)
    return [np.array(por[u], dtype=int) if u in por else np.array([], dtype=int) for u in range(len(g))], len(g)


def principal(carpeta, gpkg, salida):
    warnings.simplefilter("ignore")
    i0, i1, j0, j1 = indices_caja()
    archivos = sorted(glob.glob(os.path.join(carpeta, "*.nc4")))
    meses = defaultdict(list)
    for f in archivos:
        m = re.search(r"3IMERG\.(\d{4})(\d{2})(\d{2})", f)
        meses[(int(m[1]), int(m[2]))].append(f)
    por_unidad, n_unid = celdas_por_unidad(gpkg, i0, i1, j0, j1)
    res = []
    for (a, m), fs in sorted(meses.items()):
        dm = calendar.monthrange(a, m)[1]
        cubo = np.stack([leer_dia(f, i0, i1, j0, j1) for f in fs])
        fila = {"mes": f"{a}-{m:02d}", "dias": len(fs), "dias_del_mes": dm, "completo": len(fs) == dm}
        for u in UMBRALES:
            media, _ = mensual_late(cubo, dm, u)
            fila[f"celdas_validas_{int(u*100)}"] = int(np.isfinite(media).sum())
            fila[f"unidades_validas_{int(u*100)}"] = int(unidades_validas(media, por_unidad).sum())
        fila["celdas_caja"] = int(cubo.shape[1] * cubo.shape[2])
        res.append(fila)
    Path(salida).write_text(json.dumps({"unidades": n_unid, "meses": res}, indent=1), encoding="utf-8")
    print(json.dumps(res[-3:], indent=1))


if __name__ == "__main__":
    # uso (WSL, venv geo): python -m simulacion.geo.sensibilidad_late <carpeta imerg_late> <gpkg ADM2> <salida.json>
    principal(*sys.argv[1:4])
