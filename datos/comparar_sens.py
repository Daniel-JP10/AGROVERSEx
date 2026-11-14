# asistido por SI: Claude Code, comparación de sensibilidades de Colombia para PI-D1 y NDVI (T-D2)
"""python datos/comparar_sens.py BASE_COL c15_DIR rel0_DIR salida.json   (BASE_COL = series 1-3, reliability 0 y 1)"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

from simulacion.geo.pi_d1_colombia import comparar

base, c15, rel0, salida = (Path(x) for x in sys.argv[1:5])
meses = [f"2019-{m:02d}" for m in range(1, 13)]


def dif_rel(a, b):
    # diferencia relativa |b - a| / |a| entre dos series de la misma variable, nivel 2, 2019, ambas con valor
    m = a.merge(b, on=["unidad_id", "mes"], suffixes=("_a", "_b"))
    m = m[(m.nivel_a == 2) & m.mes.isin(meses) & m.valor_a.notna() & m.valor_b.notna()]
    r = ((m.valor_b - m.valor_a).abs() / m.valor_a.abs())
    return dict(pares=int(len(m)), **{f">{u}%": round(float((r > u / 100).mean()), 4) for u in (2, 5, 10)},
                sin_valor_en_a_con_valor_en_b=int((a.mes.isin(meses) & (a.nivel == 2) & a.valor.isna()).sum()))


out = {"pi_d1_con_clases_1_a_5": {k: v["fraccion_unidades_con_dif_relativa_mayor_a"] | {"pares": v["unidades_mes_con_cultivo_y_valor"]}
                                   for k, v in comparar(c15, meses).items()}}
out["cultivo_1_3_contra_cultivo_1_5"] = {}
for v in ("precipitacion_final", "t2m", "humedad_radicular", "ndvi"):
    a = pd.read_csv(base / f"serie_mensual_{v}_cultivo.csv.gz"); b = pd.read_csv(c15 / f"serie_mensual_{v}_cultivo.csv.gz")
    out["cultivo_1_3_contra_cultivo_1_5"][v] = dif_rel(a, b)
import simulacion.geo.pi_d1_colombia as P
P.VARS = {"ndvi": P.VARS["ndvi"]}  # la carpeta rel0 solo trae NDVI
out["ndvi_reliability_solo_0"] = {"pi_d1": {k: v["fraccion_unidades_con_dif_relativa_mayor_a"] | {"pares": v["unidades_mes_con_cultivo_y_valor"]} for k, v in comparar(rel0, meses).items()}}
for modo in ("area", "cultivo"):
    a = pd.read_csv(base / f"serie_mensual_ndvi_{modo}.csv.gz"); b = pd.read_csv(rel0 / f"serie_mensual_ndvi_{modo}.csv.gz")
    d = dif_rel(a, b); d["frac_valida_media_0y1"] = round(float(a[a.mes.isin(meses)].frac_valida.mean()), 4)
    d["frac_valida_media_solo0"] = round(float(b[b.mes.isin(meses)].frac_valida.mean()), 4)
    d["unidades_mes_sin_valor_0y1"] = int((a[a.mes.isin(meses)].valor.isna()).sum()); d["unidades_mes_sin_valor_solo0"] = int((b[b.mes.isin(meses)].valor.isna()).sum())
    out[f"ndvi_0y1_contra_solo0_{modo}"] = d
Path(salida).write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding="utf8")
