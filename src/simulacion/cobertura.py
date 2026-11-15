# asistido por SI: Claude Code (Anthropic), escritura y revisión de código; base del prototipo migrada en el hackatón
"""Cobertura IGBP simulada (D-010): MCD12C1 no se descargó, así que se deriva de Köppen, elevación, latitud y suelo.

Todas las reglas son SUPUESTO (revisión 2026-11-13), sin ficha EV-*. La Task 8 (suelo.py) la reutiliza.
IGBP: 1 ENF, 2 EBF, 3 DNF, 4 DBF, 5 MF, 6 arbustal cerrado, 7 arbustal abierto, 8 sabana leñosa, 9 sabana,
10 pastizal, 11 humedal, 12 cultivo, 13 urbano, 14 mosaico cultivo-vegetación, 15 nieve/hielo, 16 árido, 17 agua.
"""
import sqlite3
from pathlib import Path

import numpy as np
import pandas as pd

from simulacion.azar import rng_unidad
from simulacion.clima import _COD, _IDX, _clase_respaldo, _t_anual

COLS = [f"igbp_{i}" for i in range(1, 18)]
_NOMBRES = [_COD[n] for n in sorted(_COD)]  # código Köppen por índice 0..29


def _natural(cod: str) -> dict[int, float]:
    # SUPUESTO: mezcla natural por clase Köppen (fracciones relativas; se normalizan)
    if cod == "EF":
        return {15: .95, 16: .05}
    if cod == "ET":
        return {16: .3, 10: .4, 7: .3}
    if cod in ("BWh", "BWk"):
        return {16: .85, 7: .15}
    if cod[0] == "B":
        return {10: .45, 7: .35, 6: .1, 16: .1}
    if cod in ("Af", "Am"):
        return {2: .85, 4: .05, 9: .05, 11: .05}
    if cod == "Aw":
        return {9: .45, 8: .25, 10: .15, 4: .1, 11: .05}
    if cod[0] == "C":
        return {8: .3, 6: .3, 5: .2, 10: .2} if cod[1] == "s" else {5: .35, 4: .2, 1: .15, 10: .15, 6: .15}
    if cod[-1] in "cd":
        return {3: .3, 1: .35, 10: .2, 6: .15}
    return {5: .35, 4: .2, 1: .2, 10: .25}


# SUPUESTO: potencial de cultivo del clima (fracción máxima de la unidad) antes del factor de suelo
_CULTIVO = dict(Cfa=.55, Dfa=.55, BSk=.4, Cfb=.3, Dfb=.25, Cwa=.4, Aw=.25, Csa=.25, BSh=.15, Dwa=.3, Cwb=.15)
_TAB = np.zeros((30, 17))
for _c, _i in _IDX.items():
    for _k, _v in _natural(_c).items():
        _TAB[_i, _k - 1] = _v
_POT = np.array([_CULTIVO.get(c, .05 if c[0] in "ACD" else 0.0) for c in _NOMBRES])
_POT[[_IDX[c] for c in ("EF", "ET", "BWh", "BWk")]] = 0


def _rampa(x, a, b, c, d):
    return np.clip(np.minimum((x - a) / (b - a), (d - x) / (d - c)), 0, 1)


def _aptitud(est: pd.DataFrame | None, ids) -> np.ndarray:
    # SUPUESTO: pH 5,5-8, arcilla 10-60 % y arena < 85 % dan aptitud 1; fuera baja a 0; sin dato, 0,7
    if est is None:
        return np.full(len(ids), 0.7)
    e = est.reindex(ids)
    s = (_rampa(e.phh2o.to_numpy(float), 4, 5.5, 8, 9.5) * _rampa(e.clay.to_numpy(float), 0, 10, 60, 85)
         * _rampa(e.sand.to_numpy(float), -1, 0, 85, 95))
    return np.where(np.isnan(s), 0.7, s)


def _paramo(elev):
    m = np.zeros((len(elev), 17))
    m[:, 9], m[:, 6], m[:, 15] = .6, .3, .1
    roca = elev >= 4700  # nieve y roca
    m[roca] = 0
    m[roca, 14], m[roca, 15] = .5, .5
    return m


def cobertura_simulada(unidades: pd.DataFrame, koppen_moda, estatico: pd.DataFrame | None = None) -> pd.DataFrame:
    """Fracciones igbp_1..igbp_17 (suman 1) y igbp_dominante por unidad. koppen_moda: 1..30, -1 sin Köppen.

    estatico: DataFrame con índice de unidad y columnas phh2o, clay, sand (0-30 cm); None si no hay.
    """
    ids = list(unidades.index)
    lat = unidades.punto_lat.to_numpy(float)
    elev = np.nan_to_num(unidades.elev_media.to_numpy(float))
    k = np.asarray(koppen_moda, int) - 1
    k = np.where(k < 0, _clase_respaldo(_t_anual(lat, elev), lat), k)
    nat = _TAB[k].copy()
    trop = np.abs(lat) < 23.5
    # SUPUESTO: alta montaña tropical, páramo/pastizal desde 3.000 m y nieve/roca desde 4.700 m
    alto = trop & (elev >= 3000)
    nat[alto] = _paramo(elev[alto])
    # SUPUESTO: bosque tropical se aclara entre 1.500 y 3.000 m (pasa a caducifolio)
    af = (k <= 1) & (elev >= 1500) & ~alto
    nat[af, 3] += 0.3 * nat[af, 1] / .85
    nat[af, 1] *= 0.65
    # SUPUESTO: sobre 4.500 m fuera del trópico, roca y nieve
    fria = ~trop & (elev > 4500)
    nat[fria] = 0
    nat[fria, 15], nat[fria, 14] = .6, .4
    c = _POT[k] * _aptitud(estatico, ids) * (elev < 3500) * ~alto
    # azar determinista por unidad: factor lognormal sobre la mezcla natural
    z = np.stack([rng_unidad(u, "cobertura").standard_normal(17) for u in ids]) if ids else np.zeros((0, 17))
    nat = nat * np.exp(0.2 * z)
    nat /= nat.sum(1, keepdims=True)
    f = nat * (1 - c)[:, None]
    f[:, 11] += 0.7 * c
    f[:, 13] += 0.3 * c
    out = pd.DataFrame(f, index=unidades.index, columns=COLS)
    out["igbp_dominante"] = f.argmax(1) + 1
    return out


def cargar_suelo(ruta, ids=None) -> pd.DataFrame:
    """phh2o, clay y sand (0-30 cm) desde geo.sqlite (solo lectura), con el respaldo si está incompleto."""
    ruta = Path(ruta)
    for r in (ruta, ruta.with_name(ruta.name + ".bak_prereconstruccion")):
        try:
            con = sqlite3.connect(f"file:{r.as_posix()}?mode=ro", uri=True)
            try:
                d = pd.read_sql("SELECT unidad_id, variable_id, media FROM estatico WHERE variable_id IN "
                                "('phh2o_0_30','clay_0_30','sand_0_30')", con)
            finally:
                con.close()
        except sqlite3.Error:
            continue
        if d.empty:
            continue
        w = d.pivot(index="unidad_id", columns="variable_id", values="media")
        w.columns = [c.removesuffix("_0_30") for c in w.columns]
        return w if ids is None else w.reindex(list(ids))
    raise FileNotFoundError(f"sin suelo en {ruta} ni su respaldo")
