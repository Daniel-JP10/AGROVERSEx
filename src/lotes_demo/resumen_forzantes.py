# asistido por SI: Claude Code, genera imerg_diario.csv y compara POWER con IMERG por lote (T-D5 Parte B)
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

from lotes_demo.forzantes import escribir_imerg_csv, leer_power_csv


def resumir(raiz: Path, lote: str, ini: str, fin: str) -> dict:
    escribir_imerg_csv(raiz / lote / "imerg_diario.jsonl", raiz / lote / "imerg_diario.csv", ini, fin)
    im = pd.read_csv(raiz / lote / "imerg_diario.csv", parse_dates=["FECHA_UTC"]).set_index("FECHA_UTC")
    pw = leer_power_csv(raiz / lote / "power_diario.csv")
    p = pd.Series(pw["PRECTOTCORR"], index=pd.to_datetime(
        [f"{int(y)}-01-01" for y in pw["YEAR"]]) + pd.to_timedelta(np.array(pw["DOY"]) - 1, unit="D"))
    j = pd.concat([im["IMERG_PRECIP_MM_DIA"], p.rename("POWER")], axis=1, join="inner").dropna()
    m = j.resample("MS").sum()
    return dict(lote_id=lote, periodo=[ini, fin], dias=len(im), dias_imerg_faltantes=int(im["IMERG_PRECIP_MM_DIA"].isna().sum()),
                dias_cnt_cero_o_vacio=int((im["IMERG_N_MUESTRAS"].fillna(0) == 0).sum()),
                anual_media_mm=dict(imerg=float(j.IMERG_PRECIP_MM_DIA.sum() / (len(j) / 365.25)),
                                    power=float(j.POWER.sum() / (len(j) / 365.25))),
                corr_diaria=float(j.corr().iloc[0, 1]), corr_mensual=float(m.corr().iloc[0, 1]),
                sesgo_relativo_power_menos_imerg=float((j.POWER.sum() - j.IMERG_PRECIP_MM_DIA.sum()) / j.IMERG_PRECIP_MM_DIA.sum()))


if __name__ == "__main__":
    raiz, ini, fin = Path(sys.argv[1]), sys.argv[2], sys.argv[3]
    r = [resumir(raiz, l, ini, fin) for l in ("DEMO-USA-01", "DEMO-COL-01")]
    Path(sys.argv[4]).write_text(json.dumps(r, indent=1), encoding="utf-8")
    print(json.dumps(r, indent=1))
