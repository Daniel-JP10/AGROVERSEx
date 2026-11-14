# asistido por SI: Claude Code (Anthropic), escritura y revisión de código; base del prototipo migrada en el hackatón
"""Suelo: días de suelo expuesto, erosión RUSLE, carbono Tier 1 y cobertura IGBP anual (INICIAR §6).

Todo vectorizado. pH, CIC, nitrógeno, textura y densidad aparente "No medido" en el tiempo: se quedan en `estatico`.
"""
import warnings

import numpy as np
import pandas as pd

from simulacion import config
from simulacion.azar import rng_unidad
from simulacion.cobertura import COLS, cobertura_simulada
from simulacion.tiempo import dias_del_mes
from simulacion.variables import _SUP, _v

ANIOS = np.arange(2000, 2027)
N_ANIOS = len(ANIOS)
_DIAS_MES = np.array([dias_del_mes(m) for m in range(config.N_MESES)])

# --- días de suelo expuesto ---
NDVI_SUELO = 0.20      # SUPUESTO: NDVI mensual bajo este valor = suelo expuesto (revisión 2026-11-13)
NBR2_SUELO = 0.10      # SUPUESTO: NBR2 sobre este valor confirma suelo desnudo (HLS, desde 2013; revisión 2026-11-13)
ANIO_HLS = 2013        # FUENTE: HLS desde 2013-04 (INICIAR §4.1); antes solo NDVI de MOD13Q1, fiabilidad baja

# --- erosión RUSLE ---
FACTOR_BANDA = 2.5     # valor central SUPUESTO; el rango 2 a 3 es FUENTE (Borrelli 2017, INV-SUE §3)
KCAL = 0.04         # SUPUESTO: calibración global del producto R·K·LS·C para que caiga en las anclas (revisión 2026-11-13)
ANCLAS = {"global": 2.8, "cultivos": 12.7, "bosque": 0.16}  # t/ha/año, FUENTE Borrelli 2017 (INV-SUE §3)
CULTIVOS = (12, 14)    # IGBP: cultivos y mosaico cultivo/vegetación natural
BOSQUES = (1, 2, 3, 4, 5)  # IGBP
MULT_C_CULTIVO = 12.2  # SUPUESTO: calibrado a la ancla de cultivos 12,7 t/ha/año (revisión 2026-11-13)
MULT_C_BOSQUE = 0.41   # SUPUESTO: calibrado a la ancla de bosque 0,16 t/ha/año (revisión 2026-11-13)

# --- carbono ---
PROF_CM_A_FACTOR = 3   # 0-30 cm: g/kg · kg/dm³ · 3 = t C/ha (FUENTE: aritmética de unidades)
ANIOS_EQUILIBRIO = 20  # SUPUESTO Tier 1 (INICIAR §6.2, decisión 15.2-C; revisión 2026-11-13)
CAMBIO_MIN, CAMBIO_MAX = -0.1, 0.6  # t C/ha/año, INFERENCIA INV-SUE §6

# --- cobertura ---
P_CAMBIO_COBERTURA = 0.03   # SUPUESTO: fracción de unidades con un cambio en 2001-2025 (revisión 2026-11-13)

_ETIQ = ("MODELADO RUSLE con relieve de GMTED2010 (elev_max - elev_min), no pendiente de 30 m; "
         "factor LS indicativo, confianza baja; banda por factor de Borrelli 2017 (SUPUESTO central 2,5)")
_RUSLE = ("modelo", "RUSLE (R de IMERG, C de NDVI, K de SoilGrids, LS de GMTED2010)", "demo", "2000-01", "2026-11")
VARIABLES_ANUAL = {
    f"erosion_{q}": _v(f"erosion_{q}", "t/ha/año", 0.01, 0, 2000, *_RUSLE, _ETIQ, "EV-SUE")
    for q in ("p05", "p50", "p95")
}


def dias_suelo_expuesto(ndvi: np.ndarray, nbr2: np.ndarray | None, anio: int) -> tuple[np.ndarray, np.ndarray]:
    """ndvi, nbr2: (n, 12) de ese año. Devuelve (días (n,), suelo_metodo (n,)): 1 solo NDVI (hasta 2012), 2 NDVI y NBR2."""
    ndvi = np.asarray(ndvi, float)
    dias = _DIAS_MES[(anio - 2000) * 12:][:ndvi.shape[1]]
    metodo = 2 if anio >= ANIO_HLS else 1
    desnudo = ndvi < NDVI_SUELO
    if metodo == 2 and nbr2 is not None:
        nb = np.asarray(nbr2, float)
        desnudo = desnudo & ((nb > NBR2_SUELO) | np.isnan(nb))  # sin NBR2 en ese mes, queda solo el NDVI
    d = (desnudo * dias).sum(1).astype(float)
    d[np.isnan(ndvi).all(1)] = np.nan  # sin ningún mes observado no hay dato, no 0
    return d, np.full(ndvi.shape[0], metodo, dtype=int)


MES_HLS = 159  # abril de 2013 (mes_id), FUENTE: HLS desde 2013-04


def dias_suelo_mensual(ndvi: np.ndarray, nbr2: np.ndarray | None) -> tuple[np.ndarray, np.ndarray]:
    """(n, 323) para `mensual.dias_suelo_expuesto` y `suelo_metodo`. Sin NDVI el mes es NaN (NULL), nunca 0."""
    nd = np.asarray(ndvi, float)
    # método 2 solo si de verdad se aplicó NBR2 (sin él el rótulo "NDVI+NBR2" sería falso)
    metodo = np.broadcast_to(np.where((np.arange(nd.shape[1]) >= MES_HLS) & (nbr2 is not None), 2, 1), nd.shape).copy()
    desnudo = nd < NDVI_SUELO
    if nbr2 is not None:
        nb = np.asarray(nbr2, float)
        desnudo &= ~((metodo == 2) & (nb <= NBR2_SUELO))  # NBR2 sin dato (NaN) deja solo el NDVI
    return np.where(np.isnan(nd), np.nan, desnudo * _DIAS_MES[:nd.shape[1]]), metodo


def factor_r(precip_anual: np.ndarray) -> np.ndarray:
    """SUPUESTO: erosividad proporcional a la lluvia anual (mm); sin ficha para una fórmula R-P."""
    return np.asarray(precip_anual, float)


def factor_k(silt: np.ndarray, clay: np.ndarray) -> np.ndarray:
    """SUPUESTO: erodabilidad relativa creciente con limo y decreciente con arcilla (media de SoilGrids 0-30 cm)."""
    return np.clip(0.1 + 0.5 * np.asarray(silt, float) / 100 - 0.3 * np.asarray(clay, float) / 100, 0.02, 0.6)


def factor_ls(relieve_m: np.ndarray) -> np.ndarray:
    """SUPUESTO: LS por relieve (elev_max - elev_min de GMTED2010 a 1 km). NO es pendiente de 30 m."""
    return 0.1 + np.sqrt(np.maximum(np.asarray(relieve_m, float), 0) / 100)


def factor_c(ndvi: np.ndarray, igbp: np.ndarray) -> np.ndarray:
    """SUPUESTO: C = exp(-2·ndvi/(1-ndvi)) por MULT_C_CULTIVO en cultivos y MULT_C_BOSQUE en bosques (calibrados a Borrelli)."""
    n = np.clip(np.asarray(ndvi, float), 0, 0.95)
    mult = np.where(np.isin(igbp, CULTIVOS), MULT_C_CULTIVO, np.where(np.isin(igbp, BOSQUES), MULT_C_BOSQUE, 1.0))
    return np.exp(-2 * n / (1 - n)) * mult


def erosion_rusle(r, k, ls_relieve, c) -> dict:
    """t/ha/año. p05 = p50/factor y p95 = p50·factor (Borrelli 2017); no usa q05/q95 de SoilGrids (R6)."""
    p50 = KCAL * np.asarray(r, float) * k * ls_relieve * c
    return {"erosion_p05": p50 / FACTOR_BANDA, "erosion_p50": p50, "erosion_p95": p50 * FACTOR_BANDA}


def soc_stock(soc_gkg, bdod) -> np.ndarray:
    """t C/ha 0-30 cm. INFERENCIA: sin fragmentos gruesos (cfvo no está en la fase 1), sobrestima donde hay gravas."""
    return np.asarray(soc_gkg, float) * np.asarray(bdod, float) * PROF_CM_A_FACTOR


def soc_tier1(soc_stock0, cambio_manejo, anio) -> np.ndarray:
    """(n, T). cambio_manejo: fracción del stock a la que tiende el equilibrio (0 = sin cambio, constante).

    Lineal en ANIOS_EQUILIBRIO años desde anio[0]; el cambio anual se recorta a [-0,1, +0,6] t C/ha/año. soc_metodo = 1.
    """
    s0 = np.asarray(soc_stock0, float)[:, None]
    t = np.minimum(np.asarray(anio) - np.asarray(anio)[0], ANIOS_EQUILIBRIO)[None, :]
    por_anio = np.clip(s0 * np.asarray(cambio_manejo, float)[:, None] / ANIOS_EQUILIBRIO, CAMBIO_MIN, CAMBIO_MAX)
    return s0 + por_anio * t


def dias_calor(t2m_max: np.ndarray, umbral: float | None) -> np.ndarray:
    """PENDIENTE [DEP-F1-9]: sin umbral con ficha, todo NULL (NaN), nunca 0."""
    t = np.asarray(t2m_max, float)
    if umbral is None:
        return np.full(t.shape, np.nan)
    return (t > umbral).astype(float)


def cobertura_igbp(unidades: pd.DataFrame, koppen_moda, estatico: pd.DataFrame | None = None,
                   anios=ANIOS) -> tuple[np.ndarray, np.ndarray]:
    """(igbp (n, T) entero 1..17, fracciones (n, 17)). IGBP simulada por región (D-010), rotulada; sin interpolar.

    Cambios escasos (P_CAMBIO_COBERTURA, SUPUESTO): en un año aleatorio la clase pasa a la segunda de la mezcla (vecino más cercano).
    """
    if estatico is not None:  # cobertura espera phh2o, clay, sand sin sufijo de profundidad
        estatico = estatico.rename(columns=lambda c: c.removesuffix("_0_30"))
    cob = cobertura_simulada(unidades, koppen_moda, estatico)
    f = cob[COLS].to_numpy()
    orden = np.argsort(-f, axis=1)
    dom, seg = orden[:, 0] + 1, orden[:, 1] + 1
    z = np.array([rng_unidad(u, "cambio_cobertura").random(2) for u in unidades.index]).reshape(-1, 2)
    cambia = z[:, 0] < P_CAMBIO_COBERTURA
    anio_cambio = 2005 + (z[:, 1] * 20).astype(int)  # SUPUESTO: año de cambio uniforme en 2005-2024 (rev. 2026-11-13)
    igbp = np.where(cambia[:, None] & (np.asarray(anios)[None, :] >= anio_cambio[:, None]), seg[:, None], dom[:, None])
    return igbp.astype(int), f


def serie_suelo_anual(clima, ndvi: dict, geo: pd.DataFrame, estatico: pd.DataFrame, igbp: np.ndarray) -> dict:
    """Series anuales (n, 27) de erosión, NDVI medio y máximo, y SOC. `estatico`: columnas silt_0_30, clay_0_30,
    soc_0_30, bdod_0_30, elev_max, elev_min indexadas por unidad. 2026 es parcial: se promedia lo observado."""
    n = len(geo)
    def anual(x, f):
        x = np.pad(np.asarray(x, float), ((0, 0), (0, N_ANIOS * 12 - x.shape[1])), constant_values=np.nan)
        return f(x.reshape(n, N_ANIOS, 12), axis=2)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", RuntimeWarning)
        lluvia = anual(clima.precip, np.nanmean) * 12   # mm/año, 2026 escalado desde sus meses (SUPUESTO)
        nd_med = anual(ndvi["ndvi"], np.nanmean)
        nd_max = anual(ndvi["ndvi"], np.nanmax)
    e = estatico.reindex(geo.index)
    relieve = (e.elev_max - e.elev_min).to_numpy(float)
    c = factor_c(np.nan_to_num(nd_med, nan=0.3), igbp)  # sin NDVI (nieve/nube todo el año): NDVI 0,3 neutro, SUPUESTO
    ero = erosion_rusle(factor_r(lluvia), factor_k(e.silt_0_30.to_numpy(float), e.clay_0_30.to_numpy(float))[:, None],
                        factor_ls(relieve)[:, None], c)
    soc = soc_tier1(soc_stock(e.soc_0_30, e.bdod_0_30), np.zeros(n), ANIOS)
    return {**ero, "ndvi_med": nd_med, "ndvi_max": nd_max, "soc_tier1": soc}
