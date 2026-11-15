# asistido por SI: Claude Code (Anthropic), escritura y revisión de código; base del prototipo migrada en el hackatón
import numpy as np
import pandas as pd
import pytest

from simulacion import agua as ag, clima, config, vegetacion as vg
from simulacion.productos import fraccion_dias
from simulacion.tiempo import mes_id

N = config.N_MESES
# koppen: Dfa=25, Cfa=14, Af=1, BWh=4. Latitudes separadas más de 3° (celdas distintas) salvo VEC1/VEC2
FILAS = [("A0", "USA", 41.0, -100.0, 250.0, 25), ("A1", "BRA", -3.0, -60.0, 80.0, 1), ("A2", "EGY", 25.0, 30.0, 200.0, 4),
         ("A3", "CHN", 32.0, 110.0, 50.0, 14), ("VEC1", "IND", 20.1, 78.1, 100.0, 14), ("VEC2", "IND", 20.9, 78.9, 100.0, 14),
         ("LEJ", "IND", 20.5, 85.0, 100.0, 14)]
FILAS += [("B%d" % i, "FRA", 30.0 + i * 0.1, 2.0, 100.0, 14) for i in range(43)]
GEO = pd.DataFrame(FILAS, columns=["id", "iso3", "punto_lat", "punto_lon", "elev_media", "koppen"]).set_index("id")
IDS = list(GEO.index)
SM = slice(None)


@pytest.fixture(scope="module")
def sim():
    c = clima.generar_clima(IDS, SM, geo=GEO)
    nd = vg.generar_ndvi(c, SM, GEO)
    return c, nd, ag.generar_agua(c, nd, SM, geo=GEO)


def _entradas(n=50):
    rng = np.random.default_rng(1)
    p = rng.gamma(2, 40, (n, N))
    return p, rng.uniform(20, 150, (n, N)), rng.uniform(.2, 1.1, (n, N)), rng.uniform(.3, .55, n)


def test_balance_cierra():
    p, eto, kc, por = _entradas()
    s0 = .5 * por * ag.PROF_RAIZ_MM
    alm, et, q = ag.balance_hidrico(p, eto, kc, por, s0)
    ds = np.diff(np.concatenate([s0[:, None], alm], 1), axis=1)
    assert np.abs(p - et - q - ds).max() < 1e-6
    assert (et >= 0).all() and (q >= 0).all() and (alm <= por[:, None] * ag.PROF_RAIZ_MM + 1e-9).all()


def test_balance_anual_tolerancia(sim):
    c, _, a = sim
    # dS anual de GRACE: dic a dic (2003-2010, sin huecos); escorrentía es el residuo del cubo
    idx = [mes_id(y, 12) for y in range(2002, 2011)]
    uni = [IDS.index(i) for i in ("A0", "A1", "A2", "A3")]  # celdas distintas
    ds = np.diff(a.tws[uni][:, idx] * 10, axis=1)
    sl = [slice(idx[k] + 1, idx[k + 1] + 1) for k in range(len(idx) - 1)]
    P = np.stack([c.precip[uni][:, s].sum(1) for s in sl], 1)
    E = np.stack([a.et_real[uni][:, s].sum(1) for s in sl], 1)
    assert (np.abs(P - E - ds) / P).mean() < 0.15 or (np.abs(P - E - ds).sum() / P.sum()) < 0.15


def test_sm_fuente_empalme(sim):
    f = sim[2].sm_fuente
    assert (f[:, :mes_id(2015, 2) + 1] == 1).all()
    assert np.isin(f[:, mes_id(2015, 3)], [2, 3]).all()
    assert (f[:, mes_id(2015, 4):] != 1).all()


def test_sm_huecos_l3(sim):
    a = sim[2]
    m = mes_id(2019, 7)
    assert 0 < fraccion_dias("smap_l3")[m] < 1
    assert (a.sm_fuente[:, m] == 2).all() and not np.isnan(a.sm_sup[:, m]).any()
    assert all((a.sm_fuente[:, mes_id(y, k)] == 2).all() for y, k in ((2022, 8), (2022, 9)))
    assert (a.sm_fuente[:, mes_id(2019, 6)] == 3).all()
    h = ag.humedad_por_fuente(np.full((1, N), .3), np.where(np.arange(N) == mes_id(2019, 7), 0, 1.0), np.ones(N))[1]
    assert h[0, mes_id(2019, 7)] == 2 and h[0, mes_id(2019, 8)] == 3


def test_sm_rangos(sim):
    a = sim[2]
    por = ag.porosidad_suelo(np.full(len(IDS), np.nan), sim[1]["igbp_dominante"])[0]
    s3, s2, s1 = a.sm_fuente == 3, a.sm_fuente == 2, a.sm_fuente == 1
    assert (a.sm_sup[s3] >= .02 - 1e-12).all() and (a.sm_sup <= np.where(s3, por[:, None], .9) + 1e-12)[s3].all()
    assert (a.sm_sup[s2] >= 0).all() and (a.sm_sup[s2] <= .9).all()
    assert (a.sm_sup[s1] * 100 <= 60).all() and (a.sm_sup[s1] >= 0).all()


def test_sesgo_empalme_pendiente(sim):
    assert ag.SESGO_EMPALME is None and sim[2].metadatos["empalme_gldas_smap_sesgo"] == "PENDIENTE"
    x = ag.humedad_por_fuente(np.full((1, N), .3), np.ones(N), np.ones(N), sesgo=0.05)[0]
    assert x[0, 0] == .3 and abs(x[0, mes_id(2016, 1)] - .35) < 1e-12


def test_gldas_no_pasa_de_2015(sim):
    assert not (sim[2].sm_fuente[:, mes_id(2015, 4):] == 1).any()


def test_grace_huecos_nulos(sim):
    a = sim[2]
    sin = fraccion_dias("grace") == 0
    assert np.isnan(a.tws[:, sin]).all() and (a.tws_frac[:, sin] == 0).all()
    assert not np.isnan(a.tws[:, ~sin]).any()
    assert sin[:mes_id(2002, 3) + 1].all() and sin.sum() >= 33 + 27  # 33 huecos + antes de abril 2002 + final 2026


def test_grace_es_gruesa(sim):
    a = sim[2]
    i, j = IDS.index("VEC1"), IDS.index("VEC2")
    ok = ~np.isnan(a.tws[i])
    assert np.allclose(a.tws[i, ok], a.tws[j, ok])
    assert not np.allclose(a.tws[i, ok], a.tws[IDS.index("LEJ"), ok])  # celda distinta


def test_grace_sin_deriva(sim):
    a = sim[2]
    ok = ~np.isnan(a.tws[0])
    ok[:ag.RODELL_MES[0]] = ok[ag.RODELL_MES[1] + 1:] = False  # Rodell solo rige en su periodo (2002-2016)
    t = np.arange(N)[ok] / 12
    pend = [np.polyfit(t, f[ok], 1)[0] for f in a.tws]
    # la única tendencia permitida es la de Rodell (cm/año) donde la unidad cae en su caja
    g = GEO.iloc[SM]
    esperada = ag.tendencia_rodell_cm_anio(g.punto_lat, g.punto_lon)
    assert np.abs(np.array(pend) - esperada).max() < 0.3  # ventana corta de 15 años: el azar mueve la pendiente ~0,2


def test_celdas():
    c = ag.celda_3grados([20.1, 20.9, 23.5], [78.1, 78.9, 78.1])
    assert c[0] == c[1] and c[0] != c[2]

def test_grace_tendencia_rodell():
    from simulacion.referencias.cargar import cargar_rodell
    r = cargar_rodell()
    assert len(r) == 34 and not r.cm_anio.isna().any()
    # N India (-2,89 cm/año) cae en su caja; el hielo y el mar abierto no reciben tendencia
    t = ag.tendencia_rodell_cm_anio([29.0, 75.0, -2.0], [75.0, -60.0, -150.0])
    assert t[0] == pytest.approx(-2.89) and t[1] == 0 and t[2] == 0


def test_sm_err(sim):
    a = sim[2]
    assert (a.sm_err[a.sm_fuente == 2] > 0).all()
    assert np.allclose(a.sm_err[a.sm_fuente != 2], 0.04) and (a.sm_qual[a.sm_fuente != 2] == 0).all()


def test_porosidad():
    p, nulo = ag.porosidad_suelo([1.325, np.nan], [1, 12])
    assert abs(p[0] - .5) < 1e-9 and nulo.tolist() == [False, True] and p[1] == ag.POROSIDAD_RESPALDO_IGBP[11]


def test_integracion_et(sim):
    c, nd, a = sim
    r = vg.empaquetar_et_lst(c, a, SM, GEO, ndvi=nd)
    et = r["et"]
    assert np.nanmin(et) >= 0 and np.nanmax(et) <= vg.ET_MAX_8D
    assert 0 < np.nanmean(et) < 60  # kg/m²/8 días: medias de 0-7 mm/día
    assert 0 < np.nanmean(a.et_real) < 300  # mm/mes


SIN_GEO_PROTOTIPO = pytest.mark.skip(reason="depende de geo.sqlite del prototipo, que D-003 no importa; sale con el generador simulado, decisión i")


@SIN_GEO_PROTOTIPO
@pytest.mark.datos_reales
def test_datos_reales_colombia():
    geo = clima.cargar_geo()
    col = geo[geo.iso3 == "COL"]
    ids = list(col.index)
    c = clima.generar_clima(ids, SM, geo=col)
    nd = vg.generar_ndvi(c, SM, col)
    a = ag.generar_agua(c, nd, SM, geo=col)
    assert not np.isnan(a.sm_sup).any() and (a.sm_sup > 0).all()
    assert (a.sm_fuente[:, 0] == 1).all() and np.isin(a.sm_fuente[:, -1], [2, 3]).all()
