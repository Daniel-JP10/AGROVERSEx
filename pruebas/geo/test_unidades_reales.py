# asistido por SI: Claude Code (Anthropic), escritura y revisión de código; base del prototipo migrada en el hackatón
import os
import sqlite3

# el GeoJSON de ADM2 pesa GB; GDAL limita el tamaño de objeto por defecto
os.environ.setdefault("OGR_GEOJSON_MAX_OBJ_SIZE", "0")

import pytest
import shapely
import pyogrio

from simulacion.config import GEO_SQLITE, PROCESADOS

pytestmark = [pytest.mark.datos_reales,
              pytest.mark.skipif(not GEO_SQLITE.exists(), reason="falta geo.sqlite")]


@pytest.fixture(scope="module")
def con():
    c = sqlite3.connect(GEO_SQLITE)
    yield c
    c.close()


def q(con, sql):
    return con.execute(sql).fetchone()[0]


def test_colombia(con):
    assert q(con, "select count(*) from unidad where iso3='COL' and nivel=1") == 33
    assert q(con, "select count(*) from unidad where iso3='COL' and nivel=2") == 1119


def test_ids_unicos_y_padres(con):
    assert q(con, "select count(*)-count(distinct id) from unidad") == 0
    assert q(con, "select count(*) from unidad where nivel=2 and padre_id is null and cruce_ambiguo=0") == 0
    assert q(con, "select count(*) from unidad where padre_id is not null and padre_id not in (select id from unidad)") == 0


def test_area_y_nombre(con):
    assert q(con, "select count(*) from unidad where not area_km2>0") == 0
    assert q(con, "select count(*) from unidad where nombre is null or trim(nombre)=''") == 0


def test_fiji_punto_dentro(con):
    ids = {r[0]: (r[1], r[2]) for r in con.execute("select id,punto_lon,punto_lat from unidad where iso3='FJI'")}
    for n in (0, 1, 2):
        g = pyogrio.read_dataframe(PROCESADOS / f"limites_crudos/adm{n}.geojson", where="iso3='FJI'")
        g = g[g.id.isin(ids)]
        assert len(g) > 0
        for r in g.itertuples():
            assert shapely.contains_xy(r.geometry, *ids[r.id]), r.id


def test_todo_iso3_es_un_id_de_nivel_0_o_9(con):
    assert q(con, "select count(*) from unidad where iso3 not in (select id from unidad where nivel in (0, 9))") == 0


def test_kosovo_sin_duplicar(con):
    # gbOpen usa XKX y GADM XKO: el alias evita que gbOpen rellene Kosovo otra vez
    assert q(con, "select count(*) from unidad where nivel=2 and iso3='XKX'") == 0


def test_adm0_incluye_nivel_9(con):
    n9 = q(con, "select count(*) from unidad where nivel=9")
    assert n9 > 0
    g = pyogrio.read_dataframe(PROCESADOS / "limites_crudos/adm0.geojson", columns=["nivel"], read_geometry=False)
    assert int((g.nivel == 9).sum()) == n9
