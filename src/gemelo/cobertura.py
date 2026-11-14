# asistido por SI: Cursor (agente), escritura y revisión de código; núcleo del gemelo digital en el hackatón
"""Cobertura vegetal V(t), cobertura de residuo y su efecto sobre la ET y la exposición del suelo."""
import numpy as np


def actualizar_cobertura(v, vpot_hoy, vpot_ayer, g):
    """La cobertura sigue a la potencial (FAO-56 ec. 76) pero su expansión se reduce con el estrés g (0-1).

    Expansión: V += max(ΔVpot, 0) * g. Senescencia: V no supera la potencial del día. Una cobertura atrasada por
    estrés no se recupera después (el dosel perdido no se recupera dentro del ciclo): INFERENCIA de la lógica de
    expansión de dosel de AquaCrop, simplificada.
    """
    dv = np.maximum(vpot_hoy - vpot_ayer, 0.0)
    return np.clip(np.minimum(v + dv * g, vpot_hoy), 0.0, 1.0)


def kc_efectivo(kc, v, vpot, kc_min):
    """Kc reducido cuando el dosel real es menor que el potencial: Kc_min + (Kc - Kc_min) V / Vpot (INFERENCIA)."""
    r = np.where(vpot > 1e-3, np.clip(v / np.maximum(vpot, 1e-3), 0, 1), 1.0)
    return kc_min + (kc - kc_min) * r


def kc_suelo_desnudo(kc_max_suelo, f_residuo, reduccion_mulch):
    """Kc de evaporación de suelo desnudo húmedo, reducido por mulch (FAO-56 cap. 11)."""
    return kc_max_suelo * (1.0 - reduccion_mulch * np.clip(f_residuo, 0, 1))


def cobertura_residuo(masa_kg_ha, am):
    """Fracción cubierta por residuo superficial: 1 - exp(-Am M) (forma de Gregory, 1982)."""
    return 1.0 - np.exp(-am * np.maximum(masa_kg_ha, 0.0))


def fraccion_desnuda(v, f_residuo):
    """Fracción del suelo sin vegetación viva ni residuo (coberturas independientes)."""
    return (1.0 - np.clip(v, 0, 1)) * (1.0 - np.clip(f_residuo, 0, 1))
