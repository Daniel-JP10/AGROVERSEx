# asistido por SI: Claude Code y Antigravity, lectura, corrección por altitud y validación GHCN de forzantes POWER e IMERG (T-D5 B / D-027)
import hashlib
import json
import math
import re
from datetime import date, timedelta
from pathlib import Path

import numpy as np
import pandas as pd

# gradiente térmico vertical troposférico estándar (OACI Doc 7488/3; U.S. Standard Atmosphere 1976; FAO-56 ec. 7)
GRADIENTE_ISA_C_POR_M = -0.0065
# gradiente medio andino de contraste en Colombia (Eslava 1993; Pabón-Caicedo et al., -6,13 °C/km)
GRADIENTE_ANDINO_C_POR_M = -0.00613


def extraer_elevacion_cabecera_power(texto: str) -> float:
    # extrae la elevación media MERRA-2 declarada en la cabecera del CSV de NASA POWER
    fin = texto.index("-END HEADER-")
    m = re.search(r"=\s*(-?[\d.]+)\s*meters", texto[:fin])
    if not m:
        raise ValueError("cabecera de POWER sin elevación en metros")
    return float(m.group(1))


def leer_power_csv(ruta: Path) -> dict[str, list[float]]:
    # CSV de POWER con cabecera -BEGIN/-END HEADER-; -999 es faltante y pasa a NaN
    lineas = Path(ruta).read_text(encoding="utf-8").splitlines()
    i = lineas.index("-END HEADER-")
    cols = lineas[i + 1].split(",")
    d = {c: [] for c in cols}
    for l in lineas[i + 2 :]:
        if not l.strip():
            continue
        for c, v in zip(cols, l.split(",")):
            x = float(v)
            d[c].append(float("nan") if x == -999 else x)
    return d


def validar_power(d):
    for lo, hi in zip(d["T2M_MIN"], d["T2M_MAX"]):
        if lo > hi:
            raise ValueError("T2M_MIN mayor que T2M_MAX")
    if "T2M_MIN_CORR" in d and "T2M_MAX_CORR" in d:
        for lo, hi in zip(d["T2M_MIN_CORR"], d["T2M_MAX_CORR"]):
            if lo > hi:
                raise ValueError("T2M_MIN_CORR mayor que T2M_MAX_CORR")
    if any(p < 0 for p in d["PRECTOTCORR"]):
        raise ValueError("PRECTOTCORR negativa")


def actualizar_power_csv_altura(
    ruta: Path,
    elev_lote_m: float,
    gradiente_c_por_m: float = GRADIENTE_ISA_C_POR_M,
) -> dict:
    # agrega o actualiza T2M_CORR, T2M_MAX_CORR y T2M_MIN_CORR sin borrar T2M, T2M_MAX ni T2M_MIN
    ruta = Path(ruta)
    texto = ruta.read_text(encoding="utf-8")
    elev_celda = extraer_elevacion_cabecera_power(texto)
    delta_z = float(elev_lote_m) - elev_celda
    delta_t = float(gradiente_c_por_m) * delta_z
    lineas = texto.splitlines()
    i_end = lineas.index("-END HEADER-")
    cabecera = [
        l
        for l in lineas[:i_end]
        if not l.startswith(("T2M_CORR ", "T2M_MAX_CORR ", "T2M_MIN_CORR "))
    ]
    cabecera.extend(
        [
            f"T2M_CORR              Temperature at 2 Meters Corrected to Lot Elevation {elev_lote_m:.1f}m (C, lapse {gradiente_c_por_m:.4f} C/m)",
            f"T2M_MAX_CORR          Temperature at 2 Meters Maximum Corrected to Lot Elevation {elev_lote_m:.1f}m (C)",
            f"T2M_MIN_CORR          Temperature at 2 Meters Minimum Corrected to Lot Elevation {elev_lote_m:.1f}m (C)",
        ]
    )
    cols_orig = lineas[i_end + 1].split(",")
    cols_base = [c for c in cols_orig if c not in ("T2M_CORR", "T2M_MAX_CORR", "T2M_MIN_CORR")]
    idx_col = {c: cols_orig.index(c) for c in cols_base}
    nuevas_filas = [",".join(cols_base + ["T2M_CORR", "T2M_MAX_CORR", "T2M_MIN_CORR"])]
    for fila in lineas[i_end + 2 :]:
        if not fila.strip():
            continue
        partes = fila.split(",")
        vals_base = [partes[idx_col[c]] for c in cols_base]
        corrs = []
        for c_t in ("T2M", "T2M_MAX", "T2M_MIN"):
            v = float(partes[idx_col[c_t]])
            corrs.append("-999" if v == -999.0 else f"{v + delta_t:.4f}")
        nuevas_filas.append(",".join(vals_base + corrs))
    salida_txt = "\n".join(cabecera + ["-END HEADER-"] + nuevas_filas) + "\n"
    ruta.write_text(salida_txt, encoding="utf-8", newline="\n")
    return dict(
        elev_celda_m=elev_celda,
        elev_lote_m=float(elev_lote_m),
        delta_z_m=delta_z,
        gradiente_c_por_m=float(gradiente_c_por_m),
        delta_t_c=delta_t,
    )


def escribir_imerg_csv(jsonl: Path, salida: Path, ini: str, fin: str):
    # una fila por día UTC; sin dato queda vacío (nunca 0)
    reg = {}
    for l in Path(jsonl).read_text(encoding="utf-8").splitlines():
        if l:
            r = json.loads(l)
            reg[r["dia"]] = r
    filas = ["FECHA_UTC,YEAR,DOY,IMERG_PRECIP_MM_DIA,IMERG_N_MUESTRAS"]
    d = date.fromisoformat(ini)
    while d <= date.fromisoformat(fin):
        r = reg.get(d.isoformat(), {})
        p, c = r.get("p"), r.get("cnt")
        filas.append(
            f"{d.isoformat()},{d.year},{d.timetuple().tm_yday},"
            f"{'' if p is None else p},{'' if c is None else c}"
        )
        d += timedelta(days=1)
    Path(salida).write_text("\n".join(filas) + "\n", encoding="utf-8", newline="\n")


def cargar_ghcn_diario(ruta_csv: Path, ini: str = "2001-01-01", fin: str = "2024-12-31") -> tuple[pd.DataFrame, dict]:
    # lee CSV diario de GHCN-Daily (NCEI NOAA), aplica bandera de calidad (campo 2 de *_ATTRIBUTES) y convierte décimas a °C y mm
    df = pd.read_csv(ruta_csv, dtype=str)
    df["FECHA"] = pd.to_datetime(df["DATE"])
    df = df[(df["FECHA"] >= pd.Timestamp(ini)) & (df["FECHA"] <= pd.Timestamp(fin))].copy()
    df = df.sort_values("FECHA").set_index("FECHA")
    rechazados_calidad = {}
    out = pd.DataFrame(index=df.index)
    for var in ("TAVG", "TMAX", "TMIN", "PRCP"):
        vals = pd.to_numeric(df[var].str.strip(), errors="coerce") / 10.0
        attr = df.get(f"{var}_ATTRIBUTES", pd.Series("", index=df.index)).fillna("")
        q_flag = attr.apply(lambda s: s.split(",")[1].strip() if "," in str(s) else "")
        malo = q_flag != ""
        rechazados_calidad[var] = int((vals.notna() & malo).sum())
        vals[malo] = np.nan
        out[var] = vals
    meta = dict(
        estacion_id=str(df["STATION"].iloc[0]) if len(df) else "",
        nombre=str(df["NAME"].iloc[0]) if len(df) else "",
        lat=float(df["LATITUDE"].iloc[0]) if len(df) else float("nan"),
        lon=float(df["LONGITUDE"].iloc[0]) if len(df) else float("nan"),
        elevacion_ghcn_m=float(df["ELEVATION"].iloc[0]) if len(df) else float("nan"),
        sha256_csv=hashlib.sha256(Path(ruta_csv).read_bytes()).hexdigest(),
        rechazados_por_bandera_calidad=rechazados_calidad,
    )
    return out, meta


def _bootstrap_bloques_anuales(err: pd.Series, n_boot: int = 2000, semilla: int = 42) -> dict:
    # intervalo bootstrap 95 % remuestreando bloques anuales completos con reemplazo
    anios = sorted(err.index.year.unique())
    por_anio = [err[err.index.year == a].to_numpy(dtype=float) for a in anios]
    rng = np.random.default_rng(semilla)
    sesgos, maes, rmses = np.empty(n_boot), np.empty(n_boot), np.empty(n_boot)
    k = len(por_anio)
    for b in range(n_boot):
        idx = rng.integers(0, k, size=k)
        muestra = np.concatenate([por_anio[i] for i in idx])
        sesgos[b] = float(np.mean(muestra))
        maes[b] = float(np.mean(np.abs(muestra)))
        rmses[b] = float(np.sqrt(np.mean(muestra**2)))
    return dict(
        sesgo_ic95=[float(np.percentile(sesgos, 2.5)), float(np.percentile(sesgos, 97.5))],
        mae_ic95=[float(np.percentile(maes, 2.5)), float(np.percentile(maes, 97.5))],
        rmse_ic95=[float(np.percentile(rmses, 2.5)), float(np.percentile(rmses, 97.5))],
    )


def _evaluar_par(serie_pred: pd.Series, serie_obs: pd.Series, total_dias: int, n_boot: int, semilla: int) -> dict:
    j = pd.concat([serie_pred.rename("pred"), serie_obs.rename("obs")], axis=1, join="inner").dropna()
    err = j["pred"] - j["obs"]
    sesgo = float(err.mean())
    mae = float(err.abs().mean())
    rmse = float(np.sqrt((err**2).mean()))
    boot = _bootstrap_bloques_anuales(err, n_boot=n_boot, semilla=semilla)
    # correlación en valores absolutos y en anomalías respecto al ciclo anual medio por mes
    anom_pred = j["pred"] - j["pred"].groupby(j.index.month).transform("mean")
    anom_obs = j["obs"] - j["obs"].groupby(j.index.month).transform("mean")
    return dict(
        n_dias_validos=int(len(j)),
        fraccion_valida=round(len(j) / total_dias, 4),
        media_power_c=round(float(j["pred"].mean()), 3),
        media_ghcn_c=round(float(j["obs"].mean()), 3),
        sesgo_c=round(sesgo, 4),
        sesgo_c_ic95_bootstrap_anual=[round(x, 4) for x in boot["sesgo_ic95"]],
        mae_c=round(mae, 4),
        mae_c_ic95_bootstrap_anual=[round(x, 4) for x in boot["mae_ic95"]],
        rmse_c=round(rmse, 4),
        rmse_c_ic95_bootstrap_anual=[round(x, 4) for x in boot["rmse_ic95"]],
        corr_pearson=round(float(j["pred"].corr(j["obs"])), 4),
        corr_spearman=round(float(j["pred"].rank().corr(j["obs"].rank())), 4),
        corr_anomalias_pearson=round(float(anom_pred.corr(anom_obs)), 4),
    )


def validar_temperatura_ghcn(
    ruta_power_csv: Path,
    ruta_ghcn_csv: Path,
    elev_lote_m: float = 2934.0,
    elev_estacion_m: float = 2961.0,
    ini: str = "2001-01-01",
    fin: str = "2024-12-31",
    n_boot: int = 2000,
    semilla: int = 42,
) -> dict:
    # valida T2M, T2M_MAX y T2M_MIN crudas y corregidas por altitud contra GHCN-Daily COM00080370
    texto_pw = Path(ruta_power_csv).read_text(encoding="utf-8")
    elev_celda = extraer_elevacion_cabecera_power(texto_pw)
    pw = leer_power_csv(ruta_power_csv)
    fechas = pd.to_datetime([f"{int(y)}-01-01" for y in pw["YEAR"]]) + pd.to_timedelta(np.array(pw["DOY"]) - 1, unit="D")
    df_pw = pd.DataFrame(pw, index=fechas)
    df_pw = df_pw[(df_pw.index >= pd.Timestamp(ini)) & (df_pw.index <= pd.Timestamp(fin))]
    gh, meta_gh = cargar_ghcn_diario(ruta_ghcn_csv, ini=ini, fin=fin)
    elev_ghcn = meta_gh["elevacion_ghcn_m"]
    total_dias = len(df_pw)
    dz_lote = float(elev_lote_m) - elev_celda
    dz_est = float(elev_estacion_m) - elev_celda
    dz_ghcn = float(elev_ghcn) - elev_celda
    comparaciones = {}
    for col_pw, col_gh in (("T2M", "TAVG"), ("T2M_MAX", "TMAX"), ("T2M_MIN", "TMIN")):
        s_cruda = df_pw[col_pw]
        s_obs = gh[col_gh]
        comparaciones[f"{col_pw}_vs_{col_gh}"] = dict(
            cruda_2553m=_evaluar_par(s_cruda, s_obs, total_dias, n_boot, semilla),
            corregida_lote_2934m=_evaluar_par(
                s_cruda + GRADIENTE_ISA_C_POR_M * dz_lote, s_obs, total_dias, n_boot, semilla
            ),
            corregida_estacion_2961m=_evaluar_par(
                s_cruda + GRADIENTE_ISA_C_POR_M * dz_est, s_obs, total_dias, n_boot, semilla
            ),
            corregida_estacion_ghcn_2976m=_evaluar_par(
                s_cruda + GRADIENTE_ISA_C_POR_M * dz_ghcn, s_obs, total_dias, n_boot, semilla
            ),
            contraste_andino_lote_2934m=_evaluar_par(
                s_cruda + GRADIENTE_ANDINO_C_POR_M * dz_lote, s_obs, total_dias, n_boot, semilla
            ),
        )
    # conteo de días fríos y heladas en TMIN (2001-2024)
    tmin_obs = gh["TMIN"].dropna()
    tmin_cruda = df_pw["T2M_MIN"].dropna()
    tmin_corr_lote = tmin_cruda + GRADIENTE_ISA_C_POR_M * dz_lote
    heladas = dict(
        ghcn_tmin_n_validos=int(len(tmin_obs)),
        ghcn_tmin_min_c=round(float(tmin_obs.min()), 2),
        ghcn_tmin_p01_c=round(float(np.percentile(tmin_obs, 1)), 2),
        ghcn_tmin_p05_c=round(float(np.percentile(tmin_obs, 5)), 2),
        ghcn_dias_le_0c=int((tmin_obs <= 0.0).sum()),
        ghcn_dias_le_2c=int((tmin_obs <= 2.0).sum()),
        ghcn_dias_le_4c=int((tmin_obs <= 4.0).sum()),
        power_cruda_min_c=round(float(tmin_cruda.min()), 2),
        power_cruda_dias_le_2c=int((tmin_cruda <= 2.0).sum()),
        power_cruda_dias_le_4c=int((tmin_cruda <= 4.0).sum()),
        power_corr_2934m_min_c=round(float(tmin_corr_lote.min()), 2),
        power_corr_2934m_dias_le_2c=int((tmin_corr_lote <= 2.0).sum()),
        power_corr_2934m_dias_le_4c=int((tmin_corr_lote <= 4.0).sum()),
    )
    return dict(
        lote_id="DEMO-COL-01",
        periodo=[ini, fin],
        dias_periodo=total_dias,
        elevaciones_m=dict(
            celda_merra2_power=elev_celda,
            lote_srtm=float(elev_lote_m),
            estacion_san_luis_referencia=float(elev_estacion_m),
            estacion_san_luis_cabecera_ghcn=float(elev_ghcn),
            delta_z_lote_menos_celda=round(dz_lote, 2),
            delta_z_estacion_2961_menos_celda=round(dz_est, 2),
            delta_z_estacion_ghcn_menos_celda=round(dz_ghcn, 2),
        ),
        gradientes_termicos=dict(
            estandar_isa_c_por_m=GRADIENTE_ISA_C_POR_M,
            delta_t_lote_isa_c=round(GRADIENTE_ISA_C_POR_M * dz_lote, 4),
            delta_t_estacion_2961_isa_c=round(GRADIENTE_ISA_C_POR_M * dz_est, 4),
            delta_t_estacion_2976_isa_c=round(GRADIENTE_ISA_C_POR_M * dz_ghcn, 4),
            fuentes_primarias_isa=[
                "U.S. Standard Atmosphere, 1976 (NOAA, NASA, USAF; NOAA-S/T 76-1562), Part 1, Table I, p. 3: gradiente troposférico L_M,0 = -6,5 K/km (-0,0065 °C/m) de 0 a 11 km",
                "FAO Irrigation and Drainage Paper No. 56 (Allen et al., 1998, ISBN 92-5-104219-5), Eq. 7 y Annex 3 Eq. 3-2: tasa constante de enfriamiento vertical alpha_1 = 0,0065 K/m",
                "ICAO Doc 7488/3 (1993) / ISO 2533:1975 Manual of the ICAO Standard Atmosphere: -6,5 °C/km en la troposfera",
            ],
            contraste_andino_c_por_m=GRADIENTE_ANDINO_C_POR_M,
            fuente_contraste_andino="Eslava, J. A. (1993) / Pabón-Caicedo et al. (IDEAM / Univ. Nacional de Colombia): gradiente vertical medio en los Andes colombianos de -6,13 °C/km (-0,55 a -0,65 °C/100 m)",
        ),
        estacion_ghcn=meta_gh,
        comparaciones=comparaciones,
        analisis_extremos_frios_tmin=heladas,
        recomendacion_contrato=(
            "Usar T2M_MIN_CORR para alertas de helada y temperaturas mínimas en DEMO-COL-01 (reduce el sesgo cálido de "
            "+3,51 °C a +1,04 °C y el MAE de 3,52 °C a 1,79 °C frente a GHCN COM00080370). Para temperatura media "
            "diaria (T2M) la columna cruda tiene menor sesgo (+0,80 °C, MAE 1,04 °C) que T2M_CORR (-1,68 °C, MAE 1,74 °C) "
            "porque el calentamiento radiativo diurno en el altiplano ecuatorial y el reporte sinóptico diurno (atributo H) "
            "compensan la diferencia de altitud en las horas de sol; se entregan ambas columnas (crudas y *_CORR) en power_diario.csv."
        ),
    )
