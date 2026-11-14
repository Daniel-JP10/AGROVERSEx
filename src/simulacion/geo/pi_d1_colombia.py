# asistido por SI: Claude Code (Anthropic), respuesta preliminar de PI-D1 en Colombia (area frente a cultivo)
"""python -m simulacion.geo.pi_d1_colombia <carpeta de series COL> <salida.json> [AAAA-MM ...]

Compara, en unidades de nivel 2 con cultivo, el valor de ponderacion=cultivo contra el de ponderacion=area."""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

VARS = {"precipitacion_final": "lluvia (IMERG Final, mm/hr)", "ndvi": "NDVI (MOD13C2)"}


def comparar(carpeta: Path, meses: list[str]) -> dict:
    out = {}
    for v, nombre in VARS.items():
        a = pd.read_csv(carpeta / f"serie_mensual_{v}_area.csv.gz")
        c = pd.read_csv(carpeta / f"serie_mensual_{v}_cultivo.csv.gz")
        a, c = a[a.nivel == 2], c[c.nivel == 2]
        m = a.merge(c, on=["unidad_id", "mes"], suffixes=("_a", "_c"))
        m = m[m.mes.isin(meses)]
        con_cultivo = m.motivo_c.isna() & m.valor_a.notna()
        d = m[con_cultivo]
        dif = d.valor_c - d.valor_a
        rel = dif / d.valor_a.abs()
        fuera = (d.valor_c < d.p10_a) | (d.valor_c > d.p90_a)
        out[v] = dict(
            descripcion=nombre, meses=meses, unidades_nivel2=int(m.unidad_id.nunique()),
            unidades_mes_con_cultivo_y_valor=int(len(d)), sin_cultivo_o_sin_valor=int((~con_cultivo).sum()),
            diferencia_cultivo_menos_area=dict(zip(["p1", "p5", "p25", "p50", "p75", "p95", "p99"],
                                                   np.percentile(dif, [1, 5, 25, 50, 75, 95, 99]).round(5).tolist())),
            diferencia_absoluta_media=round(float(dif.abs().mean()), 5),
            diferencia_relativa_abs_percentiles=dict(zip(["p50", "p75", "p90", "p95", "p99"],
                                                         np.percentile(rel.abs(), [50, 75, 90, 95, 99]).round(5).tolist())),
            fraccion_unidades_con_dif_relativa_mayor_a={f"{u}%": round(float((rel.abs() > u / 100).mean()), 4) for u in (2, 5, 10, 20)},
            fraccion_con_valor_cultivo_fuera_de_p10_p90_area=round(float(fuera.mean()), 4),
            correlacion=round(float(np.corrcoef(d.valor_a, d.valor_c)[0, 1]), 5))
    return out


if __name__ == "__main__":
    carpeta, salida, meses = Path(sys.argv[1]), Path(sys.argv[2]), sys.argv[3:]
    Path(salida).write_text(json.dumps(comparar(carpeta, meses), indent=1, ensure_ascii=False), encoding="utf8")
