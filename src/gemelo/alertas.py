# asistido por SI: Claude Code (Opus 5.5), alerta de helada en etapa sensible (D-032) y climatología de estación
"""Alerta de helada en etapa sensible (D-032, contrato v1.1 §9): la única alerta de la v1.1.

No es un pronóstico. Dos métodos, según lo que permitan los datos:
- serie_power: cuenta, en las ventanas de clima real del escenario, las temporadas de cultivos cosechados en que la
  mínima diaria bajó del umbral en etapa sensible. Usa T2M_MIN_CORR (corregida por altura de Datos) si existe.
  Rango: la cota alta resta a la mínima la cota superior del IC95 del sesgo cálido medido contra la estación.
- climatologia_estacion (combinación propia): si la serie nunca baja del umbral y hay una estación cercana con dato
  (distancia y desnivel máximos en el YAML), la frecuencia mensual de heladas observada en la estación se cruza con
  las etapas sensibles de cada estrategia. Rango: intervalo de Wilson al 95 % de cada frecuencia mensual.
Umbral: el del catálogo de cultivos (`t_helada`) cuando tiene fuente; si no, 0 °C SUPUESTO.
"""
import json
import math
from pathlib import Path

import numpy as np
import pandas as pd

from gemelo.clima import MES_DE_DIA
from gemelo.incertidumbre import resumir
from gemelo.parametros import cargar_catalogo

UMBRAL_C = 0.0  # SUPUESTO: helada a 2 m con mínima <= 0 °C para cultivos sin tolerancia con fuente en el catálogo
ETAPA_SENSIBLE = "desarrollo_y_mediados"  # SUPUESTO: etapas des y med de FAO-56 (follaje y floración)
Z95 = 1.959964


def leer_validacion(ruta: str | Path, serie: str) -> dict:
    """Sesgo de la mínima de POWER frente a la estación, tomado del JSON de Datos (nunca a mano)."""
    v = json.loads(Path(ruta).read_text(encoding="utf-8"))
    comp = v["comparaciones"]["T2M_MIN_vs_TMIN"]
    prefijo = "corregida_lote" if serie == "t2m_min_corr" else "cruda"
    clave = next(k for k in comp if k.startswith(prefijo))
    c = comp[clave]
    ext = v.get("analisis_extremos_frios_tmin", {})
    return {"estacion": v["estacion_ghcn"]["estacion_id"], "comparacion": clave, "periodo": v["periodo"],
            "elevacion_lote_m": v.get("elevaciones_m", {}).get("lote_srtm"),
            "n_dias": c["n_dias_validos"], "sesgo_c": c["sesgo_c"], "sesgo_c_ic95": c["sesgo_c_ic95_bootstrap_anual"],
            "mae_c": c["mae_c"], "estacion_dias_le_0c": ext.get("ghcn_dias_le_0c"),
            "estacion_tmin_min_c": ext.get("ghcn_tmin_min_c"),
            "power_tmin_min_c": next((x for k, x in ext.items() if k.startswith("power_corr") and k.endswith("min_c")),
                                     None) if serie == "t2m_min_corr" else ext.get("power_cruda_min_c"),
            "fuente": Path(ruta).name, "etiqueta": "VERIFICADO" if c.get("n_dias_validos") else "FUENTE"}


def umbrales_cultivo(cultivos, umbral_defecto: float = UMBRAL_C) -> dict[str, dict]:
    """{cultivo: {valor, etiqueta, referencia}}: `t_helada` del catálogo si tiene fuente; si no, el SUPUESTO."""
    cat = cargar_catalogo()
    out = {}
    for c in sorted(set(cultivos)):
        p = cat[c].parametros.get("t_helada") if c in cat else None
        if p is not None and p.disponible and p.etiqueta != "SUPUESTO":
            out[c] = {"valor": float(p.valor), "etiqueta": p.etiqueta, "referencia": p.referencia}
        else:
            out[c] = {"valor": umbral_defecto, "etiqueta": "SUPUESTO", "referencia": None}
    return out


def mascara_sensible(programa) -> np.ndarray:
    """(T,) True en las etapas des y med de cada temporada que se cosecha."""
    sens = np.zeros(programa.T, bool)
    for k, (l1, l2, l3, _) in enumerate(programa.duraciones):
        if programa.estrategia.temporadas[k].cosechar:
            sens |= (programa.temporada == k) & (programa.dds >= l1) & (programa.dds < l1 + l2 + l3)
    return sens


def _umbral_diario(programa, umbrales: dict) -> np.ndarray:
    """(T,) umbral del cultivo de cada día (inf en barbecho)."""
    u = np.full(programa.T, np.inf)
    for k, t in enumerate(programa.estrategia.temporadas):
        u[programa.temporada == k] = umbrales[t.cultivo]["valor"]
    return u


def _distancia_km(lat1, lon1, lat2, lon2) -> float:
    f1, f2 = math.radians(lat1), math.radians(lat2)
    a = math.sin((f2 - f1) / 2) ** 2 + math.cos(f1) * math.cos(f2) * math.sin(math.radians(lon2 - lon1) / 2) ** 2
    return 2 * 6371.0 * math.asin(math.sqrt(a))


def _wilson(k: int, n: int) -> tuple[float, float]:
    if n == 0:
        return 0.0, 1.0
    p = k / n
    c = (p + Z95 ** 2 / (2 * n)) / (1 + Z95 ** 2 / n)
    h = Z95 * math.sqrt(p * (1 - p) / n + Z95 ** 2 / (4 * n * n)) / (1 + Z95 ** 2 / n)
    return max(c - h, 0.0), min(c + h, 1.0)


def leer_estacion(ruta: str | Path, periodo: list[str]) -> dict:
    """TMIN diaria de un CSV de acceso GHCN-Daily (décimas de °C). Se descartan los días con bandera de calidad."""
    df = pd.read_csv(Path(ruta), usecols=["STATION", "DATE", "LATITUDE", "LONGITUDE", "ELEVATION", "TMIN",
                                          "TMIN_ATTRIBUTES"], dtype={"TMIN_ATTRIBUTES": str})
    meta = df.iloc[0]
    df["DATE"] = pd.to_datetime(df["DATE"])
    df = df[(df.DATE >= periodo[0]) & (df.DATE <= periodo[1])]
    q = df.TMIN_ATTRIBUTES.fillna(",,").str.split(",").str[1].str.strip()
    rechazados = int((df.TMIN.notna() & (q != "")).sum())
    df = df[df.TMIN.notna() & (q == "")]
    return {"estacion": str(meta.STATION), "lat": float(meta.LATITUDE), "lon": float(meta.LONGITUDE),
            "elevacion_m": float(meta.ELEVATION), "periodo": list(periodo), "rechazados_bandera": rechazados,
            "fechas": df.DATE, "tmin_c": df.TMIN.to_numpy(float) / 10.0, "fuente": Path(ruta).name}


def climatologia_mensual(est: dict, umbral_c: float) -> list[dict]:
    """Por mes: días del periodo, días con dato, días con TMIN <= umbral, frecuencia, IC de Wilson y cobertura."""
    todos = pd.date_range(est["periodo"][0], est["periodo"][1], freq="D")
    meses = est["fechas"].dt.month.to_numpy()
    filas = []
    for m in range(1, 13):
        n = int((meses == m).sum())
        k = int(((meses == m) & (est["tmin_c"] <= umbral_c)).sum())
        lo, hi = _wilson(k, n)
        filas.append({"mes": m, "dias_periodo": int((todos.month == m).sum()), "dias_con_dato": n, "dias_helada": k,
                      "frecuencia": k / n if n else None, "frecuencia_ic95": [lo, hi],
                      "cobertura": n / int((todos.month == m).sum())})
    return filas


def _por_climatologia(programa, sens, umbrales, clim_por_umbral) -> dict:
    """Días de helada esperados por temporada y probabilidad de al menos uno, desde la frecuencia mensual."""
    cosechadas = [k for k, t in enumerate(programa.estrategia.temporadas) if t.cosechar]
    esperados, prob, meses = [], [], set()
    for k in cosechadas:
        dias = np.where(sens & (programa.temporada == k))[0]
        clim = clim_por_umbral[umbrales[programa.estrategia.temporadas[k].cultivo]["valor"]]
        cols = [[f["frecuencia"] or 0.0, *f["frecuencia_ic95"]] for f in clim]
        p = np.array([cols[MES_DE_DIA[d % 365]] for d in dias]).reshape(-1, 3)    # (días, [valor, lo, hi])
        esperados.append(p.sum(axis=0))
        prob.append(1 - np.prod(1 - p, axis=0))
        meses |= {MES_DE_DIA[d % 365] + 1 for d in dias if clim[MES_DE_DIA[d % 365]]["dias_helada"] > 0}
    e, q = np.mean(esperados, axis=0), np.mean(prob, axis=0)
    return {"dias_helada_esperados_temporada": {"valor": float(e[0]), "cota_baja": float(e[1]), "cota_alta": float(e[2])},
            "probabilidad_al_menos_una_temporada": {"valor": float(q[0]), "cota_baja": float(q[1]),
                                                    "cota_alta": float(q[2]),
                                                    "etiqueta": "INFERENCIA (días independientes; probablemente sobrestimada)"},
            "meses_sensibles_con_helada_observada": sorted(meses)}


def helada_etapa_sensible(clima, escenario, programas, umbral_c: float = UMBRAL_C, provisional: bool = False,
                          validacion: dict | None = None, estacion: dict | None = None,
                          max_km: float = 5.0, max_dz_m: float = 100.0, lote=None) -> dict:
    serie = "t2m_min_corr" if "t2m_min_corr" in clima.datos else "t2m_min"
    idx = np.array(escenario.miembros)
    K, H = idx.shape
    tmin = clima.datos[serie][idx].reshape(K, H * 365) + escenario.delta_temp_c
    margen = max(float(validacion["sesgo_c_ic95"][1]), 0.0) if validacion else 0.0
    umbrales = umbrales_cultivo([t.cultivo for p in programas for t in p.estrategia.temporadas], umbral_c)
    # La serie no resuelve heladas si nunca baja del umbral y la estación sí registró días <= 0 °C
    no_resuelve = bool(validacion and umbral_c >= 0 and validacion["estacion_dias_le_0c"]
                       and validacion["power_tmin_min_c"] is not None and validacion["power_tmin_min_c"] > umbral_c)
    # Estación cercana: distancia al lote y desnivel con la altura del lote declarada por Datos
    est_info, clim_por_umbral = None, {}
    if estacion is not None and lote is not None:
        d_km = _distancia_km(lote.lat, lote.lon, estacion["lat"], estacion["lon"])
        z_lote = (validacion or {}).get("elevacion_lote_m")
        dz = abs(estacion["elevacion_m"] - z_lote) if z_lote is not None else None
        cercana = d_km <= max_km and dz is not None and dz <= max_dz_m
        est_info = {"estacion": estacion["estacion"], "fuente": estacion["fuente"], "distancia_km": round(d_km, 2),
                    "desnivel_m": None if dz is None else round(dz, 1), "max_km": max_km, "max_desnivel_m": max_dz_m,
                    "cercana": cercana, "periodo": estacion["periodo"],
                    "rechazados_bandera": estacion["rechazados_bandera"]}
        if cercana:
            for u in {x["valor"] for x in umbrales.values()}:
                clim_por_umbral[u] = climatologia_mensual(estacion, u)
            est_info["climatologia_mensual"] = clim_por_umbral[umbral_c] if umbral_c in clim_por_umbral \
                else next(iter(clim_por_umbral.values()))
    usa_estacion = no_resuelve and bool(clim_por_umbral)
    estrategias = {}
    for p in programas:
        sens = mascara_sensible(p)
        u = _umbral_diario(p, umbrales)
        cosechadas = [k for k, t in enumerate(p.estrategia.temporadas) if t.cosechar]
        if not cosechadas:
            continue
        frac = []
        for m in (0.0, margen):
            helada = (tmin - m <= u) & sens
            con = [helada[:, p.temporada == k].any(axis=1) for k in cosechadas]   # (n_temp, K)
            frac.append(float(np.mean(con)))
        dias = ((tmin <= u) & sens).sum(axis=1) / H
        t_sens = np.where(sens, tmin, np.inf).min(axis=1)
        fila = {"fraccion_temporadas_con_helada": {"valor": frac[0], "cota_baja": frac[0], "cota_alta": frac[1]},
                "dias_helada_etapa_sensible_anio": resumir(dias), "tmin_minima_etapa_sensible_c": resumir(t_sens),
                "n_temporadas": len(cosechadas) * K,
                "umbrales": {t.cultivo: umbrales[t.cultivo] for t in p.estrategia.temporadas if t.cosechar}}
        if usa_estacion:
            c = _por_climatologia(p, sens, umbrales, clim_por_umbral)
            e = c["dias_helada_esperados_temporada"]
            estado = "activa" if e["valor"] > 0 else "sin_alerta"
            fila.update(c, estado=estado, clave=f"alert.frost.station_{estado}", parametros={
                "dias": round(e["valor"], 2), "dias_lo": round(e["cota_baja"], 2), "dias_hi": round(e["cota_alta"], 2),
                "prob": round(c["probabilidad_al_menos_una_temporada"]["valor"], 3),
                "meses": ", ".join(str(x) for x in c["meses_sensibles_con_helada_observada"]) or "-"})
        else:
            estado = "activa" if frac[0] > 0 else "vigilancia" if frac[1] > 0 or no_resuelve else "sin_alerta"
            fila.update(estado=estado,
                        clave="alert.frost.unresolved" if estado == "vigilancia" and frac[1] == 0
                        else f"alert.frost.{estado}",
                        parametros={"umbral": umbral_c, "fraccion": round(frac[0], 3),
                                    "fraccion_alta": round(frac[1], 3),
                                    "tmin_p10": round(float(np.percentile(t_sens, 10)), 2)})
        estrategias[p.estrategia.id] = fila
    avisos = []
    if usa_estacion:
        clim = est_info["climatologia_mensual"]
        n_dato, n_per = sum(f["dias_con_dato"] for f in clim), sum(f["dias_periodo"] for f in clim)
        avisos.append({"clave": "alert.frost.station_climatology", "parametros": {
            "estacion": est_info["estacion"], "km": est_info["distancia_km"], "dz": est_info["desnivel_m"],
            "dias": sum(f["dias_helada"] for f in clim), "umbral": umbral_c, "dias_dato": n_dato,
            "cobertura": n_dato / n_per, "desde": est_info["periodo"][0][:4], "hasta": est_info["periodo"][1][:4]}})
    if validacion and validacion["sesgo_c"] > 0:
        avisos.append({"clave": "alert.frost.warm_bias", "parametros": {
            "estacion": validacion["estacion"], "sesgo": validacion["sesgo_c"],
            "lo": validacion["sesgo_c_ic95"][0], "hi": validacion["sesgo_c_ic95"][1],
            "dias_estacion": validacion["estacion_dias_le_0c"], "tmin_estacion": validacion["estacion_tmin_min_c"],
            "tmin_power": validacion["power_tmin_min_c"]}})
    if provisional:
        avisos.append({"clave": "alert.frost.provisional", "parametros": {}})
    supuestos = sorted(c for c, x in umbrales.items() if x["etiqueta"] == "SUPUESTO")
    return {"clave_nombre": "alert.frost.name", "provisional": provisional, "naturaleza": "simulado",
            "es_pronostico": False, "metodo": "climatologia_estacion" if usa_estacion else "serie_power",
            "metodo_etiqueta": "combinacion_propia" if usa_estacion else "INFERENCIA",
            "serie_temperatura": serie.upper(), "umbral_c": umbral_c, "umbral_etiqueta": "SUPUESTO",
            "umbrales_cultivo": umbrales, "cultivos_umbral_supuesto": supuestos,
            "etapa_sensible": ETAPA_SENSIBLE, "etapa_etiqueta": "SUPUESTO", "margen_sesgo_c": margen,
            "serie_no_resuelve_heladas": no_resuelve, "validacion": validacion, "estacion_cercana": est_info,
            "avisos": avisos, "estrategias": estrategias}


def bloque(entrada, programas) -> dict:
    """Bloque `alertas` del documento. Las otras dos alertas de T-G5 quedan fuera de la v1.1 (D-032)."""
    cfg = (entrada.alertas or {}).get("helada", {})
    serie = "t2m_min_corr" if "t2m_min_corr" in entrada.clima.datos else "t2m_min"
    val = leer_validacion(cfg["validacion"], serie) if cfg.get("validacion") else None
    est = leer_estacion(cfg["estacion"], val["periodo"] if val else cfg["periodo_estacion"]) \
        if cfg.get("estacion") else None
    return {"helada_etapa_sensible": helada_etapa_sensible(
                entrada.clima, entrada.escenario, programas, float(cfg.get("umbral_c", UMBRAL_C)),
                bool(cfg.get("provisional", False)), val, est, float(cfg.get("estacion_max_km", 5.0)),
                float(cfg.get("estacion_max_desnivel_m", 100.0)), entrada.lote),
            "nota_alcance": "D-032: las otras dos alertas de T-G5 quedan fuera de la v1.1"}
