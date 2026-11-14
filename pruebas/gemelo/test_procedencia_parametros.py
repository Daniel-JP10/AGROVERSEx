# asistido por SI: Cursor (agente), escritura y revisión de código; núcleo del gemelo digital en el hackatón
import pytest

from gemelo.parametros import cargar_catalogo, leer_etapas, leer_kc
from gemelo.procedencia import Parametro, ParametroPendiente, cargar_tabla


def test_parametro_exige_etiqueta_y_valor():
    with pytest.raises(ValueError):
        Parametro("x", 1.0, "m", "INVENTADO")
    with pytest.raises(ValueError):
        Parametro("x", None, "m", "SUPUESTO")
    with pytest.raises(ValueError):
        Parametro("x", 5.0, "m", "SUPUESTO", rango=(0.0, 1.0))
    with pytest.raises(ParametroPendiente):
        Parametro("x", None, "m", "PENDIENTE").exigir()


def test_calibrar_colapsa_rango_y_marca_observado():
    p = Parametro("n", 30.0, "kg N/ha", "SUPUESTO", rango=(10.0, 60.0))
    c = p.calibrar(42.0)
    assert c.valor == 42.0 and c.rango is None and c.naturaleza == "observado" and c.etiqueta == "FUENTE"
    assert "SUPUESTO" in c.contexto


def test_tablas_de_referencia_cargan_con_etiquetas_validas():
    for archivo in ("agua_suelo.yaml", "carbono_nitrogeno.yaml"):
        t = cargar_tabla(archivo)
        for nombre, p in t.items():
            assert p.referencia, f"{archivo}:{nombre} sin referencia"
            if p.etiqueta == "SUPUESTO":
                assert p.rango is not None or p.unidad in ("percentil",), f"{nombre}: SUPUESTO sin rango"


@pytest.mark.parametrize("texto,central,rango", [
    ("0,3 (grupo)", 0.3, (0.3, 0.3)),
    ("0,60–0,35", 0.475, (0.35, 0.60)),
    ("0,4 helado; 0,7 no helado", 0.4, (0.4, 0.7)),
    ("1,05", 1.05, (1.05, 1.05)),
])
def test_leer_kc(texto, central, rango):
    v, r = leer_kc(texto)
    assert v == pytest.approx(central) and r == pytest.approx(rango)


def test_leer_etapas_y_variantes():
    t = "15/15/40/15 = 85 trópico; 20/30-35/60/25 = 140 centro EE. UU."
    assert leer_etapas(t) == (15, 15, 40, 15)
    assert leer_etapas(t, "centro EE. UU.") == (20, 30, 60, 25)
    assert leer_etapas("No está en Tabla 11") is None
    with pytest.raises(ValueError):
        leer_etapas(t, "Marte")


def test_catalogo_marca_pendientes_y_no_aptos():
    cat = cargar_catalogo()
    assert cat["maiz"].pendientes() == []
    assert cat["maiz"].p("kc_mid").ficha == "EV-ROT-010"
    assert "etapas" in cat["trebol_berseem"].pendientes()
    with pytest.raises(ParametroPendiente):
        cat["cana_azucar"].verificar_simulable()
    with pytest.raises(ParametroPendiente):
        cat["trebol_berseem"].verificar_simulable()
    cat["trebol_berseem"].verificar_simulable(etapas_usuario=(10, 20, 30, 10))
    assert cat["soya"].fija_n and not cat["maiz"].fija_n
