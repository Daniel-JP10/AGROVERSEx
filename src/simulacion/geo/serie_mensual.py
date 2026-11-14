# asistido por SI: Claude Code (Anthropic), corrida de series mensuales por unidad con el motor zonal (T-D2)
"""Corrida de un país: python -m simulacion.geo.serie_mensual COL [area|cultivo|ambas]

Entradas en WSL: AGRO_COPIA (copia de los crudos y de unidades.gpkg). Salida: CSV gzip por variable y
ponderación (provisional: el entorno no trae pyarrow; el esquema es el de contratos/serie_mensual.md)."""
import calendar
import json
import os
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

from simulacion.geo import lectura_nasa as L
from simulacion.geo import zonal_mensual as zm
from simulacion.geo.imerg_late import mensual_late

UMBRAL_FRAC_VALIDA = 0.5  # SUPUESTO: bajo la mitad del área (o del cultivo) con dato, el valor sale NaN con motivo
UMBRAL_DIAS_LATE = 0.8    # D-011

# variable del contrato -> (producto de lectura, producto, versión, estado, unidad)
VARIABLES = {
    "precipitacion_final": ("imerg_final", "GPM IMERG Final Run, mensual 0,1 grados (GPM_3IMERGM)", "07B", "final", "mm/hr"),
    "precipitacion_late": ("imerg_late", "GPM IMERG Late Run, diario agregado a mes en UTC (GPM_3IMERGDL)", "07B", "provisional", "mm/day"),
    "t2m": ("t2m", "MERRA-2 reanálisis, M2TMNXSLV (T2M)", "5.12.4", "final", "K"),
    "humedad_radicular": ("humedad_radicular", "GLDAS Noah 0,25 mensual, MODELO de superficie terrestre (GLDAS_NOAH025_M, RootMoist_inst)",
                          "2.1", "final", "kg m-2"),
    "ndvi": ("ndvi", "MODIS Terra MOD13C2 NDVI mensual 0,05 grados", "061", "final", "1"),
}
NOMBRE_VARIABLE = {"precipitacion_final": "precipitacion", "precipitacion_late": "precipitacion"}


def cargar_unidades(gpkg: str, iso3: str):
    import pyogrio
    cols = ["unidad_id", "nivel", "nombre"]
    partes = [pyogrio.read_dataframe(gpkg, layer=f"adm{n}", where=f"iso3='{iso3}'", columns=cols) for n in (0, 1, 2)]
    # un país sin nivel 2 repite el nivel 1 en la capa ADM2 con otro unidad_id; se conserva (nivel_real lo dice en unidades.gpkg)
    return pd.concat(partes, ignore_index=True)


CLASES_CULTIVO = {1, 2, 3}  # GFSAD1KCM: riego mayor, riego menor y secano; 4 y 5 son fragmentos menores (SUPUESTO, ver ficha)


def cultivo_desde_gfsad(tif: str, bbox, clases=CLASES_CULTIVO) -> dict:
    """{firma de grilla: fracción de cultivo plana} para las grillas de T-D3, leyendo solo la ventana del país."""
    import rasterio
    from rasterio.windows import from_bounds
    out = {}
    with rasterio.open(tif) as d:
        w = from_bounds(*bbox, transform=d.transform).round_offsets().round_lengths()
        a = d.read(1, window=w)
        t = d.window_transform(w)
    fino = zm.Grilla(t.c, t.f, t.a, -t.e, a.shape[0], a.shape[1])
    for g in L.GRILLAS.values():
        out[g.firma()] = zm.fraccion_cultivo(g, a, fino, set(clases), bbox)
    return out


def _filas(r, ids, niveles, variable, mes, ponderacion, meta):
    prod, version, estado, unidad = meta
    return pd.DataFrame({
        "unidad_id": ids, "variable": NOMBRE_VARIABLE.get(variable, variable), "mes": mes,
        "valor": r["valor"], "p10": r["p10"], "p90": r["p90"], "tipo_rango": "espacial",
        "frac_valida": r["frac_valida"], "ponderacion": ponderacion, "producto": prod, "version": version,
        "estado": estado, "unidad": unidad, "motivo": r["motivo"]})


def campos_mensuales(base: Path, clave: str):
    """Generador (mes, campo plano norte arriba) de una variable. Late se agrega con D-011 y omite el mes en curso."""
    prod = VARIABLES[clave][0]
    if prod != "imerg_late":
        regla = None
        for mes, f in L.archivos(base, prod).items():
            a, regla = L.leer_campo(f, prod, int(mes[5:]), regla)
            yield mes, a.ravel()
        return
    import rasterio
    regla = None
    for mes, fs in L.dias_late(base).items():
        n_mes = calendar.monthrange(int(mes[:4]), int(mes[5:]))[1]
        if len(fs) < n_mes:  # mes en curso: D-011 lo deja NaN en todas las celdas; no se emite
            continue
        cubo = np.stack([rasterio.open(f"netcdf:{f}:precipitation").read(1) for f in fs])
        media, _ = mensual_late(cubo, n_mes, UMBRAL_DIAS_LATE)
        a, regla = L.orientar(media.astype("float64"), "imerg_late", int(mes[5:]), regla)
        yield mes, a.ravel()


def correr(base: Path, gpkg: str, iso3: str, salida: Path, modos=("area",), variables=None, cultivo=None):
    u = cargar_unidades(gpkg, iso3)
    import pyogrio
    geoms = np.concatenate([pyogrio.read_dataframe(gpkg, layer=f"adm{n}", where=f"iso3='{iso3}'",
                            columns=["unidad_id"]).geometry.values for n in (0, 1, 2)])
    ids = u["unidad_id"].tolist()
    informe, salida = {}, Path(salida)
    salida.mkdir(parents=True, exist_ok=True)
    pesos = {}
    for clave in variables or VARIABLES:
        prod, nombre, version, estado, unidad = VARIABLES[clave]
        g = L.GRILLAS[L.PRODUCTOS[prod]["grilla"]]
        t0 = time.time()
        if g.firma() not in pesos:
            pesos[g.firma()] = zm.pesos_con_cache(g, ids, geoms, salida / "cache_pesos")
            informe[f"pesos_{g.firma()}"] = dict(grilla=L.PRODUCTOS[prod]["grilla"], segundos=round(time.time() - t0, 2),
                                                 nnz=int(len(pesos[g.firma()].c)))
        p = pesos[g.firma()]
        tm, meses, trozos, t_agr = time.time(), 0, {m: [] for m in modos}, 0.0
        for mes, x in campos_mensuales(base, clave):
            for modo in modos:
                c = None if modo == "area" else cultivo[g.firma()]
                ta = time.time()
                r = zm.agregar(p, g, x, c, UMBRAL_FRAC_VALIDA)
                t_agr += time.time() - ta
                trozos[modo].append(_filas(r, ids, u["nivel"], clave, mes, modo, (nombre, version, estado, unidad)))
            meses += 1
        informe[clave] = dict(meses=meses, segundos_total=round(time.time() - tm, 1),
                              segundos_por_mes=round((time.time() - tm) / max(meses, 1), 3),
                              segundos_agregar_por_mes_y_modo=round(t_agr / max(meses * len(modos), 1), 4))
        for modo, lista in trozos.items():
            df = pd.concat(lista, ignore_index=True)
            df.insert(1, "nivel", np.tile(u["nivel"].to_numpy(), meses))
            df.to_csv(salida / f"serie_mensual_{clave}_{modo}.csv.gz", index=False, na_rep="", float_format="%.6g")
            informe[clave][f"filas_{modo}"] = int(len(df))
        print(clave, informe[clave], flush=True)
    (salida / f"informe_{iso3}.json").write_text(json.dumps(informe, indent=1), encoding="utf8")
    return informe


if __name__ == "__main__":
    base = Path(os.environ["AGRO_COPIA"])
    iso = sys.argv[1]
    correr(base / "crudos", str(base / "proc" / "unidades.gpkg"), iso, base / "series" / iso, ("area",))
