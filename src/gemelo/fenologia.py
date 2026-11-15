# asistido por SI: Cursor (agente), escritura y revisión de código; núcleo del gemelo digital en el hackatón
"""Fenología por etapas de FAO-56 (ini, des, med, fin en días) y curva de Kc (FAO-56 ec. 66, cap. 6).

La curva se expresa como pesos lineales sobre (Kc_ini, Kc_mid, Kc_end), así el mismo calendario sirve para cada
miembro del ensamble aunque sus Kc difieran: Kc(t) = w_ini Kc_ini + w_mid Kc_mid + w_end Kc_end.
"""
import numpy as np

from gemelo.parametros import Cultivo, leer_etapas
from gemelo.procedencia import ParametroPendiente


def duraciones(cultivo: Cultivo, etapas=None, variante: str | None = None) -> tuple[int, int, int, int]:
    if etapas is not None:
        e = tuple(int(x) for x in etapas)
    elif variante is not None:
        e = leer_etapas(cultivo.etapas_referencia, variante)
    else:
        e = cultivo.etapas
    if e is None:
        raise ParametroPendiente(f"{cultivo.nombre}: etapas PENDIENTE (FAO-56 no las da); indique etapas del lugar")
    if len(e) != 4 or min(e) < 1:
        raise ValueError(f"{cultivo.nombre}: etapas inválidas {e}")
    return e


def pesos_kc(dds: np.ndarray, etapas) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Pesos de Kc_ini, Kc_mid y Kc_end para días desde la siembra dds (0 = día de siembra)."""
    l1, l2, l3, l4 = etapas
    d = np.asarray(dds, float)
    a = np.clip((d - l1 + 1) / l2, 0, 1)                    # avance en desarrollo
    b = np.clip((d - (l1 + l2 + l3) + 1) / l4, 0, 1)        # avance en etapa final
    w_ini = np.where(d < l1, 1.0, np.where(d < l1 + l2, 1 - a, 0.0))
    w_mid = np.where(d < l1, 0.0, np.where(d < l1 + l2, a, 1 - b))
    w_end = np.where(d < l1 + l2 + l3, 0.0, b)
    return w_ini, w_mid, w_end


def fraccion_raiz(dds: np.ndarray, etapas) -> np.ndarray:
    """Avance de la profundidad radicular: lineal desde la siembra hasta el inicio de mediados de temporada.

    INFERENCIA: FAO-56 cap. 8 da Zr inicial y máxima; el crecimiento lineal en el tiempo es una simplificación.
    """
    l1, l2, _, _ = etapas
    return np.clip(np.asarray(dds, float) / (l1 + l2), 0, 1)


def cobertura_potencial(kc, kc_min, kc_max, altura_m):
    """Fracción de suelo cubierta por vegetación (FAO-56 ec. 76) aplicada con el Kc único.

    INFERENCIA: FAO-56 la define con Kcb; con Kc único la cobertura de la etapa inicial puede quedar sobreestimada
    en suelo húmedo.
    """
    x = np.clip((np.asarray(kc) - kc_min) / np.maximum(kc_max - kc_min, 1e-6), 0, 1)
    return x ** (1 + 0.5 * np.asarray(altura_m))
