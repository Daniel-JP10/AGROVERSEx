# asistido por SI: Claude Code (Opus 5.5), pruebas de la alerta de helada D-032 y de la lluvia alterna IMERG
import json
from dataclasses import replace
from pathlib import Path

import numpy as np
import pytest

from gemelo import alertas
from gemelo.clima import con_precip_alterna
from gemelo.entrada import leer_entrada
from gemelo.manejo import compilar
from gemelo.parametros import cargar_catalogo

RAIZ = Path(__file__).resolve().parents[2]
LOTES = RAIZ / "datos" / "referencia" / "lotes"


def _programas(ent):
    cat = cargar_catalogo()
    usados = sorted({t.cultivo for e in ent.estrategias for t in e.temporadas})
    indice = {c: i for i, c in enumerate(usados)}
    return [compilar(e, cat, indice, 365 * ent.escenario.anios_horizonte) for e in ent.estrategias]


@pytest.fixture(scope="module")
def ipiales():
    return leer_entrada(RAIZ / "ejemplos" / "escenario_ipiales.yaml")


def test_ipiales_lee_minima_corregida_sin_tocar_la_media(ipiales):
    # §4.3: T2M crudo para la física, T2M_MIN_CORR aparte; la corregida es más fría que la cruda
    d = ipiales.clima.datos
    assert d["t2m"].mean() == pytest.approx(13.18, abs=0.05)
    assert (d["t2m_min_corr"] < d["t2m_min"]).all()
    v = json.loads((LOTES / "validacion_temperatura_ipiales.json").read_text(encoding="utf-8"))
    assert d["t2m_min_corr"].min() == pytest.approx(v["analisis_extremos_frios_tmin"]["power_corr_2934m_min_c"],
                                                    abs=0.01)


def test_alerta_ipiales_provisional_con_sesgo_de_datos_y_vigilancia(ipiales):
    b = alertas.bloque(ipiales, _programas(ipiales))["helada_etapa_sensible"]
    v = json.loads((LOTES / "validacion_temperatura_ipiales.json").read_text(encoding="utf-8"))
    c = v["comparaciones"]["T2M_MIN_vs_TMIN"]["corregida_lote_2934m"]
    assert b["provisional"] and b["serie_temperatura"] == "T2M_MIN_CORR" and not b["es_pronostico"]
    assert b["validacion"]["sesgo_c"] == c["sesgo_c"]
    assert b["margen_sesgo_c"] == c["sesgo_c_ic95_bootstrap_anual"][1]
    assert [a["clave"] for a in b["avisos"]] == ["alert.frost.warm_bias", "alert.frost.provisional"]
    # La serie nunca baja de 0 °C y la estación sí: no se puede decir "sin alerta"
    assert b["serie_no_resuelve_heladas"]
    for e in b["estrategias"].values():
        assert e["estado"] == "vigilancia" and e["clave"] == "alert.frost.unresolved"
        r = e["tmin_minima_etapa_sensible_c"]
        assert r["p10"] <= r["p50"] <= r["p90"]


def test_alerta_activa_y_rango_ordenado_con_frio_desplazado(ipiales):
    # Con -4 °C la serie sí cruza el umbral: cota baja <= cota alta y estado activa
    esc = replace(ipiales.escenario, delta_temp_c=-4.0)
    b = alertas.helada_etapa_sensible(ipiales.clima, esc, _programas(ipiales), 0.0, True,
                                      alertas.leer_validacion(LOTES / "validacion_temperatura_ipiales.json",
                                                              "t2m_min_corr"))
    e = b["estrategias"]["A"]
    f = e["fraccion_temporadas_con_helada"]
    assert e["estado"] == "activa" and 0 < f["cota_baja"] <= f["cota_alta"] <= 1


def test_mascara_sensible_solo_des_y_med_de_cultivos_cosechados(ipiales):
    p = next(x for x in _programas(ipiales) if x.estrategia.id == "D")   # avena de cobertura sin cosechar
    sens = alertas.mascara_sensible(p)
    l1, l2, l3, _ = p.duraciones[0]
    k0 = p.temporada == 0
    assert sens[k0].sum() == l2 + l3
    cobertura = [k for k, t in enumerate(p.estrategia.temporadas) if not t.cosechar]
    assert cobertura and not sens[np.isin(p.temporada, cobertura)].any()


def test_lluvia_alterna_imerg_cambia_solo_la_lluvia(ipiales):
    alt = con_precip_alterna(ipiales.clima, ipiales.precip_alterna["archivo"])
    comp = json.loads((LOTES / "comparacion_power_imerg.json").read_text(encoding="utf-8"))
    col = next(x for x in comp if x["lote_id"] == "DEMO-COL-01")
    # Media anual en años nominales (sin 29 de febrero): cerca de la de Datos
    assert alt.precip_anual().mean() == pytest.approx(col["anual_media_mm"]["imerg"], rel=0.01)
    for k in ("t2m", "t2m_min_corr", "rad_sw"):
        assert np.array_equal(alt.datos[k], ipiales.clima.datos[k])
    assert "IMERG" in alt.fuente


def test_mead_sin_validacion_no_es_provisional():
    ent = leer_entrada(RAIZ / "ejemplos" / "escenario_mead.yaml")
    b = alertas.bloque(ent, _programas(ent))["helada_etapa_sensible"]
    assert not b["provisional"] and b["validacion"] is None and b["margen_sesgo_c"] == 0.0
    assert ent.precip_alterna is None
