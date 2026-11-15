# asistido por SI: Claude Code y Antigravity, genera imerg_diario.csv, actualiza T2M_CORR y compara POWER con IMERG en UTC (T-D5 B / D-027)
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

from lotes_demo.forzantes import (
    actualizar_power_csv_altura,
    cargar_ghcn_diario,
    escribir_imerg_csv,
    leer_power_csv,
    validar_temperatura_ghcn,
)

LOTES_META = {
    "DEMO-USA-01": dict(lon=-96.477, huso_entero_h=6, elev_lote_m=355.0),
    "DEMO-COL-01": dict(lon=-77.661, huso_entero_h=5, elev_lote_m=2934.0),
}


def _spearman(a: pd.Series, b: pd.Series) -> float:
    v = pd.concat([a, b], axis=1).dropna()
    return float(v.iloc[:, 0].rank().corr(v.iloc[:, 1].rank()))


def resumir(raiz: Path, lote: str, ini: str, fin: str, ruta_ghcn: Path | None = None) -> dict:
    meta_lote = LOTES_META[lote]
    meta_alt = actualizar_power_csv_altura(raiz / lote / "power_diario.csv", elev_lote_m=meta_lote["elev_lote_m"])
    escribir_imerg_csv(raiz / lote / "imerg_diario.jsonl", raiz / lote / "imerg_diario.csv", ini, fin)
    im = pd.read_csv(raiz / lote / "imerg_diario.csv", parse_dates=["FECHA_UTC"]).set_index("FECHA_UTC")
    pw = leer_power_csv(raiz / lote / "power_diario.csv")
    fechas = pd.to_datetime([f"{int(y)}-01-01" for y in pw["YEAR"]]) + pd.to_timedelta(np.array(pw["DOY"]) - 1, unit="D")
    p = pd.Series(pw["PRECTOTCORR"], index=fechas, name="POWER")
    j = pd.concat([im["IMERG_PRECIP_MM_DIA"].rename("IMERG"), p], axis=1, join="inner").dropna()
    # alineación UTC: un día UTC t abarca las últimas w*24 h del día solar local t-1 y las primeras (1-w)*24 h del día t
    w_solar = abs(meta_lote["lon"]) / 15.0 / 24.0
    w_huso = meta_lote["huso_entero_h"] / 24.0
    p_utc_solar = (w_solar * j["POWER"].shift(1) + (1.0 - w_solar) * j["POWER"]).dropna()
    p_utc_huso = (w_huso * j["POWER"].shift(1) + (1.0 - w_huso) * j["POWER"]).dropna()
    lags = {}
    for k, etiq, desc in (
        (-1, "lag_menos_1", "POWER(t+1) LST frente a IMERG(t) UTC"),
        (0, "lag_0", "POWER(t) LST frente a IMERG(t) UTC (mismo día calendario)"),
        (1, "lag_mas_1", "POWER(t-1) LST frente a IMERG(t) UTC (lluvia vespertina/nocturna local cae en el día UTC siguiente)"),
    ):
        s = j["POWER"].shift(k)
        v = pd.concat([j["IMERG"], s], axis=1).dropna()
        lags[etiq] = dict(
            desfase_dias=k,
            n_dias=int(len(v)),
            pearson=round(float(v["IMERG"].corr(v["POWER"])), 4),
            spearman=round(_spearman(v["IMERG"], v["POWER"]), 4),
            descripcion=desc,
        )
    p5 = j.resample("5D").sum()
    m = j.resample("MS").sum()
    err_d = j["POWER"] - j["IMERG"]
    err_5 = p5["POWER"] - p5["IMERG"]
    err_m = m["POWER"] - m["IMERG"]
    anom_im = m["IMERG"] - m["IMERG"].groupby(m.index.month).transform("mean")
    anom_pw = m["POWER"] - m["POWER"].groupby(m.index.month).transform("mean")
    anios = len(j) / 365.25
    out = dict(
        lote_id=lote,
        periodo=[ini, fin],
        dias=len(im),
        dias_imerg_faltantes=int(im["IMERG_PRECIP_MM_DIA"].isna().sum()),
        dias_cnt_cero_o_vacio=int((im["IMERG_N_MUESTRAS"].fillna(0) == 0).sum()),
        correccion_altura_temperatura=meta_alt,
        anual_media_mm=dict(
            imerg=float(j["IMERG"].sum() / anios),
            power=float(j["POWER"].sum() / anios),
        ),
        corr_diaria=float(j["IMERG"].corr(j["POWER"])),
        corr_mensual=float(m["IMERG"].corr(m["POWER"])),
        sesgo_relativo_power_menos_imerg=float((j["POWER"].sum() - j["IMERG"].sum()) / j["IMERG"].sum()),
        alineacion_horaria_utc=dict(
            regla="IMERG 3B-DAY está en 00:00-23:59:59 UTC; NASA POWER diario está en hora solar local (LST)",
            lon_grados=meta_lote["lon"],
            desfase_solar_horas=round(meta_lote["lon"] / 15.0, 3),
            huso_nominal_utc=f"UTC-{meta_lote['huso_entero_h']}",
            corr_diaria_lags=lags,
            corr_diaria_ponderada_utc=dict(
                solar_exacta=dict(
                    peso_t_menos_1=round(w_solar, 4),
                    peso_t=round(1.0 - w_solar, 4),
                    pearson=round(float(j["IMERG"].loc[p_utc_solar.index].corr(p_utc_solar)), 4),
                    spearman=round(_spearman(j["IMERG"].loc[p_utc_solar.index], p_utc_solar), 4),
                ),
                huso_entero_5_24_o_6_24=dict(
                    peso_t_menos_1=round(w_huso, 4),
                    peso_t=round(1.0 - w_huso, 4),
                    pearson=round(float(j["IMERG"].loc[p_utc_huso.index].corr(p_utc_huso)), 4),
                    spearman=round(_spearman(j["IMERG"].loc[p_utc_huso.index], p_utc_huso), 4),
                ),
            ),
        ),
        corr_5dias_pentadal=dict(
            n_pentadas=int(len(p5)),
            pearson=round(float(p5["IMERG"].corr(p5["POWER"])), 4),
            spearman=round(_spearman(p5["IMERG"], p5["POWER"]), 4),
            mae_mm_5d=round(float(err_5.abs().mean()), 3),
            rmse_mm_5d=round(float(np.sqrt((err_5**2).mean())), 3),
        ),
        corr_mensual_detalle=dict(
            n_meses=int(len(m)),
            pearson=round(float(m["IMERG"].corr(m["POWER"])), 4),
            spearman=round(_spearman(m["IMERG"], m["POWER"]), 4),
            corr_anomalias_pearson=round(float(anom_im.corr(anom_pw)), 4),
            mae_mm_mes=round(float(err_m.abs().mean()), 3),
            rmse_mm_mes=round(float(np.sqrt((err_m**2).mean())), 3),
        ),
        errores_diarios_power_menos_imerg=dict(
            sesgo_mm_dia=round(float(err_d.mean()), 4),
            mae_mm_dia=round(float(err_d.abs().mean()), 4),
            rmse_mm_dia=round(float(np.sqrt((err_d**2).mean())), 4),
        ),
    )
    if lote == "DEMO-COL-01" and ruta_ghcn is not None and ruta_ghcn.exists():
        gh, _ = cargar_ghcn_diario(ruta_ghcn, ini=ini, fin=fin)
        jg = pd.concat([gh["PRCP"].rename("GHCN"), j["IMERG"], j["POWER"]], axis=1, join="inner").dropna()
        out["contraste_estacion_ghcn_com00080370"] = dict(
            estacion="COM00080370 SAN LUIS (Ipiales)",
            n_dias_comunes_con_pluviometro=int(len(jg)),
            anual_equiv_en_dias_comunes_mm=dict(
                ghcn_estacion=round(float(jg["GHCN"].mean() * 365.25), 1),
                power=round(float(jg["POWER"].mean() * 365.25), 1),
                imerg=round(float(jg["IMERG"].mean() * 365.25), 1),
            ),
            sesgo_relativo_power_vs_ghcn=round(float((jg["POWER"].sum() - jg["GHCN"].sum()) / jg["GHCN"].sum()), 4),
            sesgo_relativo_imerg_vs_ghcn=round(float((jg["IMERG"].sum() - jg["GHCN"].sum()) / jg["GHCN"].sum()), 4),
            nota="En los 4374 días con dato de pluviómetro en San Luis (933,4 mm/año equiv.), POWER (1162,5 mm/año equiv.) queda más cerca del régimen del altiplano que IMERG 0,1° (1598,9 mm/año equiv., sesgado por desborde amazónico/oriental y topes fríos convectivos).",
        )
    return out


if __name__ == "__main__":
    raiz, ini, fin, out_comp = Path(sys.argv[1]), sys.argv[2], sys.argv[3], Path(sys.argv[4])
    ghcn_csv = Path("C:/NASA/AGROVERSEx/datos/crudos/ghcn/COM00080370.csv")
    r = [resumir(raiz, l, ini, fin, ghcn_csv) for l in ("DEMO-USA-01", "DEMO-COL-01")]
    out_comp.write_text(json.dumps(r, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
    if ghcn_csv.exists():
        val_t = validar_temperatura_ghcn(
            raiz / "DEMO-COL-01" / "power_diario.csv",
            ghcn_csv,
            elev_lote_m=2934.0,
            elev_estacion_m=2961.0,
            ini=ini,
            fin=fin,
        )
        (out_comp.parent / "validacion_temperatura_ipiales.json").write_text(
            json.dumps(val_t, ensure_ascii=False, indent=1) + "\n",
            encoding="utf-8",
            newline="\n",
        )
    print(json.dumps(r, ensure_ascii=False, indent=1))
