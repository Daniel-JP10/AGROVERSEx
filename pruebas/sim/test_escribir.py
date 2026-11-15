# asistido por SI: Claude Code (Anthropic), escritura y revisión de código; base del prototipo migrada en el hackatón
import os
import sqlite3
from pathlib import Path

import numpy as np
import pytest

from simulacion.escribir_sqlite import construir_agroversex, hash_contenido
from simulacion.variables import VARIABLES, de_entero

GEO = Path(os.environ.get("AGROVERSEX_GEO_SQLITE") or Path(__file__).resolve().parents[2] / "datos/procesados/geo.sqlite")
pytestmark = pytest.mark.datos_reales


@pytest.fixture(scope="module")
def agroversex_db(tmp_path_factory):
    ruta = tmp_path_factory.mktemp("agroversex") / "agroversex.sqlite"
    r = construir_agroversex(GEO, ruta, muestra=40, tam_bloque=7, con_lotes=False)
    return ruta, r


def _con(ruta):
    return sqlite3.connect(f"file:{ruta.as_posix()}?mode=ro", uri=True)


SIN_GEO_PROTOTIPO = pytest.mark.skip(reason="depende de geo.sqlite del prototipo, que D-003 no importa; sale con el generador simulado, decisión i")


@SIN_GEO_PROTOTIPO
def test_rangos_y_coherencia(agroversex_db):
    con = _con(agroversex_db[0])
    for col, v in VARIABLES.items():
        if col not in {r[1] for r in con.execute("PRAGMA table_info(mensual)")}:
            continue
        x = de_entero(np.array([r[0] if r[0] is not None else -(2**31) for r in
                                con.execute(f"SELECT {col} FROM mensual")]), v)
        x = x[~np.isnan(x)]
        assert x.min() >= v.valido_min - 1e-6 and x.max() <= v.valido_max + 1e-6, col
    malas = con.execute("SELECT count(*) FROM mensual WHERE t2m_min > t2m OR t2m > t2m_max").fetchone()[0]
    assert malas == 0


@SIN_GEO_PROTOTIPO
def test_tipos_y_nulos(agroversex_db):
    con = _con(agroversex_db[0])
    for col in ("precip", "t2m", "ndvi", "bandera_motivo", "dias_calor"):
        tipos = {r[0] for r in con.execute(f"SELECT DISTINCT typeof({col}) FROM mensual")}
        assert tipos <= {"integer", "null"}, (col, tipos)
    assert con.execute("SELECT count(*) FROM mensual WHERE dias_calor IS NOT NULL").fetchone()[0] == 0
    assert con.execute("SELECT count(*) FROM mensual WHERE precip IN (0) AND precip_frac IS NULL").fetchone()[0] == 0


@SIN_GEO_PROTOTIPO
def test_indices_cubrientes(agroversex_db):
    con = _con(agroversex_db[0])
    plan = " ".join(r[3] for r in con.execute("EXPLAIN QUERY PLAN SELECT unidad_id, precip FROM mensual "
                                              "WHERE mes_id = 100"))
    assert "COVERING INDEX" in plan


@SIN_GEO_PROTOTIPO
def test_padres_y_variables(agroversex_db):
    con = _con(agroversex_db[0])
    assert con.execute("SELECT count(*) FROM unidad WHERE nivel=2 AND padre_id IS NULL AND cruce_ambiguo<>1"
                       ).fetchone()[0] == 0
    assert con.execute("SELECT count(*) FROM variable").fetchone()[0] == 11 + len(VARIABLES) + 3
    assert con.execute("SELECT valor FROM metadatos WHERE clave='hash_contenido'").fetchone()[0] == agroversex_db[1]["hash"]


@SIN_GEO_PROTOTIPO
def test_reproducible_y_bloque(agroversex_db, tmp_path):
    r = construir_agroversex(GEO, tmp_path / "b.sqlite", muestra=40, tam_bloque=40, con_lotes=False)
    assert r["hash"] == agroversex_db[1]["hash"] == hash_contenido(tmp_path / "b.sqlite")


@SIN_GEO_PROTOTIPO
def test_invariancia_bloque_300(tmp_path):
    a = construir_agroversex(GEO, tmp_path / "a.sqlite", muestra=300, tam_bloque=50, con_lotes=False)
    b = construir_agroversex(GEO, tmp_path / "b.sqlite", muestra=300, tam_bloque=200, con_lotes=False)
    assert a["hash"] == b["hash"]


def test_precip_mm_h_ida_y_vuelta():
    from simulacion.escribir_sqlite import a_mm_h
    from simulacion.variables import a_entero
    m = np.zeros((1, 323)); m[0, 3] = 720.0  # abril de 2000: 30 días = 720 h
    h = a_mm_h(m)
    assert h[0, 3] == pytest.approx(1.0)
    v = VARIABLES["precip"]
    assert de_entero(a_entero(h, v), v)[0, 3] == pytest.approx(1.0, abs=v.escala)
