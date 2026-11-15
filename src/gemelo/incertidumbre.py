# asistido por SI: Cursor (agente), escritura y revisión de código; núcleo del gemelo digital en el hackatón
"""Incertidumbre paramétrica: hipercubo latino sobre los rangos de theta y resumen por percentiles.

Cada Parametro con rango se muestrea (uniforme o triangular con moda en el valor central). Los que no tienen
rango quedan fijos. La muestra 0 es siempre el vector central, para que el ensamble contenga la corrida nominal.
"""
import numpy as np
from scipy.stats import qmc

from gemelo.procedencia import Parametro

PERCENTILES = (10, 50, 90)


def _inversa(u, p: Parametro):
    lo, hi = p.limites()
    c = p.exigir()
    if hi <= lo:
        return np.full_like(u, c)
    if p.distribucion == "uniforme":
        return lo + u * (hi - lo)
    fc = (c - lo) / (hi - lo)                     # triangular con moda c
    return np.where(u < fc, lo + np.sqrt(u * (hi - lo) * (c - lo)), hi - np.sqrt((1 - u) * (hi - lo) * (hi - c)))


def muestrear(parametros: dict[str, Parametro], n: int, semilla: int) -> dict[str, np.ndarray]:
    """{nombre: valores (n,)}. Solo los parámetros con rango varían; la muestra 0 es la central."""
    inciertos = [k for k, p in parametros.items() if p.rango is not None and p.rango[1] > p.rango[0]]
    salida = {k: np.full(n, p.exigir()) for k, p in parametros.items()}
    if n > 1 and inciertos:
        u = qmc.LatinHypercube(d=len(inciertos), seed=semilla).random(n - 1)
        for j, k in enumerate(inciertos):
            salida[k][1:] = _inversa(u[:, j], parametros[k])
    return salida


def resumir(valores: np.ndarray, eje: int = 0) -> dict:
    """p10, p50, p90 a lo largo del eje de miembros (NaN se ignoran)."""
    v = np.asarray(valores, float)
    if v.size == 0 or np.all(np.isnan(v)):
        return {f"p{q}": None for q in PERCENTILES}
    r = np.nanpercentile(v, PERCENTILES, axis=eje)
    return {f"p{q}": (float(x) if np.ndim(x) == 0 else x) for q, x in zip(PERCENTILES, r)}


def cvar(valores: np.ndarray, alfa: float = 0.9) -> float:
    """CVaR_alfa: media de la cola superior (peor 1 - alfa) de una pérdida."""
    v = np.sort(np.asarray(valores, float))
    k = max(1, int(np.ceil((1 - alfa) * len(v))))
    return float(v[-k:].mean())
