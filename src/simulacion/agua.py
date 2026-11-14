# asistido por SI: Claude Code (Anthropic), escritura y revisión de código; base del prototipo migrada en el hackatón
"""Agua mensual sintética: balance hídrico de un cubo, humedad GLDAS→SMAP y TWS tipo GRACE (Task 6).

Unidades: precip, ET y escorrentía en mm/mes; almacenamiento en mm; humedad en m³/m³; tws en cm.
Todo vectorizado entre unidades; solo el bucle temporal del balance (323 meses).
"""
from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from simulacion import config
from simulacion.clima import _rad_extraterrestre, cargar_geo
from simulacion.incertidumbre import err_sm_l4, err_sm_sin_campo, err_tws, nivel_confianza
from simulacion.productos import aplicar_cobertura, bandera_mes, fraccion_dias
from simulacion.referencias.cargar import cargar_rodell
from simulacion.tiempo import dias_del_mes, mes_id

N = config.N_MESES
_DIAS = np.array([dias_del_mes(m) for m in range(N)])
_MES = np.arange(N) % 12
MES_SMAP = mes_id(2015, 3)  # primer mes con SMAP (2015-03-31)

# SUPUESTO (revisión 2026-11-13), sin ficha: constantes del cubo y de GRACE
PROF_RAIZ_MM = 1000.0       # profundidad del cubo (zona de raíces)
FRAC_ESTRES = 0.5           # bajo esta fracción de la capacidad la ET real baja linealmente
S0_FRAC = 0.5               # almacenamiento inicial, fracción de la capacidad
SM_MIN, SM_GLDAS_MAX = 0.02, 0.6   # GLDAS <= 60 kg/m² en 0-10 cm = 0,6 m³/m³ (INICIAR §5.4)
MASCON_SIGMA_CM = 2.0       # sigma del mascon (PENDIENTE de ficha)
BASE_GRACE = slice(4 * 12 + 0, 10 * 12)   # línea base 2004-2009 de la anomalía (SUPUESTO)
POROSIDAD_RESPALDO_IGBP = np.array([.50, .50, .50, .50, .50, .45, .43, .45, .45, .45, .45, .45, .45, .50, .40, .40, .40])
# SUPUESTO: porosidad de respaldo por clase IGBP 1..17 cuando el suelo es NULL

RODELL_MES = (mes_id(2002, 1), mes_id(2016, 12))  # FUENTE: periodo 2002-2016 de Rodell 2018 (EV-ENS-017)
# SUPUESTO (revisión 2026-11-13): sm_sup responde a la lluvia del mes con esta fracción de la capacidad del cubo
K_SUP = 0.5

UMBRAL_L3 = 0.5 # decisión del controlador: bajo esta fracción de días de L3 se usa L4

# Sesgo de nivel del empalme GLDAS→SMAP: PENDIENTE (sin ficha EV-AGU que lo traiga); queda sin sesgo
SESGO_EMPALME = None
METADATOS = {"empalme_gldas_smap_sesgo": "PENDIENTE",
             "tws_tendencia_rodell": "INFERENCIA: Rodell 2018 (EV-ENS-017) en cm/año sobre cajas SUPUESTO, sin regiones de hielo",
             "tws_nota": "deriva del cubo quitada; solo queda la tendencia de Rodell donde la unidad cae en su caja; celda de 3°x3°"}


@dataclass
class Agua:
    sm_sup: np.ndarray
    sm_raiz: np.ndarray
    sm_err: np.ndarray
    sm_fuente: np.ndarray   # 1 GLDAS, 2 SMAP L4 (modelo con asimilación), 3 SMAP L3
    sm_qual: np.ndarray
    sm_frac: np.ndarray
    tws: np.ndarray
    tws_err: np.ndarray
    tws_frac: np.ndarray
    et_real: np.ndarray     # mm/mes
    bandera: np.ndarray
    metadatos: dict = field(default_factory=lambda: dict(METADATOS))


def eto_hargreaves(lat, t2m, t2m_max, t2m_min) -> np.ndarray:
    # SUPUESTO de método: Hargreaves-Samani (la ficha FAO-56 respalda Kc, no este método); mm/mes
    ra = _rad_extraterrestre(np.asarray(lat, float))[:, _MES] / 2.45   # MJ/m²/día -> mm/día
    rango = np.sqrt(np.maximum(t2m_max - t2m_min, 0))
    return np.maximum(0.0023 * ra * (t2m + 17.8) * rango, 0) * _DIAS[None, :]


def porosidad_suelo(bdod, igbp) -> tuple[np.ndarray, np.ndarray]:
    """1 - bdod/2,65 (INFERENCIA: física de suelos estándar, sin ficha); respaldo por clase si bdod es NULL."""
    bdod = np.asarray(bdod, float)
    resp = POROSIDAD_RESPALDO_IGBP[np.asarray(igbp, int) - 1]
    nulo = np.isnan(bdod)
    return np.clip(np.where(nulo, resp, 1 - bdod / 2.65), 0.25, 0.65), nulo


def balance_hidrico(precip, eto, kc, porosidad, s0):
    """Cubo por unidad y mes -> (almacenamiento, ET real, escorrentía), mm. P - ET - Q - dS = 0 por construcción."""
    precip, eto, kc = (np.nan_to_num(np.asarray(a, float)) for a in (precip, eto, kc))
    cap = np.asarray(porosidad, float) * PROF_RAIZ_MM
    s = np.asarray(s0, float).copy()
    alm, et, q = (np.empty(precip.shape) for _ in range(3))
    for t in range(precip.shape[1]):
        disp = s + precip[:, t]
        e = np.minimum(kc[:, t] * eto[:, t] * np.minimum(1, disp / (FRAC_ESTRES * cap)), disp)
        s = disp - e
        q[:, t] = np.maximum(s - cap, 0)
        s = s - q[:, t]
        alm[:, t], et[:, t] = s, e
    return alm, et, q


def humedad_por_fuente(sm_modelo, fraccion_l3, fraccion_l4, sesgo=SESGO_EMPALME):
    """(sm_sup, sm_fuente). 1 GLDAS antes de SMAP; 2 (L4, modelo con asimilación) si la fracción de L3 < 0,5; si no, 3 (L3)."""
    sm = np.asarray(sm_modelo, float)
    m = np.arange(sm.shape[1])
    fuente = np.where(m < MES_SMAP, 1, np.where(np.asarray(fraccion_l3) < UMBRAL_L3, 2, 3)).astype(np.int8)
    if sesgo is not None:  # sesgo de nivel documentado, solo a partir de SMAP
        sm = sm + np.where(m >= MES_SMAP, sesgo, 0.0)[None, :]
    return sm, np.broadcast_to(fuente, sm.shape).copy()


def tws_desde_almacenamiento(almacenamiento, celdas_3grados) -> np.ndarray:
    """Media del almacenamiento por celda de 3°, anomalía en cm respecto de 2004-2009, sin deriva del cubo; la
    tendencia de Rodell se suma aparte en generar_agua."""
    a = np.asarray(almacenamiento, float)
    cel = np.asarray(celdas_3grados)
    _, inv = np.unique(cel, return_inverse=True)
    suma = np.zeros((inv.max() + 1, a.shape[1])) if len(inv) else np.zeros((0, a.shape[1]))
    np.add.at(suma, inv, a)
    media = suma / np.bincount(inv)[:, None]
    # La deriva del cubo sería una tendencia falsa: se quita la lineal
    t = np.arange(a.shape[1])
    media = media - np.array([np.polyval(np.polyfit(t, f, 1), t) for f in media]) if len(media) else media
    return ((media - media[:, BASE_GRACE].mean(1, keepdims=True)) / 10.0)[inv]  # mm -> cm


def tendencia_rodell_cm_anio(lat, lon) -> np.ndarray:
    """cm/año de Rodell por unidad: la de la caja más pequeña que la contiene; 0 fuera y en regiones de hielo
    (allí los cm son sobre el polígono de hielo, no sobre suelo agrícola). Cajas SUPUESTO."""
    lat, lon = np.asarray(lat, float), np.asarray(lon, float)
    out, area = np.zeros(len(lat)), np.full(len(lat), np.inf)
    for r in cargar_rodell().itertuples():
        if r.hielo or r.caja is None or r.region == "Caspian Sea":  # la caja del Caspio es mar y tierra: se excluye
            continue
        s, n, o, e = r.caja
        dentro = (lat >= s) & (lat <= n) & (lon >= o) & (lon <= e) & (r.area_km2 < area)
        out[dentro], area[dentro] = r.cm_anio, r.area_km2
    return out


def celda_3grados(lat, lon) -> np.ndarray:
    # Celda de 3°x3° (la de GRACE, aproximada por rejilla regular)
    return (np.floor((np.asarray(lat, float) + 90) / 3).astype(int) * 1000
            + np.floor((np.asarray(lon, float) + 180) / 3).astype(int))


def generar_agua(clima, ndvi, bloque: slice, geo: pd.DataFrame | None = None,
                 estatico: pd.DataFrame | None = None) -> Agua:
    """geo: DataFrame completo (por defecto cargar_geo()); estatico: columna `bdod` en kg/dm³ indexada por id."""
    g = (geo if geo is not None else cargar_geo()).iloc[bloque]
    nd = ndvi["ndvi"] if isinstance(ndvi, dict) else np.asarray(ndvi)
    igbp = ndvi["igbp_dominante"] if isinstance(ndvi, dict) else np.full(len(g), 12)
    bdod = (estatico["bdod"].reindex(g.index).to_numpy(float) if estatico is not None and "bdod" in estatico
            else np.full(len(g), np.nan))
    por, _ = porosidad_suelo(bdod, igbp)
    eto = eto_hargreaves(g.punto_lat.to_numpy(float), *(np.nan_to_num(getattr(clima, k)) for k in ("t2m", "t2m_max", "t2m_min")))
    # SUPUESTO: Kc lineal en NDVI (no es la ficha FAO-56 de Kc por cultivo); sin NDVI, 0,5
    kc = np.clip(0.1 + 1.2 * np.nan_to_num(nd, nan=0.35), 0.1, 1.15)
    alm, et, _ = balance_hidrico(clima.precip, eto, kc, por, S0_FRAC * por * PROF_RAIZ_MM)
    sm_raiz = alm / PROF_RAIZ_MM
    # SUPUESTO: la capa superior reacciona más rápido a la lluvia reciente que la zona de raíces (anomalía mensual de lluvia)
    llu = np.nan_to_num(clima.precip) / np.maximum(clima.precip_frac, 0.1) / (por * PROF_RAIZ_MM)[:, None]
    sm_sup0 = sm_raiz + K_SUP * (llu - llu.mean(1, keepdims=True))
    sm_mod = np.clip(sm_sup0, SM_MIN, np.minimum(por, SM_GLDAS_MAX)[:, None])
    l3, l4 = fraccion_dias("smap_l3"), fraccion_dias("smap_l4")
    sm_sup, fuente = humedad_por_fuente(sm_mod, l3, l4)
    frac = np.where(fuente == 1, fraccion_dias("gldas"), np.where(fuente == 3, l3, l4))
    err = np.where(fuente == 2, err_sm_l4(sm_sup), err_sm_sin_campo(1)[0])
    qual = np.where(fuente == 2, nivel_confianza(frac, "modelo", True), 0).astype(np.int8)
    cel = celda_3grados(g.punto_lat, g.punto_lon)
    tws = tws_desde_almacenamiento(alm, cel)
    # Rodell solo en su periodo observado (2002-2016): plana antes y después, sin extender a 2026; anomalía respecto de 2004-2009
    anios = np.clip(np.arange(tws.shape[1]), RODELL_MES[0], RODELL_MES[1]) / 12.0
    tws = tws + tendencia_rodell_cm_anio(g.punto_lat, g.punto_lon)[:, None] * (anios - anios[BASE_GRACE].mean())[None, :]
    tws, tfrac, b_gr = aplicar_cobertura(tws, "grace")
    bm = np.where(fuente == 1, bandera_mes("gldas")[None], np.where(fuente == 3, bandera_mes("smap_l3")[None],
                                                                    bandera_mes("smap_l4")[None]))
    return Agua(sm_sup, sm_raiz, err, fuente, qual, frac, tws, err_tws(tws, MASCON_SIGMA_CM),
                np.broadcast_to(tfrac, tws.shape).copy(), et, bm | b_gr[None, :])
