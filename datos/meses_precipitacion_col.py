# asistido por SI: Claude Code, primer y ultimo mes de IMERG Final y Late en las series de Colombia (T-D2)
import sys
import pandas as pd
for k in ("final", "late"):
    for m in ("area", "cultivo"):
        d = pd.read_csv(f"{sys.argv[1]}/serie_mensual_precipitacion_{k}_{m}.csv.gz", usecols=["mes", "estado", "version", "unidad"])
        ms = sorted(d.mes.unique())
        print(k, m, "primer", ms[0], "ultimo", ms[-1], "n_meses", len(ms), "estado", d.estado.unique().tolist(), "unidad", d.unidad.unique().tolist(), "version", d.version.unique().tolist())
