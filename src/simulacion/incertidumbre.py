# asistido por SI: Claude Code (Anthropic), escritura y revisión de código; base del prototipo migrada en el hackatón
"""Campos de error que imitan los de cada producto real (INICIAR §5.7).

Los coeficientes son SUPUESTO (revisión 2026-11-13) mientras no tengan ficha EV-*.
"""
import numpy as np

Z_P90 = 1.2816  # cuantil 0,9 de la normal estándar


def err_precip(precip: np.ndarray, frac: np.ndarray, provisional: bool = False) -> np.ndarray:
    # SUPUESTO: imita randomError de IMERG; crece con el valor y con la poca fracción válida
    e = (0.05 + 0.3 * np.abs(precip)) / np.sqrt(np.clip(frac, 0.1, 1))
    # SUPUESTO: Late V07 provisional con banda 1,5 veces más ancha (D-008)
    return e * 1.5 if provisional else e


def err_sm_l4(sm: np.ndarray) -> np.ndarray:
    # SUPUESTO: imita la desviación del ensamble (*_ensstd) de SMAP L4
    return 0.01 + 0.05 * np.abs(sm)


def err_sm_sin_campo(n: int) -> np.ndarray:
    # PENDIENTE de fuente: requisito de misión de 0,04 m³/m³ (INICIAR §5.7); SUPUESTO con confianza baja
    return np.full(n, 0.04)


def err_tws(tws: np.ndarray, mascon_sigma: float) -> np.ndarray:
    # SUPUESTO: sigma del mascon más 5 % de la anomalía
    return np.hypot(mascon_sigma, 0.05 * tws)


def err_lst(lst: np.ndarray, calidad: np.ndarray) -> np.ndarray:
    # INFERENCIA (sin ficha): bits 6-7 del QC de MOD11 = error <=1, <=2, <=3 o >3 K; se usa el techo (4 K para >3)
    return np.where(np.isnan(lst), np.nan, (np.asarray(calidad) + 1).astype(float))


def banda_p10_p90(valor: np.ndarray, dispersion_unidad: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    # Aproximación normal: p10 y p90 a ±1,2816 desviaciones
    d = Z_P90 * np.abs(dispersion_unidad)
    return valor - d, valor + d


def nivel_confianza(frac: np.ndarray, nivel_dato: str, tiene_intervalo: bool) -> np.ndarray:
    # 2 alto, 1 medio, 0 bajo (INICIAR §5.7, SUPUESTO)
    frac = np.asarray(frac, float)
    if not tiene_intervalo:
        return np.zeros(frac.shape, np.int8)
    if nivel_dato == "observado":
        return np.where(frac >= 0.8, 2, np.where(frac >= 0.5, 1, 0)).astype(np.int8)
    return np.where(frac >= 0.5, 1, 0).astype(np.int8)
