# asistido por SI: Cursor (agente), escritura y revisión de código; núcleo del gemelo digital en el hackatón
"""Textos v1.1: claves en inglés y español, avisos traducidos a clave y rótulo de procedencia."""
import re

import pytest

from gemelo import indicadores as ind
from gemelo.api import simular
from gemelo.salida import AVISO_EQUILIBRIO, AVISO_MENSUAL, AVISO_SIMULADO
from gemelo.textos import catalogo, clave_de_aviso, texto
from test_contrato import ESCENARIO


def test_mismas_claves_y_parametros_en_los_dos_idiomas():
    cat = catalogo()
    assert set(cat["en"]) == set(cat["es"])
    for k in cat["en"]:
        assert set(re.findall(r"{(\w+)", cat["en"][k])) == set(re.findall(r"{(\w+)", cat["es"][k])), k
    for k in ind.DEFINICIONES:
        assert f"indicator.{k}.explanation" in cat["en"]


@pytest.mark.parametrize("aviso", [AVISO_SIMULADO, AVISO_EQUILIBRIO, AVISO_MENSUAL])
def test_avisos_fijos_tienen_clave(aviso):
    assert clave_de_aviso(aviso)["clave"] != "warning.untranslated"


def test_aviso_con_parametros():
    c = clave_de_aviso("Regla de sucesión Papa / nematodo PENDIENTE: no se aplica")
    assert c == {"clave": "warning.succession_pending", "parametros": {"familia": "Papa", "enfermedad": "nematodo"}}
    assert texto(c["clave"], "en", **c["parametros"]) == "Succession rule Papa / nematodo PENDIENTE: not applied"


def test_documento_con_claves_y_rotulo():
    doc = simular(ESCENARIO)
    cat = catalogo()
    assert len(doc["avisos_claves"]) == len(doc["avisos"])
    assert all(a["clave"] in cat["en"] and a["clave"] != "warning.untranslated" for a in doc["avisos_claves"])
    assert doc["metadatos"]["version_contrato_completa"] == "1.2"
    assert doc["metadatos"]["naturaleza"] == "simulado"
    assert doc["metadatos"]["rotulo"]["parametros"]["fuentes"] == ["source.nasa_power", "source.soilgrids"]
    e = doc["estrategias"][0]
    assert e["indicadores"]["riego_mm_anio"]["explicacion_clave"] == "indicator.riego_mm_anio.explanation"
    assert set(doc["tarjetas"]) == {"A", "B"}
    assert doc["tarjetas"]["B"]["por_que"][0]["clave"] == "card.why.is_baseline"


def _claves_anidadas(x):
    if isinstance(x, dict):
        if isinstance(x.get("clave"), str) and "." in x["clave"]:
            yield x["clave"]
        for v in x.values():
            yield from _claves_anidadas(v)
    elif isinstance(x, list):
        for v in x:
            yield from _claves_anidadas(v)


def test_tarjetas_se_traducen_sin_unidades_en_espanol():
    doc = simular(ESCENARIO)
    cat = catalogo()
    for t in doc["tarjetas"].values():
        for c in _claves_anidadas(t):
            assert c in cat["en"], c
        for seccion in t.values():
            for entrada in seccion if isinstance(seccion, list) else []:
                en = texto(entrada["clave"], "en", **entrada.get("parametros", {}))
                assert not re.search(r"año|adimensional|fracción|temporadas|bajo|alto", en), en


def test_unidades_en_ingles():
    assert texto("unit.kg N/ha/año") == "kg N/ha/yr"
    assert texto("unit.kg MS/ha") == "kg DM/ha"
    assert texto("unit.kg N/ha/año", "es") == "kg N/ha/año"
    assert texto("card.gap.changes_order", "en", parametro="x", lo=1, hi=2, unidad={"clave": "unit.días"},
                 central=1, bajo=2, alto=3).startswith("SUPUESTO parameter x (range 1 to 2 days)")
