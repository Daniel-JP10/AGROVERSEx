# asistido por SI: Antigravity (Google DeepMind), cálculo de exposición erosiva, umbrales semanales P90, pendiente NASADEM y erodabilidad K (T-D6 Idea 2)
import json
import math
import sys
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd

CONVERSION_K_SI = 0.1317  # Foster et al. (1981), J. Soil Water Conserv. 36(6): 355-359
UMBRAL_TORMENTA_MIN_MM = 0.1  # evita contar días secos (0 mm) como tormenta si P90 semanal es 0


def semana_del_anio(fechas) -> np.ndarray:
    # convierte fechas a semana del año 1..52 (los días 358..366 entran en la semana 52)
    idx = pd.DatetimeIndex(pd.to_datetime(fechas))
    doy = np.asarray(idx.dayofyear, dtype=int)
    return np.minimum((doy - 1) // 7 + 1, 52)


def umbral_p90_semanal(
    precip_mm_dia,
    fechas,
    fecha_corte: str | None = None,
    solo_dias_humedos: bool = False,
    umbral_humedo_mm: float = 0.1,
) -> dict[int, float]:
    # calcula el percentil 90 histórico por semana del año (1..52) sin usar datos posteriores a fecha_corte
    p = np.asarray(precip_mm_dia, dtype=float)
    f = pd.DatetimeIndex(pd.to_datetime(fechas))
    if len(p) != len(f):
        raise ValueError("precip_mm_dia y fechas deben tener la misma longitud")
    mask = np.isfinite(p)
    if fecha_corte is not None:
        mask = mask & (np.asarray(f <= pd.Timestamp(fecha_corte), dtype=bool))
    p_val = p[mask]
    sem_val = semana_del_anio(f[mask])
    out: dict[int, float] = {}
    for w in range(1, 53):
        vals = p_val[sem_val == w]
        if solo_dias_humedos:
            vals = vals[vals >= umbral_humedo_mm]
        out[w] = float(np.percentile(vals, 90)) if len(vals) > 0 else float("nan")
    return out


def factor_pendiente_mccool(pendiente_m_m: float) -> float:
    # factor S de McCool et al. (1987), Trans. ASAE 30(5): 1387-1396 y Renard et al. (1997), USDA AH-703 ec. 4-4 y 4-5
    s = float(pendiente_m_m)
    if s < 0.0:
        raise ValueError("pendiente_m_m no puede ser negativa")
    sen_theta = s / math.sqrt(1.0 + s * s)
    if s < 0.09:
        return 10.8 * sen_theta + 0.03
    return 16.8 * sen_theta - 0.50


def factor_erodabilidad_williams(
    arena_kg_kg: float,
    limo_kg_kg: float,
    arcilla_kg_kg: float,
    soc_g_kg: float,
) -> float:
    # factor K de Williams (1995) / Sharpley y Williams (1990, EPIC, USDA TB-1768) en unidades SI (t·ha·h/(ha·MJ·mm))
    ms = max(float(arena_kg_kg) * 100.0, 0.0)
    msilt = max(float(limo_kg_kg) * 100.0, 0.0)
    mc = max(float(arcilla_kg_kg) * 100.0, 0.0)
    orgc = max(float(soc_g_kg) / 10.0, 0.0)
    f_csand = 0.2 + 0.3 * math.exp(-0.256 * ms * (1.0 - msilt / 100.0))
    f_cl_si = (msilt / max(mc + msilt, 1e-9)) ** 0.3
    f_orgc = 1.0 - (0.25 * orgc) / (orgc + math.exp(3.72 - 2.95 * orgc))
    sn1 = 1.0 - ms / 100.0
    f_hisand = 1.0 - (0.7 * sn1) / (sn1 + math.exp(-5.51 + 22.9 * sn1))
    return float(CONVERSION_K_SI * f_csand * f_cl_si * f_orgc * f_hisand)


def pendiente_nasadem_lote(zip_path: Path, anillo_lon_lat: list[list[float]], lat_centro: float, lon_centro: float) -> dict:
    # lee el archivo HGT de 1 segundo de arco de NASADEM y calcula pendiente en m/m con espaciado métrico UTM
    from pyproj import Transformer

    m_nombre = zip_path.stem.lower().split("_")[-1]
    lat_sur = (1 if m_nombre[0] == "n" else -1) * int(m_nombre[1:3])
    lon_oeste = (1 if m_nombre[3] == "e" else -1) * int(m_nombre[4:7])
    with zipfile.ZipFile(zip_path) as zf:
        hgt_name = next(n for n in zf.namelist() if n.endswith(".hgt"))
        arr = np.frombuffer(zf.read(hgt_name), dtype=">i2").reshape(3601, 3601).astype(float)
    arr[arr <= -32768] = np.nan
    lons = [c[0] for c in anillo_lon_lat]
    lats = [c[1] for c in anillo_lon_lat]
    c_min = int(math.floor((min(lons) - lon_oeste) * 3600)) - 1
    c_max = int(math.ceil((max(lons) - lon_oeste) * 3600)) + 1
    r_min = int(math.floor((lat_sur + 1.0 - max(lats)) * 3600)) - 1
    r_max = int(math.ceil((lat_sur + 1.0 - min(lats)) * 3600)) + 1
    sub = arr[r_min : r_max + 1, c_min : c_max + 1]
    zona = int((lon_centro + 180.0) // 6) + 1
    epsg_utm = (32600 if lat_centro >= 0 else 32700) + zona
    tr = Transformer.from_crs(4326, epsg_utm, always_xy=True)
    ddeg = 1.0 / 3600.0
    x0, y0 = tr.transform(lon_centro, lat_centro)
    x1, _ = tr.transform(lon_centro + ddeg, lat_centro)
    _, y1 = tr.transform(lon_centro, lat_centro + ddeg)
    dx_m = abs(x1 - x0)
    dy_m = abs(y1 - y0)
    dz_dy, dz_dx = np.gradient(sub, dy_m, dx_m)
    pend = np.sqrt(dz_dx**2 + dz_dy**2)[1:-1, 1:-1]
    elev = sub[1:-1, 1:-1]
    r_c = int(round((lat_sur + 1.0 - lat_centro) * 3600))
    c_c = int(round((lon_centro - lon_oeste) * 3600))
    dz_dy_c = (arr[r_c + 1, c_c] - arr[r_c - 1, c_c]) / (2.0 * dy_m)
    dz_dx_c = (arr[r_c, c_c + 1] - arr[r_c, c_c - 1]) / (2.0 * dx_m)
    pend_centro_manual = math.sqrt(dz_dx_c**2 + dz_dy_c**2)
    return dict(
        producto="NASADEM_HGT v001 (1 arc-sec, ~30 m)",
        crs_metrico=f"EPSG:{epsg_utm}",
        dx_m=round(dx_m, 4),
        dy_m=round(dy_m, 4),
        n_pixeles=int(elev.size),
        elevacion_centro_m=float(arr[r_c, c_c]),
        elevacion_media_m=float(np.nanmean(elev)),
        elevacion_p10_p50_p90_m=[
            float(np.nanpercentile(elev, 10)),
            float(np.nanpercentile(elev, 50)),
            float(np.nanpercentile(elev, 90)),
        ],
        pendiente_media_m_m=float(np.nanmean(pend)),
        pendiente_p10_p50_p90_m_m=[
            float(np.nanpercentile(pend, 10)),
            float(np.nanpercentile(pend, 50)),
            float(np.nanpercentile(pend, 90)),
        ],
        fraccion_pendiente_alta_ge_0p09=float(np.nanmean(pend >= 0.09)),
        pendiente_centro_m_m=float(pend_centro_manual),
    )


def _metricas_con_mascara(p_val: np.ndarray, es_tormenta: np.ndarray, d_mask: np.ndarray, s_factor: float, k_erod: float, anios: float) -> dict:
    # calcula tormentas, lámina e índice para un vector de fracción de suelo desnudo d_mask en [0, 1]
    d = np.clip(np.asarray(d_mask, dtype=float), 0.0, 1.0)
    dias_desnudos = float(np.sum(d))
    n_torm = float(np.sum(es_tormenta * d))
    lluvia_torm = float(np.sum(p_val * es_tormenta * d))
    lluvia_torm_anio = lluvia_torm / anios
    indice = lluvia_torm_anio * s_factor * float(k_erod)
    return dict(
        dias_desnudos=dias_desnudos,
        dias_desnudos_anio=dias_desnudos / anios,
        n_tormentas=n_torm,
        n_tormentas_anio=n_torm / anios,
        lluvia_mm=lluvia_torm,
        lluvia_mm_anio=lluvia_torm_anio,
        indice=indice,
    )


def exposicion_erosiva(
    precip_mm_dia,
    fechas,
    desnudo=None,
    *,
    cobertura_v=None,
    desnudo_cota_baja=None,
    desnudo_cota_alta=None,
    pendiente_m_m: float = 0.05,
    k_erodabilidad: float = 0.03,
    umbrales_p90: dict[int, float] | None = None,
    fecha_corte: str | None = None,
) -> dict:
    # calcula el índice de exposición erosiva (combinación propia) y sus componentes explicables por separado
    p = np.asarray(precip_mm_dia, dtype=float)
    f = pd.to_datetime(fechas)
    if len(p) != len(f):
        raise ValueError("precip_mm_dia y fechas deben tener la misma longitud")
    if desnudo is None:
        if cobertura_v is not None:
            desnudo = 1.0 - np.clip(np.asarray(cobertura_v, dtype=float), 0.0, 1.0)
        else:
            desnudo = np.ones(len(p), dtype=float)
    d_central = np.clip(np.asarray(desnudo, dtype=float), 0.0, 1.0)
    d_baja = d_central if desnudo_cota_baja is None else np.clip(np.asarray(desnudo_cota_baja, dtype=float), 0.0, 1.0)
    d_alta = d_central if desnudo_cota_alta is None else np.clip(np.asarray(desnudo_cota_alta, dtype=float), 0.0, 1.0)
    if np.any(d_baja > d_alta + 1e-12) or np.any(d_baja > d_central + 1e-12) or np.any(d_central > d_alta + 1e-12):
        raise ValueError("cota_baja de suelo desnudo no puede superar el valor central ni la cota_alta")
    if umbrales_p90 is None:
        umbrales_p90 = umbral_p90_semanal(p, f, fecha_corte=fecha_corte)
    sem = semana_del_anio(f)
    umb_dia = np.array([umbrales_p90.get(int(w), float("nan")) for w in sem], dtype=float)
    valido = np.isfinite(p) & np.isfinite(umb_dia)
    if not np.any(valido):
        raise ValueError("sin días válidos para evaluar exposición erosiva")
    p_val = p[valido]
    umb_val = umb_dia[valido]
    es_tormenta = (p_val >= np.maximum(umb_val, UMBRAL_TORMENTA_MIN_MM)) & (p_val > 0.0)
    anios = max(float(np.sum(valido)) / 365.25, 1.0 / 365.25)
    s_factor = factor_pendiente_mccool(pendiente_m_m)
    k_val = float(k_erodabilidad)
    if k_val < 0.0:
        raise ValueError("k_erodabilidad no puede ser negativa")
    m_cen = _metricas_con_mascara(p_val, es_tormenta, d_central[valido], s_factor, k_val, anios)
    m_lo = _metricas_con_mascara(p_val, es_tormenta, d_baja[valido], s_factor, k_val, anios)
    m_hi = _metricas_con_mascara(p_val, es_tormenta, d_alta[valido], s_factor, k_val, anios)
    return dict(
        indice_exposicion_erosiva=m_cen["indice"],
        rango_indice=[m_lo["indice"], m_hi["indice"]],
        rotulo="combinacion_propia",
        etiqueta="INFERENCIA",
        formula=" (lluvia_tormentas_suelo_desnudo_mm / anios) * S_McCool1987(pendiente_m_m) * K_Williams1995 ",
        n_tormentas_suelo_desnudo=m_cen["n_tormentas"],
        n_tormentas_suelo_desnudo_anio=m_cen["n_tormentas_anio"],
        rango_n_tormentas_suelo_desnudo=[m_lo["n_tormentas"], m_hi["n_tormentas"]],
        lluvia_tormentas_suelo_desnudo_mm=m_cen["lluvia_mm"],
        lluvia_tormentas_suelo_desnudo_mm_anio=m_cen["lluvia_mm_anio"],
        rango_lluvia_tormentas_mm_anio=[m_lo["lluvia_mm_anio"], m_hi["lluvia_mm_anio"]],
        dias_desnudos_totales=dict(
            valor=m_cen["dias_desnudos"],
            cota_baja=m_lo["dias_desnudos"],
            cota_alta=m_hi["dias_desnudos"],
        ),
        dias_desnudos_anio=dict(
            valor=m_cen["dias_desnudos_anio"],
            cota_baja=m_lo["dias_desnudos_anio"],
            cota_alta=m_hi["dias_desnudos_anio"],
        ),
        pendiente_m_m=float(pendiente_m_m),
        factor_pendiente_s=s_factor,
        k_erodabilidad=k_val,
        umbrales_p90_semanal_mm_dia={int(k): float(v) for k, v in umbrales_p90.items()},
        anios_evaluados=anios,
    )


def resumir_lotes_demo(raiz_procesados: Path, raiz_crudos: Path, ruta_lotes_json: Path) -> dict:
    # calcula umbrales P90 semanales, pendiente NASADEM, K de Williams y exposición erosiva de ambos lotes DEMO
    from lotes_demo.forzantes import leer_power_csv
    from lotes_demo.suelo import media_ponderada

    lotes_info = {x["lote_id"]: x for x in json.loads(ruta_lotes_json.read_text(encoding="utf-8"))["lotes"]}
    tiles_nasadem = {
        "DEMO-USA-01": raiz_crudos / "nasadem" / "NASADEM_HGT_n41w097.zip",
        "DEMO-COL-01": raiz_crudos / "nasadem" / "NASADEM_HGT_n00w078.zip",
    }
    salida = {"version": 1, "rotulo": "combinacion_propia", "lotes": {}}
    for lote_id in ("DEMO-USA-01", "DEMO-COL-01"):
        info = lotes_info[lote_id]
        # D-033f: POWER es la base de la lluvia de los lotes; IMERG va solo como sensibilidad rotulada
        pw = leer_power_csv(raiz_procesados / lote_id / "power_diario.csv")
        f_pw = pd.to_datetime([f"{int(y)}-{int(d)}" for y, d in zip(pw["YEAR"], pw["DOY"])], format="%Y-%j")
        p_pw = np.asarray(pw["PRECTOTCORR"], dtype=float)
        im = pd.read_csv(raiz_procesados / lote_id / "imerg_diario.csv", parse_dates=["FECHA_UTC"])
        rest = json.loads((raiz_procesados / lote_id / "soilgrids_rest.json").read_text(encoding="utf-8"))
        capas = {c["name"]: c for c in rest["properties"]["layers"]}
        arena_30 = media_ponderada(capas["sand"], "mean", 30) * 0.001
        limo_30 = media_ponderada(capas["silt"], "mean", 30) * 0.001
        arcilla_30 = media_ponderada(capas["clay"], "mean", 30) * 0.001
        soc_30 = media_ponderada(capas["soc"], "mean", 30) * 0.1
        k_williams = factor_erodabilidad_williams(arena_30, limo_30, arcilla_30, soc_30)
        relieve = pendiente_nasadem_lote(
            tiles_nasadem[lote_id],
            info["geometria"]["coordinates"][0],
            info["lat"],
            info["lon"],
        )
        pot = exposicion_erosiva(
            p_pw,
            f_pw,
            desnudo=np.ones(len(p_pw)),
            pendiente_m_m=relieve["pendiente_media_m_m"],
            k_erodabilidad=k_williams,
        )
        p_im = im["IMERG_PRECIP_MM_DIA"].to_numpy(dtype=float)
        sens_imerg = exposicion_erosiva(
            p_im,
            pd.to_datetime(im["FECHA_UTC"]),
            desnudo=np.ones(len(p_im)),
            pendiente_m_m=relieve["pendiente_media_m_m"],
            k_erodabilidad=k_williams,
        )
        salida["lotes"][lote_id] = dict(
            lote_id=lote_id,
            periodo=[str(f_pw.min())[:10], str(f_pw.max())[:10]],
            fuente_lluvia="NASA POWER diario (PRECTOTCORR), base de los lotes (D-033f)",
            relieve_nasadem_30m=relieve,
            erodabilidad_k_williams_0_30cm=dict(
                valor=round(k_williams, 6),
                unidad="t*ha*h/(ha*MJ*mm)",
                etiqueta="INFERENCIA",
                fuente="Williams (1995) EPIC / Sharpley y Williams (1990, USDA TB-1768) con conversión SI 0,1317 de Foster et al. (1981), sobre SoilGrids 2.0 0-30 cm",
                insumos_0_30cm=dict(
                    arena_kg_kg=round(arena_30, 4),
                    limo_kg_kg=round(limo_30, 4),
                    arcilla_kg_kg=round(arcilla_30, 4),
                    soc_g_kg=round(soc_30, 2),
                ),
            ),
            exposicion_potencial_suelo_desnudo_100pct=pot,
            sensibilidad_imerg=dict(
                rotulo="sensibilidad a la fuente de lluvia: IMERG Final V07 diario, día UTC; sobrestima frente a la estación en Ipiales (comparacion_power_imerg.json)",
                exposicion_potencial_suelo_desnudo_100pct=sens_imerg,
            ),
            # PENDIENTE: la exposición con suelo desnudo real necesita el reloj de suelo desnudo de T-D6 (cota con cobertura en los huecos).
            # La visibilidad HLS no es suelo desnudo, así que ya no se usa como cota (director, 20:50).
            exposicion_con_suelo_desnudo_real="PENDIENTE",
        )
    return salida


if __name__ == "__main__":
    raiz_proc = Path(sys.argv[1])
    raiz_crud = Path(sys.argv[2])
    ruta_lotes = Path(sys.argv[3])
    ruta_out = Path(sys.argv[4])
    res = resumir_lotes_demo(raiz_proc, raiz_crud, ruta_lotes)
    ruta_out.write_text(json.dumps(res, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
