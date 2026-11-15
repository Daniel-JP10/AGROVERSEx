# asistido por SI: Cursor (agente), escritura y revisión de código; núcleo del gemelo digital en el hackatón
"""Nitrógeno mineral del suelo N(t), kg N/ha:  dN/dt = F_N + M_N - U_N - L_N.

F_N: fertilizante neto de volatilización. La fijación biológica entra a la planta, no al suelo; llega al suelo
     cuando el residuo se mineraliza (por eso se reporta aparte).
M_N: mineralización neta del carbono (carbono.py); negativa = inmovilización.
U_N: absorción desde el suelo, (1 - Ndfa) * n_biomasa * dB.
L_N: lixiviación con el drenaje profundo más volatilización del fertilizante.
"""
import numpy as np


def limitar_por_n(db_sin_n, n_biomasa, ndfa, n_disponible, ndfa_max=0.0):
    """Crecimiento limitado por N (ley del mínimo) y reparto de la demanda entre suelo y fijación.

    Demanda = n_biomasa * dB. Una leguminosa (ndfa > 0) fija ndfa de la demanda y, si el suelo no cubre el
    resto, aumenta la fijación hasta ndfa_max (la fijación sube cuando el N del suelo es bajo). Sin leguminosa
    toda la demanda va al suelo. Devuelve (dB, absorción del suelo, fijación, f_N); U + fijación = n dB.
    """
    dem = n_biomasa * db_sin_n
    fij_base = ndfa * dem
    absorcion = np.minimum(dem - fij_base, np.maximum(n_disponible, 0.0))
    tope = np.where(ndfa > 0, np.maximum(ndfa_max, ndfa) * dem, fij_base)
    fijacion = np.minimum(dem - absorcion, tope)
    f_n = np.where(dem > 1e-12, (absorcion + fijacion) / np.maximum(dem, 1e-12), 1.0)
    return db_sin_n * f_n, absorcion, fijacion, f_n


def fertilizar(kg_n, frac_volatilizacion):
    """(N que entra al suelo, N volatilizado)."""
    return kg_n * (1.0 - frac_volatilizacion), kg_n * frac_volatilizacion


def lixiviacion(n_mineral, drenaje_mm, agua_perfil_mm):
    """N que sale con el drenaje profundo, con concentración uniforme en el agua del perfil (SUPUESTO)."""
    frac = drenaje_mm / np.maximum(agua_perfil_mm + drenaje_mm, 1e-9)
    return n_mineral * np.clip(frac, 0, 1)


def n_disponible_raiz(n_mineral, z_raiz, zp):
    """N accesible a las raíces: proporcional al espesor explorado (distribución uniforme, SUPUESTO)."""
    return n_mineral * np.clip(z_raiz / zp, 0, 1)
