# asistido por SI: Cursor (agente), escritura y revisión de código; núcleo del gemelo digital en el hackatón
import numpy as np
import pytest

from gemelo.escenarios import construir
from gemelo.modelos import Estrategia, Fertilizacion, Temporada, dia_nominal
from gemelo.optimizacion import (RESTRICCIONES, Campania, OpcionCultivo, ProblemaRotacion, ReglaSucesion,
                                 cargar_reglas, optimizar)
from gemelo.parametros import cargar_catalogo


def _problema(**kw):
    opciones = {"maiz": OpcionCultivo("maiz", "maiz", fertilizacion=[Fertilizacion(0, 150.0)]),
                "soya": OpcionCultivo("soya", "soya", etapas_variante="centro EE. UU."),
                "avena_cob": OpcionCultivo("avena_cob", "avena", cosechar=False)}
    campanias = [Campania("otono", "10-10", ["avena_cob"]), Campania("principal", "05-01", ["maiz", "soya"])]
    return ProblemaRotacion(2, campanias, opciones, desfases_dias=(0, 14), **kw)


def test_codificacion_y_decodificacion():
    p = _problema()
    assert [c.nombre for c in p.campanias] == ["principal", "otono"]
    xl, xu = p.limites()
    assert len(xl) == 2 * 2 * 2 and xu.tolist() == [2, 1, 1, 1, 2, 1, 1, 1]
    cat = cargar_catalogo()
    est, viol = p.decodificar([1, 0, 1, 0, 2, 0, 0, 0], cat)
    assert [t.cultivo for t in est.temporadas] == ["maiz", "avena", "soya"]
    assert est.temporadas[1].cosechar is False
    assert est.temporadas[2].siembra == dia_nominal("A2-05-01")
    assert all(v == 0 for v in viol.values())
    # Maíz con desfase de 14 días termina después del 10 de octubre: solape con la avena
    _, viol = p.decodificar([1, 1, 1, 0, 0, 0, 0, 0], cat)
    assert viol["solape_dias"] > 0
    # Genes irrelevantes de un barbecho no cambian la clave
    assert p.canonico([0, 1, 0, 0, 1, 0, 0, 0]) == p.canonico([0, 0, 0, 0, 1, 0, 0, 0])


def test_restricciones_de_sucesion_exigidos_y_cosechas():
    regla = ReglaSucesion("Prueba", ("soya",), 1.0, "EV-TEST")
    p = _problema(reglas=[regla], exigidos=["maiz"], min_cosechas_por_anio=1.0)
    cat = cargar_catalogo()
    _, viol = p.decodificar([2, 0, 0, 0, 2, 0, 0, 0], cat)      # soya dos años seguidos, sin maíz
    assert viol["sucesion_dias"] > 0
    assert viol["cultivos_exigidos_faltantes"] == 1
    _, viol = p.decodificar([0, 0, 1, 0, 0, 0, 0, 0], cat)      # solo cobertura: ninguna cosecha
    assert viol["cosechas_faltantes"] == 2


def test_cargar_reglas_por_clima():
    templado, avisos = cargar_reglas(clima="templado")
    familias = {r.familia: r for r in templado}
    assert familias["Papa"].intervalo_anios == 4.0 and "papa" in familias["Papa"].cultivos
    assert any("PENDIENTE" in a for a in avisos)
    tropical, avisos_t = cargar_reglas(clima="tropical")
    assert tropical == [] and any("INV-ROT §5.2" in a for a in avisos_t)


def test_objetivos_invalidos():
    with pytest.raises(ValueError):
        _problema(objetivos=["produccion", "felicidad"])
    with pytest.raises(ValueError):
        _problema(objetivos=["produccion"])


@pytest.mark.lento
def test_nsga2_frente_factible_y_no_dominado(clima_ames, suelo_ames):
    esc = construir(clima_ames, "historico", 2, max_miembros=3)
    base = Estrategia("BASE", "Maíz continuo", [Temporada("maiz", dia_nominal(f"A{i}-05-01"),
                                                          fertilizacion=[Fertilizacion(0, 150.0)]) for i in (1, 2)])
    p = _problema(objetivos=["produccion", "carbono", "exposicion_erosiva"])
    assert p.objetivos == ["produccion", "carbono", "lluvia_intensa_suelo_desnudo"]
    r = optimizar(clima_ames, esc, suelo_ames, p, base, poblacion=10, generaciones=4, miembros_clima=2,
                  muestras_parametros=2, miembros_final=3, muestras_final=2, semilla=5, max_soluciones=5)
    assert 1 <= len(r["frente"]) <= 5
    assert r["busqueda"]["factibles"] >= len(r["frente"])
    cat = cargar_catalogo()
    F = []
    for f in r["frente"]:
        assert f["etiqueta"].startswith("candidata NSGA-II")
        temps = f["temporadas"]
        for a, b in zip(temps, temps[1:]):
            assert dia_nominal(a["cosecha"]) < dia_nominal(b["siembra"])
        F.append([-f["objetivos"]["produccion"], -f["objetivos"]["carbono"], f["objetivos"]["lluvia_intensa_suelo_desnudo"]])
        assert set(f["frente_a_linea_base"]) == {"gana", "cede", "similar"}
    assert r["compromisos"]["compromiso_equilibrado"] in {f["id"] for f in r["frente"]}
    assert r["linea_base"]["id"] == "BASE"
    assert len(RESTRICCIONES) == 5
    # Reproducible con la misma semilla
    r2 = optimizar(clima_ames, esc, suelo_ames, p, base, poblacion=10, generaciones=4, miembros_clima=2,
                   muestras_parametros=2, miembros_final=3, muestras_final=2, semilla=5, max_soluciones=5)
    assert [f["secuencia"] for f in r2["frente"]] == [f["secuencia"] for f in r["frente"]]
    assert np.isfinite(np.array(F)).all()
