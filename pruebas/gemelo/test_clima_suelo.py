# asistido por SI: Cursor (agente), escritura y revisión de código; núcleo del gemelo digital en el hackatón
import numpy as np
import pytest

from gemelo.clima import (DIAS_MES, desagregar_mensual, eto_hargreaves, eto_penman_monteith,
                          radiacion_extraterrestre)
from gemelo.suelo import (coef_drenaje, escorrentia_scs, grupo_hidrologico, numero_curva_efectivo, numeros_curva,
                          saxton_rawls)


def test_radiacion_extraterrestre_ejemplo_8_fao56():
    # FAO-56, ejemplo 8: 20° S, 3 de septiembre (J = 246) -> Ra = 32,2 MJ/m²/día
    assert radiacion_extraterrestre(-20.0, 246) == pytest.approx(32.2, abs=0.05)


def test_eto_penman_monteith_ejemplo_18_fao56():
    # FAO-56, ejemplo 18: Bruselas, 6 de julio -> ET0 = 3,9 mm/día
    eto = eto_penman_monteith(21.5, 12.3, 22.07, 50.8, 187, 100.0, ea=1.409, u2=2.078)
    assert eto == pytest.approx(3.9, abs=0.05)


def test_hargreaves_mismo_orden_que_penman_monteith():
    pm = eto_penman_monteith(30.0, 18.0, 22.0, 10.0, 100, 200.0, rh=60.0, u2=2.0)
    hs = eto_hargreaves(30.0, 18.0, 24.0, 10.0, 100)
    assert 0.6 < hs / pm < 1.4


def test_power_real_calendario_nominal(clima_ames):
    assert clima_ames.datos["precip"].shape == (clima_ames.n_anios, 365)
    assert clima_ames.naturaleza == "estimado"
    assert 500 < clima_ames.precip_anual().mean() < 1200
    assert clima_ames.elevacion_m == pytest.approx(310.22)


def test_desagregacion_conserva_lluvia_mensual():
    rng = np.random.default_rng(0)
    mensual = {"precip": rng.uniform(0, 250, (3, 12)), "t2m": np.full((3, 12), 20.0),
               "t2m_max": np.full((3, 12), 26.0), "t2m_min": np.full((3, 12), 14.0), "rad_sw": np.full((3, 12), 18.0)}
    c = desagregar_mensual(mensual, [2001, 2002, 2003], 5.0, 100.0, semilla=1)
    ini = np.concatenate([[0], np.cumsum(DIAS_MES)])
    sumas = np.stack([c.datos["precip"][:, ini[m]:ini[m + 1]].sum(1) for m in range(12)], axis=1)
    np.testing.assert_allclose(sumas, mensual["precip"], rtol=1e-12)
    assert c.naturaleza == "derivado"
    np.testing.assert_allclose(c.datos["t2m"], 20.0)


def test_saxton_rawls_arena_como_tabla_publicada():
    # Saxton y Rawls (2006): arena (5 % arcilla, 88 % arena, 2,5 % MO) -> PMP 5 %, CC 10 %, Sat 46 %, Ksat 108 mm/h
    r = saxton_rawls(0.88, 0.05, 2.5)
    assert r["theta_pmp"] == pytest.approx(0.05, abs=0.01)
    assert r["theta_cc"] == pytest.approx(0.10, abs=0.01)
    assert r["theta_sat"] == pytest.approx(0.46, abs=0.01)
    assert r["ksat_mm_h"] == pytest.approx(108.0, rel=0.05)


def test_saxton_rawls_monotonia_y_dominio():
    franco, arcilla = saxton_rawls(0.40, 0.20, 2.5), saxton_rawls(0.25, 0.50, 2.5)
    assert arcilla["theta_pmp"] > franco["theta_pmp"] and arcilla["ksat_mm_h"] < franco["ksat_mm_h"]
    assert bool(saxton_rawls(0.4, 0.2, 12.0)["fuera_dominio"])
    assert not bool(franco["fuera_dominio"])


def test_escorrentia_scs_valor_conocido():
    # P = 50 mm, CN = 80: S = 63,5; Ia = 12,7; Q = 37,3² / (37,3 + 63,5) = 13,8 mm
    assert escorrentia_scs(50.0, 80.0) == pytest.approx(13.80, abs=0.01)
    assert escorrentia_scs(10.0, 80.0) == 0.0


def test_numero_curva_y_drenaje():
    cn = numeros_curva("B")
    assert numero_curva_efectivo(cn, 1.0, 0.0) == cn["cultivo"]
    assert numero_curva_efectivo(cn, 0.0, 0.0) == cn["desnudo"]
    assert numero_curva_efectivo(cn, 0.0, 1.0) == cn["residuo"]
    assert grupo_hidrologico(108.0) == "A" and grupo_hidrologico(1.0) == "D"
    assert 0 < coef_drenaje(1.0) < coef_drenaje(50.0) <= 1.0


def test_perfil_soilgrids_ames(suelo_ames):
    assert 80 < suelo_ames.valor("cos_t_ha") < 120
    assert suelo_ames.valor("theta_pmp") < suelo_ames.valor("theta_cc") < suelo_ames.valor("theta_sat")
    assert suelo_ames["arcilla"].rango[0] <= suelo_ames.valor("arcilla") <= suelo_ames["arcilla"].rango[1]


def test_perfil_ipiales_avisa_fuera_de_dominio():
    from gemelo.suelo import perfil_desde_soilgrids
    from conftest import REF
    p = perfil_desde_soilgrids(REF / "suelo" / "soilgrids_ipiales.json")
    assert any("fuera de dominio" in a for a in p.avisos)
    calibrado = p.calibrar(mo_pct=5.0)
    assert not any("fuera de dominio" in a for a in calibrado.avisos)
    assert calibrado["mo_pct"].naturaleza == "observado"
    medido = p.calibrar(mo_pct=5.0, theta_cc=0.48)
    assert medido.valor("theta_cc") == 0.48 and medido["theta_cc"].rango is None
    with pytest.raises(KeyError):
        p.calibrar(color=3)
