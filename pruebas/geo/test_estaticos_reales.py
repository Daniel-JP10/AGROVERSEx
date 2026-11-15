# asistido por SI: Claude Code (Anthropic), escritura y revisión de código; base del prototipo migrada en el hackatón
import sqlite3

import pytest

from simulacion.config import GEO_SQLITE

# se corren en WSL, sobre la geo.sqlite con estaticos ya calculados
pytestmark = [pytest.mark.datos_reales,
              pytest.mark.skipif(not GEO_SQLITE.exists(), reason="falta geo.sqlite")]


@pytest.fixture(scope="module")
def con():
    c = sqlite3.connect(GEO_SQLITE)
    if not c.execute("SELECT count(*) FROM estatico").fetchone()[0]:
        pytest.skip("estatico vacio: falta correr estaticos")
    yield c
    c.close()


def q(con, sql):
    return con.execute(sql).fetchone()[0]


def test_ph_en_rango(con):
    assert q(con, "SELECT count(*) FROM estatico WHERE variable_id='phh2o_0_30' AND media IS NOT NULL "
                  "AND (media < 3 OR media > 11)") == 0


def test_textura_suma_cien(con):
    malas = q(con, """SELECT count(*) FROM estatico c JOIN estatico a ON a.unidad_id=c.unidad_id AND a.variable_id='sand_0_30'
        JOIN estatico s ON s.unidad_id=c.unidad_id AND s.variable_id='silt_0_30'
        WHERE c.variable_id='clay_0_30' AND c.media IS NOT NULL AND a.media IS NOT NULL AND s.media IS NOT NULL
        AND (c.media + a.media + s.media < 95 OR c.media + a.media + s.media > 105)""")
    assert malas == 0


def test_bdod_en_rango(con):
    assert q(con, "SELECT count(*) FROM estatico WHERE variable_id='bdod_0_30' AND media IS NOT NULL "
                  "AND (media < 0.1 OR media > 2.0)") == 0


def test_bogota(con):
    v = q(con, "SELECT e.media FROM estatico e JOIN unidad u ON u.id=e.unidad_id "
               "WHERE u.iso3='COL' AND u.nombre LIKE 'Bogot%' AND e.variable_id='elev_media' LIMIT 1")
    assert 2000 <= v <= 3500


def test_sin_valor_con_fraccion_cero(con):
    assert q(con, "SELECT count(*) FROM estatico WHERE fraccion_valida = 0 AND media IS NOT NULL") == 0


def test_unidades_pequenas_contexto(con):
    # unidades menores de 1 km2 (menor que la celda): fraccion_valida entre 0 y 1; se cuenta como contexto
    n = q(con, "SELECT count(*) FROM estatico e JOIN unidad u ON u.id=e.unidad_id "
               "WHERE u.area_km2 < 1 AND (e.fraccion_valida < 0 OR e.fraccion_valida > 1)")
    assert n == 0


def test_unidades_pequenas_con_suelo_null_se_registran(con):
    # cota medida: 245 unidades de menos de 1 km2 sin dato de suelo (SoilGrids es de 1 km)
    n = q(con, "SELECT count(DISTINCT e.unidad_id) FROM estatico e JOIN unidad u ON u.id=e.unidad_id "
               "WHERE u.area_km2 < 1 AND e.variable_id='phh2o_0_30' AND e.media IS NULL")
    print(f"unidades < 1 km2 con suelo NULL: {n}")
    assert n <= 300


def test_elevacion_nodata_marino_sin_valor(con):
    # el mar es NoData: ninguna unidad sin celdas validas trae media, y hay unidades parcialmente marinas
    assert q(con, "SELECT count(*) FROM estatico WHERE variable_id='elev_media' AND fraccion_valida = 0 AND media IS NOT NULL") == 0
    assert q(con, "SELECT count(*) FROM estatico WHERE variable_id='elev_media' AND fraccion_valida < 1") > 0
