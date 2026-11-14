# asistido por SI: Claude Code (Anthropic), regla de días válidos de IMERG Late diario a mes (D-011)
import numpy as np


def mensual_late(dias: np.ndarray, dias_del_mes: int, umbral: float = 0.8, relleno: float = -9999.9004):
    """Media mensual (UTC) por celda de un cubo diario [día, fila, columna].

    Una celda es válida si tiene al menos `umbral` de los días del CALENDARIO con dato;
    el denominador no es el número de granulos recibidos, así un mes en curso sale NaN.
    La unidad queda la del producto (mm/día); no se convierte.
    """
    valido = ~np.isclose(dias, relleno) & np.isfinite(dias)
    n = valido.sum(axis=0)
    suma = np.where(valido, dias, 0.0).sum(axis=0, dtype="float64")
    media = np.where(n >= umbral * dias_del_mes - 1e-9, suma / np.maximum(n, 1), np.nan)
    return media, n


def unidades_validas(media: np.ndarray, celdas_por_unidad) -> np.ndarray:
    """Unidad-mes válida si alguna de sus celdas (índices planos) tiene valor; si no, NaN."""
    plano = media.ravel()
    return np.array([bool(np.isfinite(plano[c]).any()) for c in celdas_por_unidad])
