# asistido por SI: Claude Code (Anthropic), escritura y revisión de código; base del prototipo migrada en el hackatón
"""Condición de la tierra (ODS 15.3.1, INICIAR §6.2): uno fuera, todos fuera, por periodos. Nunca un promedio."""
import math
import warnings

import numpy as np
import pandas as pd

from simulacion.suelo import ANIOS, CULTIVOS

DEGRADADO, ESTABLE, MEJORA = 0, 1, 2
# periodo 1 = línea base 2000-2015; 2 = 2016-2019; 3 = 2020-2023; 4 = 2024-2026 (parcial)
PERIODOS = {1: (2000, 2015), 2: (2016, 2019), 3: (2020, 2023), 4: (2024, 2026)}
P_SIGNIF = 0.05        # SUPUESTO: significancia de la tendencia (revisión 2026-11-13)
UMBRAL_REL = 0.10      # SUPUESTO: cambio relativo que separa estable de degradado/mejora (revisión 2026-11-13)
Z_RUIDO = 2.0          # SUPUESTO: el cambio debe superar 2 errores estándar del ruido interanual de la línea base


def periodo_de(anio) -> np.ndarray:
    a = np.asarray(anio)
    return np.select([a <= 2015, a <= 2019, a <= 2023], [1, 2, 3], 4)


def prueba_tendencia(serie_anual) -> tuple[float, float]:
    """Pendiente de Sen y p-valor bilateral de Mann-Kendall (aproximación normal, sin empates), por última dimensión."""
    x = np.asarray(serie_anual, float)
    n = x.shape[-1]
    i, j = np.triu_indices(n, 1)
    d = x[..., j] - x[..., i]
    pend = np.nanmedian(d / (j - i), axis=-1)
    s = np.nansum(np.sign(d), axis=-1)
    var = n * (n - 1) * (2 * n + 5) / 18
    z = np.where(s > 0, s - 1, np.where(s < 0, s + 1, 0)) / math.sqrt(var)
    p = np.vectorize(lambda v: math.erfc(abs(v) / math.sqrt(2)))(z)
    return (float(pend), float(p)) if x.ndim == 1 else (pend, p)


def clase_tendencia(pend, p) -> np.ndarray:
    return np.where(p < P_SIGNIF, np.where(pend > 0, MEJORA, DEGRADADO), ESTABLE)


def clase_por_cambio(rel, mejora_si_sube: bool = True, z=None) -> np.ndarray:
    """Cambio relativo contra la línea base; NaN queda NaN (componente no evaluado).

    Con z (cambio en errores estándar del ruido de la línea base), solo cuenta si |z| supera Z_RUIDO.
    """
    rel = np.asarray(rel, float)
    if z is not None:
        rel = np.where(np.abs(z) > Z_RUIDO, rel, 0.0)
    sube = np.where(rel > UMBRAL_REL, 1, np.where(rel < -UMBRAL_REL, -1, 0)) * (1 if mejora_si_sube else -1)
    return np.where(np.isnan(rel), np.nan, np.where(sube > 0, MEJORA, np.where(sube < 0, DEGRADADO, ESTABLE)))


def clase_cobertura(igbp_ini, igbp_fin) -> np.ndarray:
    """SUPUESTO: pasar de natural a cultivo, urbano o suelo desnudo degrada; el camino inverso mejora; otro cambio, estable."""
    a, b = np.asarray(igbp_ini), np.asarray(igbp_fin)
    peor = lambda k: np.isin(k, (12, 13, 14, 16))
    return np.where(a == b, ESTABLE, np.where(peor(b) & ~peor(a), DEGRADADO, np.where(peor(a) & ~peor(b), MEJORA, ESTABLE)))


def clasificar_condicion(prod_tendencia, prod_estado, prod_desempeno, cobertura_cambio, erosion, soc) -> np.ndarray:
    """Entradas: clases 0/1/2 por componente (NaN = no evaluado, se ignora). Un solo 0 degrada; sin 0, un 2 mejora.

    Salida entera {0,1,2}; -1 solo si ningún componente tiene dato (el generador lo escribe como NULL).
    """
    c = np.stack(np.broadcast_arrays(*[np.asarray(x, float) for x in
                                       (prod_tendencia, prod_estado, prod_desempeno, cobertura_cambio, erosion, soc)]))
    con_dato = ~np.isnan(c)
    degr = (c == DEGRADADO).any(0)
    mejora = (c == MEJORA).any(0)
    out = np.where(degr, DEGRADADO, np.where(mejora, MEJORA, ESTABLE))
    return np.where(con_dato.any(0), out, -1).astype(int)


def _z(x, p):
    # (media del periodo - media base) / (sd interanual base / sqrt(años del periodo))
    a, b = PERIODOS[p]
    sd = np.nanstd(x[:, :16], axis=1)
    return (_medias(x, p) - _medias(x, 1)) / np.maximum(sd / np.sqrt(b - a + 1), 1e-12)


def _medias(x, p):
    a, b = PERIODOS[p]
    return np.nanmean(x[:, a - 2000:b - 2000 + 1], axis=1)


def tabla_anual(geo_ids, igbp, serie: dict) -> pd.DataFrame:
    """Filas de `anual` (n·27) con clase_condicion solo en los periodos 2 a 4 (la línea base queda NULL)."""
    n = len(geo_ids)
    comp = {k: np.full((n, len(ANIOS)), np.nan) for k in ("prod_tendencia", "prod_estado", "prod_desempeno")}
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", RuntimeWarning)
        base = {k: _medias(serie[k], 1) for k in ("ndvi_med", "ndvi_max", "erosion_p50", "soc_tier1")}
        clase_final = np.full((n, len(ANIOS)), np.nan)
        for p in (2, 3, 4):
            a, b = PERIODOS[p]
            sl = slice(a - 2000, b - 2000 + 1)
            pend, pv = prueba_tendencia(serie["ndvi_med"][:, :b - 2000 + 1])  # ventana creciente desde 2000
            rel = lambda k: _medias(serie[k], p) / base[k] - 1
            c_tend = clase_tendencia(pend, pv)
            c_est = clase_por_cambio(rel("ndvi_med"), z=_z(serie["ndvi_med"], p))
            c_des = clase_por_cambio(rel("ndvi_max"), z=_z(serie["ndvi_max"], p))
            c_cob = clase_cobertura(igbp[:, 2000 - 2000 + 15], igbp[:, b - 2000])
            c_ero = clase_por_cambio(rel("erosion_p50"), mejora_si_sube=False, z=_z(serie["erosion_p50"], p))
            c_soc = clase_por_cambio(rel("soc_tier1"), z=_z(serie["soc_tier1"], p))
            clase_final[:, sl] = clasificar_condicion(c_tend, c_est, c_des, c_cob, c_ero, c_soc)[:, None]
            comp["prod_tendencia"][:, sl] = pend[:, None]
            comp["prod_estado"][:, sl] = rel("ndvi_med")[:, None]
            comp["prod_desempeno"][:, sl] = rel("ndvi_max")[:, None]
    clase_final[clase_final < 0] = np.nan
    ids = np.repeat(np.asarray(geo_ids), len(ANIOS))
    df = pd.DataFrame({"unidad_id": ids, "anio": np.tile(ANIOS, n)})
    for k, v in comp.items():
        df[k] = v.ravel()
    df["cobertura_igbp"] = igbp.ravel()
    df["cambio_cobertura"] = (igbp != igbp[:, [0]]).ravel().astype(int)
    for k in ("erosion_p05", "erosion_p50", "erosion_p95", "soc_tier1"):
        df[k] = serie[k].ravel()
    df["soc_metodo"] = 1
    df["clase_condicion"] = clase_final.ravel()
    df["periodo"] = np.tile(periodo_de(ANIOS), n)
    return df
