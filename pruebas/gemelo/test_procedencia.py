# asistido por SI: Cursor (agente), escritura y revisión de código; núcleo del gemelo digital en el hackatón
"""Regla del equipo: sin datos, coeficientes, servicios ni modelos de entidades afiliadas o de propiedad de China."""
import re

import pytest

from conftest import RAIZ
from gemelo.procedencia import REFERENCIAS

MARCAS = re.compile(r"(?i)procedencia[_ ]china|\bchina\b|\bchinese\b|\bCHN\b|D-009|Cai 2025|Chen 2019|"
                    r"North China|Academy of Sciences|\bCAS\b|\bCAAS\b")


@pytest.mark.parametrize("ruta", sorted(REFERENCIAS.glob("*.yaml")), ids=lambda p: p.name)
def test_referencias_sin_procedencia_china(ruta):
    assert not MARCAS.search(ruta.read_text(encoding="utf-8"))


def test_readme_declara_procedencia_de_cada_fuente():
    txt = (RAIZ / "src/gemelo/README.md").read_text(encoding="utf-8")
    assert "### Procedencia de las fuentes" in txt
    for fuente in ("FAO-56", "AquaCrop", "SoilGrids", "NASA POWER", "Saxton y Rawls", "ICBM", "NOAA CPC",
                   "TR-55", "IPCC", "Yan y Hunt", "Sinclair y Muchow", "Salvagiotti", "Gregory", "pymoo"):
        assert fuente in txt, fuente
