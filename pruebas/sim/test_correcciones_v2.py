# asistido por SI: Claude Code (Anthropic), escritura y revisión de código; base del prototipo migrada en el hackatón
"""Correcciones tras V2 (fase 2): un fallo, una prueba. Sin datos reales."""
import sqlite3

import numpy as np
import pandas as pd
import pytest

from simulacion import agua as ag, clima, config, suelo as sl, vegetacion as vg
from simulacion import escribir_sqlite as esc
from simulacion.tiempo import dias_del_mes, mes_id
from simulacion.variables import VARIABLES, a_entero

N = config.N_MESES
NOV26 = mes_id(2026, 11)
GEO = pd.DataFrame([("U0", "IND", 29.0, 75.0, 200.0, 14), ("U1", "FRA", 45.0, 2.0, 100.0, 14),
                    ("U2", "BRA", -10.0, -50.0, 300.0, 1), ("U3", "AZE", 41.0, 49.0, 0.0, 4)],
                   columns=["id", "iso3", "punto_lat", "punto_lon", "elev_media", "koppen"]).set_index("id")
IDS = list(GEO.index)


def test_a_mm_h_mes_parcial():  # fallo 1
    tasa = 0.126
    frac = np.ones((1, N)); frac[0, NOV26] = 5 / 30
    mm = np.full((1, N), tasa) * np.array([dias_del_mes(m) * 24 for m in range(N)]) * frac
    h = esc.a_mm_h(mm, frac)
    assert h[0, NOV26] == pytest.approx(tasa) and h[0, 0] == pytest.approx(tasa)


def test_mensual_desde_base_precip_mm_mes():  # fallo 2: ruta de escribir_lotes
    con = sqlite3.connect(":memory:")
    con.execute("CREATE TABLE mensual(unidad_id, mes_id, ndvi, sm_raiz, precip, dias_helada)")
    v = VARIABLES["precip"]
    p = a_entero(np.full(N, 0.5), v)  # 0,5 mm/h
    con.executemany("INSERT INTO mensual VALUES('U',?,5000,300,?,0)", [(m, int(p[m])) for m in range(N)])
    mu = esc._mensual_desde_base(con, ["U"])["U"]["precip"]
    assert mu[0] == pytest.approx(0.5 * 31 * 24, rel=0.01)  # enero: 372 mm/mes


def test_suelo_metodo_sin_nbr2():  # fallo 3
    _, m = sl.dias_suelo_mensual(np.full((2, N), 0.5), None)
    assert (m == 1).all()


def _agua(parchar=False, monkeypatch=None):
    c = clima.generar_clima(IDS, slice(None), geo=GEO)
    nd = vg.generar_ndvi(c, slice(None), GEO)
    return c, ag.generar_agua(c, nd, slice(None), geo=GEO)


def test_rodell_plana_tras_2016_y_sin_caspio(monkeypatch):  # fallo 4
    assert ag.tendencia_rodell_cm_anio([41.0], [49.0])[0] == 0  # caja del Caspio excluida
    assert ag.tendencia_rodell_cm_anio([29.0], [75.0])[0] < 0   # N India sigue
    con = _agua()[1].tws
    monkeypatch.setattr(ag, "tendencia_rodell_cm_anio", lambda la, lo: np.zeros(len(la)))
    sin = _agua()[1].tws
    d = (con - sin)[0]  # unidad de N India: solo la tendencia
    a, b = mes_id(2017, 1), mes_id(2025, 12)
    assert np.nanmax(np.abs(d[a:b] - d[a])) < 1e-9 and abs(d[a]) > 5
    assert abs(d[mes_id(2010, 1)] - d[a]) > 5


def test_enso_sur_eeuu_djf_y_adm1():  # fallo 5
    r = np.ones(N)
    llu, _ = clima.forzante_enso("Sur de EE. UU.", r)
    m = np.arange(N) % 12 + 1
    assert (llu[np.isin(m, (12, 1, 2))] != 0).all() and (llu[~np.isin(m, (12, 1, 2))] == 0).all()
    reg = np.array([None, None], dtype=object)
    out = clima._enso_por_adm1(reg, np.array(["USA", "USA"]), np.array(["Texas", "Maine"], dtype=object))
    assert out[0] == "Sur de EE. UU." and out[1] is None
    assert clima._REGION["USA"]["enso"] is None


def test_sm_sup_dinamica_propia():  # fallo 6
    _, a = _agua()
    ok = ~np.isnan(a.sm_sup[1]) & ~np.isnan(a.sm_raiz[1])
    assert np.corrcoef(a.sm_sup[1][ok], a.sm_raiz[1][ok])[0, 1] < 0.99
    assert (np.abs(a.sm_sup - a.sm_raiz) > 1e-6).mean() > 0.5
