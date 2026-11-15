# asistido por SI: Claude Code, fixture JSON del empalme IMERG Final a Late en Colombia (T-D2)
"""python fixture_empalme_imerg.py SERIES_COL_DIR salida.json"""
import json
import sys
import pandas as pd

d = sys.argv[1]
cols = ["unidad_id", "nivel", "mes", "valor", "unidad", "estado", "motivo"]
f = pd.read_csv(f"{d}/serie_mensual_precipitacion_final_area.csv.gz", usecols=cols)
l = pd.read_csv(f"{d}/serie_mensual_precipitacion_late_area.csv.gz", usecols=cols)
u = ["COL-ADM0"] + f[f.nivel == 1].unidad_id.drop_duplicates().iloc[[0, 5, 10, 20]].tolist()
meses_f = [f"{a}-{m}" for a in range(2015, 2026) for m in ("09", "10") if f"{a}-{m}" <= "2025-09"]
filas = pd.concat([f[f.unidad_id.isin(u) & f.mes.isin(meses_f)], l[l.unidad_id.isin(u) & (l.mes == "2025-10")]])
filas = filas[filas.motivo.isna()].drop(columns=["motivo", "nivel"])
json.dump(filas.to_dict("records"), open(sys.argv[2], "w"), indent=0)
print(len(filas), "filas", sorted(filas.unidad.unique()))
