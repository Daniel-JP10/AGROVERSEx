# asistido por SI: Cursor (agente), escritura y revisión de código; núcleo del gemelo digital en el hackatón
"""Prioridades v1.1: la fórmula de orden por pesos reproduce los casos de prueba publicados para Web."""
import pytest

from gemelo import prioridades as pr
from gemelo.optimizacion import OBJETIVOS


def test_deslizadores_cubren_los_cuatro_de_web():
    assert set(pr.DESLIZADORES) == {"agua", "suelo", "insumos", "estabilidad_climatica"}
    assert pr.DESLIZADORES["insumos"] == ("fertilizante",)
    assert OBJETIVOS["fertilizante"]["indicador"] == "fertilizante_n_kg_ha_anio"
    assert all(o in OBJETIVOS for objs in pr.DESLIZADORES.values() for o in objs)


def test_mapeo_v12_igual_al_archivo_compartido_con_web():
    import json
    d = json.loads(pr.CASOS_ARCHIVO.read_text(encoding="utf-8"))
    assert d["version_contrato"] == "1.2"
    assert {k: tuple(v) for k, v in d["deslizadores"].items()} == pr.DESLIZADORES
    assert pr.DESLIZADORES["suelo"] == ("carbono", "exposicion_erosiva")
    assert d["alias_obsoletos"] == {"lluvia_intensa_suelo_desnudo": "exposicion_erosiva"}
    for o, x in d["objetivos"].items():
        assert OBJETIVOS[o]["indicador"] == x["indicador"] and OBJETIVOS[o]["sentido"] == x["sentido"]


@pytest.mark.parametrize("caso", pr.CASOS_PRUEBA, ids=lambda c: c["nombre"])
def test_casos_de_prueba(caso):
    norm = pr.normalizar(pr.TABLA_PRUEBA)
    s = pr.puntajes(norm, caso["pesos"])
    for i, esperado in caso["puntajes"].items():
        assert s[i] == pytest.approx(esperado, abs=1e-6)
    assert pr.ordenar(norm, caso["pesos"]) == caso["orden"]


def test_normalizacion_orientada_y_empates():
    norm = pr.normalizar(pr.TABLA_PRUEBA)
    assert norm["Y"]["deficit"] == 1.0 and norm["X"]["deficit"] == 0.0      # min: menor es mejor
    assert norm["Z"]["riesgo_produccion"] == 1.0                            # max: mayor es mejor
    assert {n["riego"] for n in norm.values()} == {0.5}                     # todos iguales -> 0,5


def test_pesos_negativos_son_error():
    with pytest.raises(ValueError):
        pr.puntajes(pr.normalizar(pr.TABLA_PRUEBA), {"agua": -1})
