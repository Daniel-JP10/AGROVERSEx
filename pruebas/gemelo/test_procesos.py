# asistido por SI: Cursor (agente), escritura y revisión de código; núcleo del gemelo digital en el hackatón
"""Pruebas de cada proceso por separado: agua, fenología, cobertura, biomasa, nitrógeno y carbono."""
import numpy as np
import pytest

from gemelo import agua, biomasa, carbono, cobertura, nitrogeno
from gemelo.fenologia import cobertura_potencial, fraccion_raiz, pesos_kc


def test_coef_estres_fao56():
    # A = 100 mm disponibles, RAW = 50: sin estrés hasta agotar 50 mm; a 75 mm agotados Ks = 0,5
    assert agua.coef_estres(80.0, 100.0, 0.0, 50.0) == 1.0
    assert agua.coef_estres(25.0, 100.0, 0.0, 50.0) == pytest.approx(0.5)
    assert agua.coef_estres(0.0, 100.0, 0.0, 50.0) == 0.0
    assert agua.coef_estres(120.0, 100.0, 0.0, 50.0) == 1.0


def test_p_ajustado_fao56():
    assert agua.p_ajustado(0.55, 5.0) == pytest.approx(0.55)
    assert agua.p_ajustado(0.55, 8.0) == pytest.approx(0.43)
    assert agua.p_ajustado(0.1, 10.0) == 0.1


def test_redistribuir_conserva_agua():
    w1, w2 = np.array([30.0, 80.0]), np.array([200.0, 150.0])
    a, b = agua.redistribuir(w1, w2, np.array([0.1, 0.8]), np.array([0.5, 0.1]), 1.0)
    np.testing.assert_allclose(a + b, w1 + w2)
    assert a[0] > w1[0] and a[1] < w1[1]


def test_riego_respeta_tope_y_umbral():
    neto, bruto = agua.riego_automatico(np.array([True, True, False]), np.array([40.0, 90.0, 40.0]), 100.0, 30.0,
                                        1.0, np.array([0.0, 0.0, 0.0]), np.array([np.inf, np.inf, np.inf]), 0.75)
    np.testing.assert_allclose(neto, [60.0, 0.0, 0.0])
    np.testing.assert_allclose(bruto, [80.0, 0.0, 0.0])
    neto, bruto = agua.riego_automatico(np.array([True]), np.array([40.0]), 100.0, 30.0, 1.0, np.array([50.0]),
                                        np.array([70.0]), 0.75)
    assert bruto[0] == pytest.approx(20.0) and neto[0] == pytest.approx(15.0)


def test_drenaje_subpasos_equivalente_sin_otros_flujos():
    w, wcc, tau = 150.0, 100.0, 0.4
    un_paso = w - agua.drenaje(w, wcc, tau)
    ts = agua.tau_subpaso(tau, 4)
    x = w
    for _ in range(4):
        x -= agua.drenaje(x, wcc, ts)
    assert x == pytest.approx(un_paso)


def test_curva_kc_fao56():
    etapas = (30, 40, 50, 30)
    d = np.arange(150)
    wi, wm, we = pesos_kc(d, etapas)
    np.testing.assert_allclose(wi + wm + we, 1.0)
    kc = wi * 0.3 + wm * 1.2 + we * 0.475
    assert kc[0] == pytest.approx(0.3) and kc[29] == pytest.approx(0.3)
    assert kc[69] == pytest.approx(1.2) and kc[100] == pytest.approx(1.2)
    assert kc[149] == pytest.approx(0.475)
    assert np.all(np.diff(kc[30:70]) > 0)
    assert fraccion_raiz(np.array([0, 35, 70, 120]), etapas).tolist() == pytest.approx([0, 0.5, 1, 1])


def test_cobertura_potencial_ec76():
    assert cobertura_potencial(0.15, 0.15, 1.2, 2.0) == 0.0
    assert cobertura_potencial(1.2, 0.15, 1.2, 2.0) == pytest.approx(1.0)
    assert 0 < cobertura_potencial(0.6, 0.15, 1.2, 2.0) < cobertura_potencial(0.6, 0.15, 1.2, 0.3)


def test_cobertura_con_estres_se_atrasa():
    v = cobertura.actualizar_cobertura(np.array([0.2, 0.2]), 0.5, 0.3, np.array([1.0, 0.5]))
    np.testing.assert_allclose(v, [0.4, 0.3])
    assert cobertura.actualizar_cobertura(0.8, 0.5, 0.6, 1.0) == pytest.approx(0.5)


def test_funcion_beta_temperatura():
    assert biomasa.f_temperatura(30.0, 8.0, 30.0, 42.0) == pytest.approx(1.0)
    assert biomasa.f_temperatura(8.0, 8.0, 30.0, 42.0) == 0.0
    assert biomasa.f_temperatura(43.0, 8.0, 30.0, 42.0) == 0.0
    assert 0 < biomasa.f_temperatura(15.0, 8.0, 30.0, 42.0) < 1


def test_cosecha_conserva_masa():
    rend, res, nexp, nres = biomasa.cosecha(np.array([10000.0, 5000.0]), np.array([150.0, 90.0]), 0.5, 0.7,
                                            np.array([True, False]))
    np.testing.assert_allclose(rend + res, [10000.0, 5000.0])
    np.testing.assert_allclose(nexp + nres, [150.0, 90.0])
    assert rend[1] == 0 and nexp[1] == 0


def test_limitacion_por_n_y_fijacion():
    # Sin leguminosa: el suelo limita el crecimiento
    db, u, fx, fn = nitrogeno.limitar_por_n(100.0, 0.02, 0.0, 1.0)
    assert fn == pytest.approx(0.5) and u == pytest.approx(1.0) and fx == 0 and db == pytest.approx(50.0)
    # Leguminosa con suelo pobre: la fijación compensa hasta ndfa_max
    db, u, fx, fn = nitrogeno.limitar_por_n(100.0, 0.03, 0.5, 0.0, ndfa_max=0.9)
    assert fn == pytest.approx(0.9) and u == 0 and fx == pytest.approx(2.7)
    db, u, fx, fn = nitrogeno.limitar_por_n(100.0, 0.03, 0.5, 10.0, ndfa_max=0.9)
    assert fn == 1 and u == pytest.approx(1.5) and fx == pytest.approx(1.5)
    assert u + fx == pytest.approx(0.03 * db)


def test_icbm_conserva_c_y_n_e_inmoviliza_con_limite():
    y, o, yn, n = np.array([2.0]), np.array([60.0]), np.array([30.0]), np.array([0.0])
    k1, k2, h, cn = 0.8 / 365, 0.006 / 365, 0.125, 10.0
    y2, o2, yn2, n2, resp, neto, s = carbono.paso_icbm(y, o, yn, n, k1, k2, h, 1.0, cn)
    assert y2 + o2 + resp == pytest.approx(y + o)
    n_org = lambda yn_, o_: yn_ + o_ * 1000 / cn
    assert n_org(yn2, o2) + n2 == pytest.approx(n_org(yn, o) + n)
    assert n2 >= 0
    # Residuo pobre en N (C:N 100), sin N mineral ni humus que mineralice: la descomposición se frena
    _, _, _, n3, _, _, s3 = carbono.paso_icbm(np.array([2.0]), np.array([0.0]), np.array([20.0]), np.array([0.0]),
                                              k1, k2, h, 1.0, cn)
    assert s3[0] < 1 and n3[0] >= -1e-12


def test_icbm_decaimiento_exponencial_con_r_constante():
    y, o, yn, n = np.array([1.0]), np.array([0.0]), np.array([0.0]), np.array([1e6])
    k1 = 0.8 / 365
    for _ in range(365):
        y, o, yn, n, *_ = carbono.paso_icbm(y, o, yn, n, k1, 0.0, 0.0, 1.0, 10.0)
    assert float(y[0]) == pytest.approx(np.exp(-0.8), rel=1e-3)


def test_factor_clima_normalizado():
    assert carbono.factor_clima(5.5, 1.0, -3.8, 30.0, 5.5) == pytest.approx(1.0)
    assert carbono.factor_clima(25.0, 1.0, -3.8, 30.0, 5.5) > 5
    assert carbono.factor_clima(25.0, 0.0, -3.8, 30.0, 5.5) == 0.0


def test_lixiviacion_acotada():
    assert nitrogeno.lixiviacion(50.0, 0.0, 300.0) == 0
    assert nitrogeno.lixiviacion(50.0, 300.0, 300.0) == pytest.approx(25.0)
    assert nitrogeno.lixiviacion(50.0, 1e9, 0.0) <= 50.0
