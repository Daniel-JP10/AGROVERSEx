# asistido por SI: Cursor (agente), escritura y revisión de código; núcleo del gemelo digital en el hackatón
"""Carbono orgánico del suelo C(t) = Y + O con ICBM (Andrén y Kätterer, 1997), t C/ha en 0-30 cm.

dY/dt = i - k1 r Y
dO/dt = h k1 r Y - k2 r O
r = f_T(T) f_W(agua) / f_T(T_norm): factor climático; i = entrada de C del residuo.
El N orgánico acompaña al C: el reservorio joven lleva su propio N (Y_N); el viejo tiene C:N fijo (del suelo).
"""
import numpy as np


def factor_temperatura(t, t_min=-3.8, t_ref=30.0):
    """((T - T_min) / (T_ref - T_min))^2 para T > T_min (ICBM regional, Andrén et al., 2004)."""
    x = np.clip((np.asarray(t, float) - t_min) / (t_ref - t_min), 0, None)
    return x ** 2


def factor_clima(t, fraccion_agua, t_min, t_ref, t_norm):
    """r diario, = 1 a T_norm con suelo a capacidad de campo. f_W lineal en el agua disponible (SUPUESTO)."""
    return factor_temperatura(t, t_min, t_ref) / factor_temperatura(t_norm, t_min, t_ref) * np.clip(fraccion_agua, 0, 1)


def paso_icbm(y, o, y_n, n_min, k1, k2, h, r, cn_viejo, dt=1.0):
    """Un paso explícito de ICBM con N acoplado. k1 y k2 en 1/día.

    Mineralización neta = N liberado del joven - N inmovilizado en el humus + N liberado del viejo.
    Si la inmovilización supera el N mineral disponible, la descomposición del joven se frena (escala s).
    Devuelve (y, o, y_n, n_min, respiración en t C/ha, mineralización neta en kg N/ha).
    """
    dec_y = np.minimum(k1 * r * dt, 1.0) * y
    dec_o = np.minimum(k2 * r * dt, 1.0) * o
    razon_n = np.where(y > 1e-12, y_n / np.maximum(y, 1e-12), 0.0)    # kg N / t C
    n_y = dec_y * razon_n
    hum_n = h * dec_y * 1000.0 / cn_viejo                              # t C -> kg C, / C:N
    n_o = dec_o * 1000.0 / cn_viejo
    neto = n_y - hum_n + n_o
    # Inmovilización mayor que lo disponible: escalar la descomposición del joven
    necesita = hum_n - n_y
    s = np.where((neto < 0) & (necesita > 1e-12), np.clip((n_min + n_o) / np.maximum(necesita, 1e-12), 0, 1), 1.0)
    dec_y, n_y, hum_n = dec_y * s, n_y * s, hum_n * s
    neto = n_y - hum_n + n_o
    hum = h * dec_y
    y = y - dec_y
    o = o + hum - dec_o
    resp = dec_y - hum + dec_o
    return y, o, y_n - n_y, n_min + neto, resp, neto, s


def inicializar(cos_t_ha, frac_joven, cn_suelo):
    """(Y0, O0, Y_N0) repartiendo el COS inicial; el joven arranca con el C:N del suelo (SUPUESTO)."""
    y0 = cos_t_ha * frac_joven
    return y0, cos_t_ha - y0, y0 * 1000.0 / cn_suelo
