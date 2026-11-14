# asistido por SI: Claude Code (Anthropic), escritura y revisión de código; base del prototipo migrada en el hackatón
"""NDVI, ET y LST mensuales sintéticos (Task 7).

NDVI = mínimo + (máximo - mínimo) * factor de crecimiento, con máximo y mínimo de la clase IGBP dominante
(cobertura simulada, D-010). El factor sale de la T y la lluvia del Clima. Todo vectorizado (n unidades, 323 meses);
el azar sale de rng_unidad, así un bloque da lo mismo que la corrida completa.
"""
import numpy as np
import pandas as pd

from simulacion import config
from simulacion.azar import rng_unidad
from simulacion.cobertura import cobertura_simulada
from simulacion.incertidumbre import banda_p10_p90, err_lst
from simulacion.productos import aplicar_cobertura, bandera_mes
from simulacion.tiempo import dias_del_mes
from simulacion.variables import B_HUECO, B_NIEVE, B_NUBE, B_PROVISIONAL

N = config.N_MESES
_DIAS = np.array([dias_del_mes(m) for m in range(N)])
# SUPUESTO (revisión 2026-11-13): NDVI máximo y mínimo por clase IGBP 1..17. El pico de cultivo (0,84) cae en el
# rango maíz 0,78-0,86 y soya 0,87-0,91 de INV-VEG §8 (FUENTE para el rango, SUPUESTO para el valor central)
_NMAX = np.array([.75, .85, .72, .82, .80, .60, .35, .65, .60, .65, .60, .84, .30, .75, .05, .08, -.05])
_NMIN = np.array([.60, .80, .30, .35, .50, .30, .15, .35, .30, .25, .30, .20, .20, .30, .00, .05, -.05])
SIGMA_NDVI = 0.04          # SUPUESTO: dispersión para la banda p10-p90
SD_ANUAL, SD_MES = 0.02, 0.015  # SUPUESTO: ruido interanual y mensual
# LIMITACIÓN (D-024): sin ajuste de greening en ningún país; se retiró el coeficiente de Chen 2019 y no hay reemplazo
ET_MAX_8D = 12.0 * 8       # SUPUESTO: tope físico de 12 mm/día (brief, §5.4)
SD_REL_ET = 0.15           # SUPUESTO: banda relativa de ET
P_HUECO_GF, P_HUECO_2026 = 0.01, 0.15  # SUPUESTO: MOD16A2GF rellena huecos; MOD16A2 de 2026 no
DELTA_LST_SUELO = 5.0      # SUPUESTO: K extra de suelo desnudo frente a vegetación densa


def _nieve_nube(c):
    # SUPUESTO: nieve crece con la T bajo 0 °C (total a -10 °C); nube con la lluvia mensual (máx. 0,6)
    s = np.clip(-np.nan_to_num(c.t2m) / 10, 0, 1)
    n = np.clip(np.nan_to_num(c.precip) / 500, 0, 0.6)
    return s, n


def bandera_nieve_nube(clima, bloque=None) -> np.ndarray:
    # Clima ya corresponde al bloque; `bloque` se acepta por la interfaz del brief y no se usa
    s, n = _nieve_nube(clima)
    return np.where(s > 0.2, B_NIEVE, 0) | np.where(n > 0.4, B_NUBE, 0)


def generar_ndvi(clima, bloque: slice, geo: pd.DataFrame, estatico: pd.DataFrame | None = None) -> dict:
    """geo: DataFrame completo de unidades; ids = geo.index[bloque], alineados con las filas de `clima`."""
    g = geo.iloc[bloque]
    ids = list(g.index)
    cob = cobertura_simulada(g, g.koppen, estatico)
    dom = cob.igbp_dominante.to_numpy() - 1
    t, p = np.nan_to_num(clima.t2m), np.nan_to_num(clima.precip)
    crec = np.minimum(np.clip((t - 5) / 15, 0, 1), np.clip(p / 60, 0, 1))
    nmax, nmin = _NMAX[dom][:, None], _NMIN[dom][:, None]
    z = np.stack([rng_unidad(u, "ndvi").standard_normal((2, N)) for u in ids]) if ids else np.zeros((0, 2, N))
    anio = np.arange(N) // 12
    ndvi = nmin + (nmax - nmin) * crec + SD_ANUAL * z[:, 0, :27][:, anio] + SD_MES * z[:, 1]
    ndvi = np.clip(ndvi, -0.2, 1.0)
    p10, p90 = banda_p10_p90(ndvi, SIGMA_NDVI)
    p10, p90 = np.clip(p10, -0.2, 1.0), np.clip(p90, -0.2, 1.0)

    s, n = _nieve_nube(clima)
    ndvi, cov, b = aplicar_cobertura(ndvi, "mod13")
    frac = cov * (1 - s) * (1 - n)
    frac = np.where(frac < 0.05, 0.0, frac)  # sin píxeles útiles: NaN, no 0
    sin = frac == 0
    return {"ndvi": np.where(sin, np.nan, ndvi), "ndvi_p10": np.where(sin, np.nan, p10),
            "ndvi_p90": np.where(sin, np.nan, p90), "ndvi_frac": frac,
            "bandera": b[None, :] | bandera_nieve_nube(clima), "igbp_dominante": dom + 1}


def empaquetar_et_lst(clima, agua, bloque: slice, geo: pd.DataFrame, ndvi: dict | None = None) -> dict:
    """ET (kg/m²/8 días, desde agua.et_real en mm/mes) y LST diurna (K). Un `ndvi` ya calculado evita repetirlo."""
    g = geo.iloc[bloque]
    ids = list(g.index)
    nd = ndvi if ndvi is not None else generar_ndvi(clima, bloque, geo)
    et = np.clip(np.asarray(agua.et_real, float) / _DIAS * 8, 0, ET_MAX_8D)
    et, cov, b_et = aplicar_cobertura(et, "mod16")
    prov = (b_et & B_PROVISIONAL) > 0  # 2026 con MOD16A2 sin relleno
    u = np.stack([rng_unidad(i, "et").random(N) for i in ids]) if ids else np.zeros((0, N))
    hueco = u < np.where(prov, P_HUECO_2026, P_HUECO_GF)[None, :]
    et = np.where(hueco, np.nan, et)
    p10, p90 = banda_p10_p90(et, SD_REL_ET * et)
    et_frac = np.where(np.isnan(et), 0.0, np.broadcast_to(cov, et.shape))

    # LST: Tmax + suelo desnudo; nubes bajan la fracción válida y suben el error
    _, n = _nieve_nube(clima)
    veg = np.clip(np.nan_to_num(nd["ndvi"], nan=0.3), 0, 1)
    lst = np.clip(np.nan_to_num(clima.t2m_max) + 273.15 + DELTA_LST_SUELO * (1 - veg), 250, 340)
    lst, cov11, b11 = aplicar_cobertura(lst, "mod11")
    lfrac = cov11 * (1 - 0.9 * n)  # SUPUESTO: la nube resta hasta 90 % de la fracción de LST (rev. 2026-11-13)
    lst = np.where(lfrac < 0.05, np.nan, lst)
    err = err_lst(lst, np.clip(np.floor(n * 5), 0, 3))
    bandera = b_et[None, :] | b11[None, :] | np.where(hueco, B_HUECO, 0) | np.where(n > 0.4, B_NUBE, 0)
    return {"et": et, "et_p10": np.maximum(p10, 0), "et_p90": p90, "et_frac": et_frac,
            "lst_dia": lst, "lst_err": err, "lst_frac": np.where(np.isnan(lst), 0.0, lfrac), "bandera": bandera}
