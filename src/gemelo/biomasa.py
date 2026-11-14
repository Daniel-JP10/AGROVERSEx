# asistido por SI: Cursor (agente), escritura y revisión de código; núcleo del gemelo digital en el hackatón
"""Biomasa aérea B(t) por eficiencia de uso de la radiación (Monteith, 1977).

dB/dt = 10 * RUE * fi * Rs * f_T(T) * min(Ks, f_N)      [kg MS/ha/día]
RUE en g MS/MJ de radiación solar interceptada; Rs en MJ/m²/día; 1 g/m² = 10 kg/ha.
fi (fracción interceptada) se aproxima con la cobertura verde V (INFERENCIA).

Se eligió RUE en lugar de la logística dB/dt = rB(1 - B/K)g de la especificación: la logística necesita una
capacidad K sin fuente por cultivo y lugar, mientras que RUE tiene valores de literatura y responde a la
radiación medida. logistica() queda como variante para comparar.
"""
import numpy as np


def f_temperatura(t, t_base, t_opt, t_max):
    """Función beta de temperatura (Yan y Hunt, 1999): 0 fuera de (t_base, t_max), 1 en t_opt."""
    t = np.asarray(t, float)
    dentro = (t > t_base) & (t < t_max)
    a = (t_opt - t_base) / np.maximum(t_max - t_opt, 1e-6)
    x = np.where(dentro, (t_max - t) / np.maximum(t_max - t_opt, 1e-6), 0.0)
    y = np.where(dentro, (t - t_base) / np.maximum(t_opt - t_base, 1e-6), 0.0)
    return np.where(dentro, x * np.power(np.maximum(y, 0), a), 0.0)


def crecimiento(rue, cobertura, rs, f_t, g=1.0):
    """Incremento diario de biomasa aérea, kg MS/ha."""
    return 10.0 * rue * np.clip(cobertura, 0, 1) * np.maximum(rs, 0) * f_t * g


def cosecha(b, n_planta, indice_cosecha, indice_cosecha_n, exporta):
    """Reparte la biomasa a la cosecha: (rendimiento, residuo, N exportado, N del residuo). Conserva masa."""
    rend = np.where(exporta, indice_cosecha * b, 0.0)
    n_exp = np.where(exporta, indice_cosecha_n * n_planta, 0.0)
    return rend, b - rend, n_exp, n_planta - n_exp


def logistica(b, r, k, g):
    """Variante conceptual de la especificación: dB/dt = r B (1 - B/K) g. No se usa en el motor."""
    return r * b * (1 - b / k) * g
