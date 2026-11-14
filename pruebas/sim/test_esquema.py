# asistido por SI: Claude Code (Anthropic), escritura y revisión de código; base del prototipo migrada en el hackatón
import sqlite3

import numpy as np
import pytest

from simulacion import config
from simulacion.variables import INT_NULO, VARIABLES, a_entero, crear_esquema, de_entero

COLS_MENSUAL = [
    "unidad_id", "mes_id", "precip", "precip_err", "precip_frac", "t2m", "t2m_p10", "t2m_p90", "t2m_max",
    "t2m_min", "rh2m", "rad_sw", "dias_helada", "et", "et_p10", "et_p90", "et_frac", "ndvi", "ndvi_p10",
    "ndvi_p90", "ndvi_frac", "lst_dia", "lst_err", "lst_frac", "sm_sup", "sm_raiz", "sm_err", "sm_frac",
    "sm_fuente", "sm_qual", "tws", "tws_err", "tws_frac", "dias_calor", "dias_extremo",
    "dias_suelo_expuesto", "suelo_metodo", "bandera_motivo",
]
TABLAS = {
    "fuente", "variable", "unidad", "estatico", "clase_fraccion", "mensual", "anual", "enso", "evento",
    "evento_unidad", "sistema_rotacion", "efecto_antecesor", "cultivo", "regla_sucesion", "lote",
    "lote_diario", "lote_ventana", "metadatos", "zona_demo",
}


@pytest.fixture
def con():
    c = sqlite3.connect(":memory:")
    crear_esquema(c)
    return c


def test_esquema_crea_todas_las_tablas(con):
    nombres = {r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    assert nombres == TABLAS


@pytest.mark.parametrize("tabla", ["mensual", "anual", "lote_diario"])
def test_sin_rowid(con, tabla):
    assert "WITHOUT ROWID" in con.execute("SELECT sql FROM sqlite_master WHERE name=?", (tabla,)).fetchone()[0]
    assert [r[3] for r in con.execute(f"PRAGMA index_list('{tabla}')")] == ["pk"]


def test_columnas_mensual_son_las_de_8_3(con):
    assert [r[1] for r in con.execute("PRAGMA table_info(mensual)")] == COLS_MENSUAL


def test_columnas_numericas_son_integer(con):
    for r in con.execute("PRAGMA table_info(mensual)"):
        assert r[2] == ("TEXT" if r[1] == "unidad_id" else "INTEGER")
    for r in con.execute("PRAGMA table_info(lote_diario)"):
        assert r[2] == ("TEXT" if r[1] == "lote_id" else "INTEGER")


def test_variables_son_columnas_reales(con):
    cols = {r[1] for r in con.execute("PRAGMA table_info(mensual)")} | {
        r[1] for r in con.execute("PRAGMA table_info(lote_diario)")}
    assert set(VARIABLES) <= cols
    assert all(v.id == k == v.columna for k, v in VARIABLES.items())


@pytest.mark.parametrize("var", VARIABLES.values(), ids=list(VARIABLES))
def test_roundtrip_escala(var):
    x = np.linspace(var.valido_min, var.valido_max, 1001)
    err = np.abs(de_entero(a_entero(x, var), var) - x)
    assert err.max() < var.escala / 2 + 1e-9


@pytest.mark.parametrize("var", VARIABLES.values(), ids=list(VARIABLES))
def test_nan_a_nulo(var):
    assert a_entero(np.array([np.nan]), var)[0] == INT_NULO


@pytest.mark.parametrize("var", VARIABLES.values(), ids=list(VARIABLES))
def test_ningun_valido_coincide_con_relleno(var):
    enteros = a_entero(np.array([var.valido_min, var.valido_max]), var)
    assert var.relleno not in enteros.tolist()
    assert a_entero(np.array([1.0]), var).dtype == np.int32


def test_ids_no_chocan_con_los_de_la_fase_1():
    # el worktree no trae datos: se busca en el checkout principal
    ruta = next((p / "datos/procesados/geo.sqlite"
                 for p in (config.RAIZ, *config.RAIZ.parents) if (p / "datos/procesados/geo.sqlite").exists()), None)
    if ruta is None:
        pytest.skip("sin geo.sqlite")
    ro = sqlite3.connect(f"file:{ruta.as_posix()}?mode=ro", uri=True)
    ids = {r[0] for r in ro.execute("SELECT id FROM variable")}
    assert not ids & set(VARIABLES)
