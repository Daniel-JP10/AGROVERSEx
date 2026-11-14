# asistido por SI: Claude Code (Anthropic), escritura y revisión de código; base del prototipo migrada en el hackatón
import gzip
import json
import sqlite3
from pathlib import Path

import pytest

from simulacion.geo.indice_busqueda import construir_indice, escribir_indice

ESQUEMA = Path(__file__).parents[2] / "src/simulacion/geo/esquema_geo.sql"

# (id, nivel, iso3, padre_id, nombre, nombre_ascii, nombre_es, nombre_en)
UNIDADES = [
    ("COL", 0, "COL", None, "Colombia", "Colombia", "Colombia", "Colombia"),
    ("COL.1_1", 1, "COL", "COL", "Antioquia", "Antioquia", "Antioquia", "Antioquia"),
    ("COL.2_1", 1, "COL", "COL", "Bolívar", "Bolivar", None, "Bolivar"),
    ("COL.1.1_1", 2, "COL", "COL.1_1", "Bolívar", "Bolivar", "Bolívar", None),
    ("COL.2.1_1", 2, "COL", "COL.2_1", "Bolívar", "Bolivar", None, None),
    ("XD1", 9, "XD1", None, "Zona en disputa (XD1)", "Zona en disputa (XD1)", None, None),
    ("gb:77", 2, "COL", None, "Huérfana", "Huerfana", None, None),
]


@pytest.fixture
def sqlite_temporal(tmp_path):
    ruta = tmp_path / "geo.sqlite"
    con = sqlite3.connect(ruta)
    con.executescript(ESQUEMA.read_text(encoding="utf-8"))
    con.executemany(
        "INSERT INTO unidad(id, nivel, iso3, padre_id, nombre, nombre_ascii, nombre_es, nombre_en)"
        " VALUES (?,?,?,?,?,?,?,?)", UNIDADES)
    con.commit()
    con.close()
    return ruta


def test_contexto_distingue_los_bolivar(sqlite_temporal):
    filas = {f["id"]: f for f in construir_indice(sqlite_temporal)}
    assert filas["COL.1.1_1"]["ctx"] == "Antioquia · Colombia"
    assert filas["COL.2.1_1"]["ctx"] == "Bolívar · Colombia"
    assert filas["COL.1_1"]["ctx"] == "Colombia"
    assert filas["COL"]["ctx"] == ""


def test_ascii_normalizado(sqlite_temporal):
    filas = {f["id"]: f for f in construir_indice(sqlite_temporal)}
    assert filas["COL.1.1_1"]["a"] == "bolivar"


def test_nombre_es_nulo_omite_clave(sqlite_temporal):
    filas = {f["id"]: f for f in construir_indice(sqlite_temporal)}
    assert "es" not in filas["COL.2.1_1"]
    assert "en" not in filas["COL.2.1_1"]
    assert filas["COL.1.1_1"]["es"] == "Bolívar"


def test_incluye_zonas_en_disputa(sqlite_temporal):
    filas = {f["id"]: f for f in construir_indice(sqlite_temporal)}
    assert filas["XD1"]["ctx"] == "Zona en disputa" and filas["XD1"]["nivel"] == 9
    assert len(filas) == 7


def test_padre_nulo_completa_pais_por_iso3(sqlite_temporal):
    filas = {f["id"]: f for f in construir_indice(sqlite_temporal)}
    assert filas["gb:77"]["ctx"] == "Colombia"


def test_escritura_y_lectura_de_vuelta(sqlite_temporal, tmp_path):
    filas = construir_indice(sqlite_temporal)
    ruta = tmp_path / "salida" / "indice.json.gz"
    n = escribir_indice(filas, ruta)
    assert n == ruta.stat().st_size
    assert json.loads(gzip.decompress(ruta.read_bytes())) == filas


def test_nombres_ne_completan_nivel_0(sqlite_temporal):
    ne = {"COL": ("Colombia NE", "Colombia NE"), "CIV": ("Costa de Marfil", "Ivory Coast")}
    con = sqlite3.connect(sqlite_temporal)
    con.execute("INSERT INTO unidad(id, nivel, iso3, nombre, nombre_ascii) VALUES ('CIV', 0, 'CIV', 'Côte d''Ivoire', 'Cote d''Ivoire')")
    con.commit()
    con.close()
    filas = {f["id"]: f for f in construir_indice(sqlite_temporal, ne)}
    assert filas["CIV"]["es"] == "Costa de Marfil" and filas["CIV"]["en"] == "Ivory Coast"
    assert filas["COL"]["es"] == "Colombia"  # lo que la base ya trae no se pisa
    assert "es" not in filas["COL.2.1_1"]  # solo el nivel 0


def test_costa_de_marfil_encuentra_civ():
    from simulacion.geo.normalizar import normalizar_nombre
    from simulacion.geo.indice_busqueda import NE_ADMIN0, nombres_paises
    if not NE_ADMIN0.exists():
        pytest.skip("sin ne_10m_admin_0_countries.zip en datos/crudos")
    ne = nombres_paises()
    assert normalizar_nombre(ne["CIV"][0]) == "costa de marfil"
    assert ne["XKO"] == ne["KOS"] and ne["FRA"][0] == "Francia"
