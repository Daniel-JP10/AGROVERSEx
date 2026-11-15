# asistido por SI: Claude Code (Opus 5.5), alerta de helada en etapa sensible (D-032)
"""Alerta de helada en etapa sensible (D-032, contrato v1.1 §9): la única alerta de la v1.1.

No es un pronóstico: cuenta, en las ventanas de clima real del escenario, en cuántas temporadas de cultivos
cosechados la mínima diaria bajó del umbral durante la etapa sensible. Usa T2M_MIN_CORR (mínima corregida por
altura de Datos) cuando existe, porque la cruda oculta las heladas del altiplano (forzantes_gemelo.md §4.3).

Rango: la cota baja usa la mínima tal cual; la cota alta le resta la cota superior del IC95 del sesgo cálido
medido contra la estación (validación de Datos). Así el número sale con su incertidumbre de entrada.
"""
import json
from pathlib import Path

import numpy as np

from gemelo.incertidumbre import resumir

UMBRAL_C = 0.0  # SUPUESTO: helada a 2 m con mínima <= 0 °C; umbral por cultivo PENDIENTE
ETAPA_SENSIBLE = "desarrollo_y_mediados"  # SUPUESTO: etapas des y med de FAO-56 (follaje y floración)


def leer_validacion(ruta: str | Path, serie: str) -> dict:
    """Sesgo de la mínima de POWER frente a la estación, tomado del JSON de Datos (nunca a mano)."""
    v = json.loads(Path(ruta).read_text(encoding="utf-8"))
    comp = v["comparaciones"]["T2M_MIN_vs_TMIN"]
    prefijo = "corregida_lote" if serie == "t2m_min_corr" else "cruda"
    clave = next(k for k in comp if k.startswith(prefijo))
    c = comp[clave]
    ext = v.get("analisis_extremos_frios_tmin", {})
    return {"estacion": v["estacion_ghcn"]["estacion_id"], "comparacion": clave, "periodo": v["periodo"],
            "n_dias": c["n_dias_validos"], "sesgo_c": c["sesgo_c"], "sesgo_c_ic95": c["sesgo_c_ic95_bootstrap_anual"],
            "mae_c": c["mae_c"], "estacion_dias_le_0c": ext.get("ghcn_dias_le_0c"),
            "estacion_tmin_min_c": ext.get("ghcn_tmin_min_c"),
            "power_tmin_min_c": next((x for k, x in ext.items() if k.startswith("power_corr") and k.endswith("min_c")),
                                     None) if serie == "t2m_min_corr" else ext.get("power_cruda_min_c"),
            "fuente": Path(ruta).name, "etiqueta": "VERIFICADO" if c.get("n_dias_validos") else "FUENTE"}


def mascara_sensible(programa) -> np.ndarray:
    """(T,) True en las etapas des y med de cada temporada que se cosecha."""
    sens = np.zeros(programa.T, bool)
    for k, (l1, l2, l3, _) in enumerate(programa.duraciones):
        if programa.estrategia.temporadas[k].cosechar:
            sens |= (programa.temporada == k) & (programa.dds >= l1) & (programa.dds < l1 + l2 + l3)
    return sens


def helada_etapa_sensible(clima, escenario, programas, umbral_c: float = UMBRAL_C, provisional: bool = False,
                          validacion: dict | None = None) -> dict:
    serie = "t2m_min_corr" if "t2m_min_corr" in clima.datos else "t2m_min"
    idx = np.array(escenario.miembros)
    K, H = idx.shape
    tmin = clima.datos[serie][idx].reshape(K, H * 365) + escenario.delta_temp_c
    margen = max(float(validacion["sesgo_c_ic95"][1]), 0.0) if validacion else 0.0
    # La serie no resuelve heladas si nunca baja del umbral y la estación sí registró días <= 0 °C
    no_resuelve = bool(validacion and umbral_c >= 0 and validacion["estacion_dias_le_0c"]
                       and validacion["power_tmin_min_c"] is not None and validacion["power_tmin_min_c"] > umbral_c)
    estrategias = {}
    for p in programas:
        sens = mascara_sensible(p)
        cosechadas = [k for k, t in enumerate(p.estrategia.temporadas) if t.cosechar]
        if not cosechadas:
            continue
        frac = []
        for m in (0.0, margen):
            helada = (tmin - m <= umbral_c) & sens
            con = [helada[:, p.temporada == k].any(axis=1) for k in cosechadas]   # (n_temp, K)
            frac.append(float(np.mean(con)))
        dias = ((tmin <= umbral_c) & sens).sum(axis=1) / H
        t_sens = np.where(sens, tmin, np.inf).min(axis=1)
        estado = "activa" if frac[0] > 0 else "vigilancia" if frac[1] > 0 or no_resuelve else "sin_alerta"
        clave = "alert.frost.unresolved" if estado == "vigilancia" and frac[1] == 0 else f"alert.frost.{estado}"
        estrategias[p.estrategia.id] = {
            "estado": estado, "clave": clave,
            "parametros": {"umbral": umbral_c, "fraccion": round(frac[0], 3), "fraccion_alta": round(frac[1], 3),
                           "tmin_p10": round(float(np.percentile(t_sens, 10)), 2)},
            "fraccion_temporadas_con_helada": {"valor": frac[0], "cota_baja": frac[0], "cota_alta": frac[1]},
            "dias_helada_etapa_sensible_anio": resumir(dias),
            "tmin_minima_etapa_sensible_c": resumir(t_sens),
            "n_temporadas": len(cosechadas) * K}
    avisos = []
    if validacion and validacion["sesgo_c"] > 0:
        avisos.append({"clave": "alert.frost.warm_bias", "parametros": {
            "estacion": validacion["estacion"], "sesgo": validacion["sesgo_c"],
            "lo": validacion["sesgo_c_ic95"][0], "hi": validacion["sesgo_c_ic95"][1],
            "dias_estacion": validacion["estacion_dias_le_0c"], "tmin_estacion": validacion["estacion_tmin_min_c"],
            "tmin_power": validacion["power_tmin_min_c"]}})
    if provisional:
        avisos.append({"clave": "alert.frost.provisional", "parametros": {}})
    return {"clave_nombre": "alert.frost.name", "provisional": provisional, "naturaleza": "simulado",
            "es_pronostico": False, "serie_temperatura": serie.upper(),
            "umbral_c": umbral_c, "umbral_etiqueta": "SUPUESTO", "etapa_sensible": ETAPA_SENSIBLE,
            "etapa_etiqueta": "SUPUESTO", "margen_sesgo_c": margen, "serie_no_resuelve_heladas": no_resuelve, "validacion": validacion,
            "avisos": avisos, "estrategias": estrategias}


def bloque(entrada, programas) -> dict:
    """Bloque `alertas` del documento. Las otras dos alertas de T-G5 quedan fuera de la v1.1 (D-032)."""
    cfg = (entrada.alertas or {}).get("helada", {})
    serie = "t2m_min_corr" if "t2m_min_corr" in entrada.clima.datos else "t2m_min"
    val = leer_validacion(cfg["validacion"], serie) if cfg.get("validacion") else None
    return {"helada_etapa_sensible": helada_etapa_sensible(
                entrada.clima, entrada.escenario, programas, float(cfg.get("umbral_c", UMBRAL_C)),
                bool(cfg.get("provisional", False)), val),
            "nota_alcance": "D-032: las otras dos alertas de T-G5 quedan fuera de la v1.1"}
