# asistido por SI: Cursor (agente), escritura y revisión de código; núcleo del gemelo digital en el hackatón
"""Propiedades del sistema acoplado: conservación de masa, límites físicos, convergencia, reproducibilidad."""
import numpy as np
import pytest

from conftest import clima_constante, maiz_continuo, maiz_soya
from gemelo.escenarios import construir
from gemelo.modelos import Estrategia, Riego, Temporada, dia_nominal
from gemelo.simulador import ejecutar, resumir_estrategias


def _cierres(ens):
    reg, ini = ens.reg, ens.reg["inicial"]
    cn = ens.reg["_cn_suelo"] if "_cn_suelo" in reg else None
    w_prev = np.concatenate([ini["W"][:, None], reg["W"][:, :-1]], axis=1)
    agua = np.abs(reg["W"] - w_prev - (reg["P"] + reg["I_neto"] - reg["ETa"] - reg["R"] - reg["D"])).max()
    carbono = np.abs(reg["C"][:, -1] - ini["C"] - (reg["c_entrada"].sum(1) - reg["resp"].sum(1))).max()
    return agua, carbono, cn


def _n_total(ens, t=None):
    reg, ini = ens.reg, ens.reg["inicial"]
    cn = np.tile(ens.theta.ts["cn_suelo"], ens.S * ens.K)
    if t is None:
        return ini["N"] + ini["Y_N"] + ini["O"] * 1000 / cn
    return reg["N"][:, t] + reg["Y_N"][:, t] + reg["O"][:, t] * 1000 / cn + reg["N_planta"][:, t]


@pytest.fixture(scope="module")
def ens_ames(clima_ames, suelo_ames):
    esc = construir(clima_ames, "historico", 2, max_miembros=4)
    riego = Riego("automatico", tope_mm=150.0)
    estrategias = [maiz_continuo(2), maiz_soya(2), maiz_continuo(2, riego=riego)]
    return ejecutar(clima_ames, esc, suelo_ames, estrategias, n_parametros=3, semilla=7)


def test_conservacion_agua_carbono_nitrogeno(ens_ames):
    agua, carbono, _ = _cierres(ens_ames)
    assert agua < 1e-9
    assert carbono < 1e-9
    reg = ens_ames.reg
    entradas = reg["fert_suelo"].sum(1) + reg["fijacion"].sum(1)
    salidas = reg["L_lix"].sum(1) + reg["N_export"].sum(1)
    delta = _n_total(ens_ames, -1) - _n_total(ens_ames)
    np.testing.assert_allclose(delta, entradas - salidas, atol=1e-6)


def test_limites_fisicos(ens_ames):
    reg = ens_ames.reg
    for k in ("W", "N", "C", "B", "Y_N", "O", "D", "R", "ETa", "L_lix", "U", "fijacion"):
        assert reg[k].min() >= -1e-9, k
    for k in ("V", "f_residuo", "desnudo", "agua_raiz"):
        assert reg[k].min() >= -1e-12 and reg[k].max() <= 1 + 1e-12, k
    assert np.all(reg["K"] <= 1 + 1e-12)
    assert np.all(reg["ETa"] <= reg["ETc"] + 1e-9)


def test_riego_reduce_estres_y_respeta_tope(ens_ames):
    r = {e["id"] + str(i): e for i, e in enumerate(resumir_estrategias(ens_ames))}
    secano, regado = r["A0"]["indicadores"], r["A2"]["indicadores"]
    assert secano["riego_mm_anio"]["p50"] == 0
    assert regado["dias_estres_anio"]["p50"] < secano["dias_estres_anio"]["p50"]
    for t in r["A2"]["temporadas"]:
        assert t["indicadores"]["riego_mm"]["p90"] <= 150.0 + 1e-9


def test_leguminosa_fija_y_monocultivo_no(ens_ames):
    r = resumir_estrategias(ens_ames)
    assert r[0]["indicadores"]["fijacion_n_kg_ha_anio"]["p90"] == 0
    soya = r[1]["temporadas"][1]["indicadores"]
    assert soya["fijacion_n_kg_ha"]["p50"] > 20


def test_equilibrio_de_referencia_mantiene_carbono(ens_ames):
    r = resumir_estrategias(ens_ames)
    assert abs(r[0]["indicadores"]["cambio_carbono_t_ha_anio"]["p50"]) < 0.3
    assert ens_ames.referencia == "A"


def test_reproducible_con_misma_semilla(clima_ames, suelo_ames):
    esc = construir(clima_ames, "historico", 1, max_miembros=2)
    a = ejecutar(clima_ames, esc, suelo_ames, [maiz_continuo(1)], n_parametros=3, semilla=11)
    b = ejecutar(clima_ames, esc, suelo_ames, [maiz_continuo(1)], n_parametros=3, semilla=11)
    c = ejecutar(clima_ames, esc, suelo_ames, [maiz_continuo(1)], n_parametros=3, semilla=12)
    np.testing.assert_array_equal(a.reg["B"], b.reg["B"])
    assert not np.array_equal(a.reg["B"], c.reg["B"])


def test_convergencia_en_subpasos(clima_ames, suelo_ames):
    esc = construir(clima_ames, "historico", 2, anio_inicio=2010)
    estr = [maiz_soya(2)]
    r1 = resumir_estrategias(ejecutar(clima_ames, esc, suelo_ames, estr, n_parametros=1, n_sub=1))[0]
    r4 = resumir_estrategias(ejecutar(clima_ames, esc, suelo_ames, estr, n_parametros=1, n_sub=4))[0]
    for k, tol in (("et_real_mm_anio", 0.03), ("drenaje_mm_anio", 0.15), ("lixiviacion_n_kg_ha_anio", 0.25)):
        a, b = r1["indicadores"][k]["p50"], r4["indicadores"][k]["p50"]
        assert abs(a - b) <= tol * max(abs(b), 1.0), (k, a, b)
    for t1, t4 in zip(r1["temporadas"], r4["temporadas"]):
        a, b = t1["indicadores"]["biomasa_kg_ha"]["p50"], t4["indicadores"]["biomasa_kg_ha"]["p50"]
        assert abs(a - b) <= 0.05 * b


def test_escenario_seco_mas_estres_que_humedo(clima_ames, suelo_ames):
    est = [maiz_continuo(1)]
    res = {}
    for tipo in ("seco", "humedo"):
        esc = construir(clima_ames, tipo, 1, semilla=3, n_miembros=6)
        res[tipo] = resumir_estrategias(ejecutar(clima_ames, esc, suelo_ames, est, n_parametros=2))[0]["indicadores"]
    assert res["seco"]["deficit_relativo"]["p50"] > res["humedo"]["deficit_relativo"]["p50"]
    assert res["seco"]["drenaje_mm_anio"]["p50"] < res["humedo"]["drenaje_mm_anio"]["p50"]


@pytest.mark.parametrize("precip,t", [(0.0, 25.0), (120.0, 20.0), (5.0, -5.0), (5.0, 45.0)])
def test_extremos_no_rompen_balances(precip, t, suelo_franco):
    clima = clima_constante(2, precip=precip, t=t)
    esc = construir(clima, "historico", 2)
    ens = ejecutar(clima, esc, suelo_franco, [maiz_continuo(2), maiz_soya(2)], n_parametros=2)
    agua, carbono, _ = _cierres(ens)
    assert agua < 1e-8 and carbono < 1e-9
    for k in ("W", "N", "C", "B"):
        assert np.all(np.isfinite(ens.reg[k])) and ens.reg[k].min() >= -1e-9
    if t <= -5 or t >= 45:
        assert ens.reg["B"].max() == 0


def test_cobertura_reduce_lluvia_intensa_sobre_suelo_desnudo(clima_ames, suelo_ames):
    esc = construir(clima_ames, "historico", 2, max_miembros=3)
    desnudo = Estrategia("A", "Maíz-soya", [Temporada("maiz", dia_nominal("A1-05-01")),
                                            Temporada("soya", dia_nominal("A2-05-15"))])
    cubierto = Estrategia("B", "Maíz-avena-soya", [Temporada("maiz", dia_nominal("A1-05-01")),
                                                   Temporada("avena", dia_nominal("A1-10-25"), cosechar=False),
                                                   Temporada("soya", dia_nominal("A2-05-15"))])
    r = resumir_estrategias(ejecutar(clima_ames, esc, suelo_ames, [desnudo, cubierto], n_parametros=2))
    a, b = r[0]["indicadores"], r[1]["indicadores"]
    assert b["cobertura_media"]["p50"] > a["cobertura_media"]["p50"]
    k = "lluvia_intensa_sobre_suelo_desnudo_mm_anio"
    assert b[k]["p50"] <= a[k]["p50"]
    assert a["exposicion_erosiva_mm_anio"]["p50"] == a[k]["p50"]
    nuevo = "indice_exposicion_erosiva"
    assert a["exposicion_erosiva_mm_anio"]["obsoleto"] and a["exposicion_erosiva_mm_anio"]["reemplazado_por"] == nuevo
    assert a[k]["obsoleto"] and a[k]["reemplazado_por"] == nuevo
    # Índice de la función de Datos con la cobertura simulada: la avena de cobertura lo baja
    assert b[nuevo]["p50"] <= a[nuevo]["p50"]
    assert b["dias_suelo_desnudo_anio"]["p50"] <= a["dias_suelo_desnudo_anio"]["p50"]


def test_estado_inicial_de_residuo_igual_para_todas(ens_ames):
    ini = ens_ames.carbono_inicial
    assert np.all(ini["res0"] >= 0) and np.median(ini["res0"]) > 0
    n = ens_ames.K * ens_ames.P
    f0 = ens_ames.reg["f_residuo"][:, 0].reshape(ens_ames.S, n)
    np.testing.assert_allclose(f0[0], f0[1], rtol=0.05)


def test_temporadas_solapadas_y_pendientes_fallan(clima_ames, suelo_ames):
    esc = construir(clima_ames, "historico", 1, max_miembros=1)
    solapada = Estrategia("X", "mal", [Temporada("maiz", dia_nominal("A1-03-01")),
                                        Temporada("soya", dia_nominal("A1-04-01"))])
    with pytest.raises(ValueError, match="antes de terminar"):
        ejecutar(clima_ames, esc, suelo_ames, [solapada], n_parametros=1)
    from gemelo.procedencia import ParametroPendiente
    with pytest.raises(ParametroPendiente):
        ejecutar(clima_ames, esc, suelo_ames, [Estrategia("Y", "café", [Temporada("cafe", 0)])], n_parametros=1)
