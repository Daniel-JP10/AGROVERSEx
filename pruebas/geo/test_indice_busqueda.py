# asistido por SI: Claude Code (Anthropic), pruebas del índice de búsqueda sobre unidades CGAZ (T-D1)
import gzip
import json

import pandas as pd
import pytest

from simulacion.geo.indice_busqueda import construir_indice, escribir_indice

COLS = ["unidad_id", "nivel", "iso3", "padre_id", "nombre", "nombre_ascii", "es_disputa", "nivel_real"]
UNIDADES = pd.DataFrame([
    ("COL-ADM0", 0, "COL", None, "Colombia", "Colombia", 0, "ADM0"),
    ("COL-ADM1-1", 1, "COL", "COL-ADM0", "Antioquia", "Antioquia", 0, "ADM1"),
    ("COL-ADM1-2", 1, "COL", "COL-ADM0", "Bolívar", "Bolivar", 0, "ADM1"),
    ("COL-ADM2-1", 2, "COL", "COL-ADM1-1", "Bolívar", "Bolivar", 0, "ADM2"),
    ("COL-ADM2-2", 2, "COL", "COL-ADM1-2", "Bolívar", "Bolivar", 0, "ADM2"),
    ("111-ADM0", 0, "111", None, "Abyei", "Abyei", 1, "DISP"),
    ("111-ADM2-DIS001", 2, "111", "111-ADM0", "Abyei", "Abyei", 1, "DISP"),
    ("AND-ADM2-1", 2, "COL", "COL-ADM1-1", "Repetida", "Repetida", 0, "ADM1"),
    ("COL-ADM2-9", 2, "COL", None, "Huérfana", "Huerfana", 0, "ADM2"),
], columns=COLS)


def _por_id(ne=None):
    return {f["id"]: f for f in construir_indice(UNIDADES, ne)}


def test_contexto_distingue_los_bolivar():
    filas = _por_id()
    assert filas["COL-ADM2-1"]["ctx"] == "Antioquia · Colombia"
    assert filas["COL-ADM2-2"]["ctx"] == "Bolívar · Colombia"
    assert filas["COL-ADM1-1"]["ctx"] == "Colombia"
    assert filas["COL-ADM0"]["ctx"] == ""


def test_ascii_normalizado_y_sin_es_en():
    filas = _por_id()
    assert filas["COL-ADM2-1"]["a"] == "bolivar"
    assert "es" not in filas["COL-ADM2-1"] and "en" not in filas["COL-ADM2-1"]


def test_zona_en_disputa_lleva_marca_y_contexto():
    f = _por_id()["111-ADM0"]
    assert f["ctx"] == "Zona en disputa" and f["d"] == 1 and f["nivel"] == 0
    assert "d" not in _por_id()["COL-ADM0"]
    assert len(_por_id()) == 7


def test_filas_que_repiten_un_nivel_superior_no_se_indexan():
    # la capa ADM2 repite el nivel 1 donde no hay municipios, y las zonas en disputa salen en los tres niveles
    ids = set(_por_id())
    assert "AND-ADM2-1" not in ids and "111-ADM2-DIS001" not in ids and "111-ADM0" in ids


def test_padre_nulo_completa_pais_por_iso3():
    assert _por_id()["COL-ADM2-9"]["ctx"] == "Colombia"


def test_escritura_y_lectura_de_vuelta(tmp_path):
    filas = construir_indice(UNIDADES)
    ruta = tmp_path / "salida" / "indice.json.gz"
    n = escribir_indice(filas, ruta)
    assert n == ruta.stat().st_size
    assert json.loads(gzip.decompress(ruta.read_bytes())) == filas


def test_indice_reproducible_por_hash(tmp_path):
    import hashlib
    h = []
    for i in range(2):
        ruta = tmp_path / f"i{i}.json.gz"
        escribir_indice(construir_indice(UNIDADES), ruta)
        h.append(hashlib.sha256(ruta.read_bytes()).hexdigest())
    assert h[0] == h[1]


def test_nombres_ne_completan_nivel_0():
    ne = {"COL": ("Colombia NE", "Colombia EN"), "CIV": ("Costa de Marfil", "Ivory Coast")}
    t = pd.concat([UNIDADES, pd.DataFrame([("CIV-ADM0", 0, "CIV", None, "Côte d'Ivoire", "Cote d'Ivoire", 0, "ADM0")], columns=COLS)])
    filas = {f["id"]: f for f in construir_indice(t, ne)}
    assert filas["CIV-ADM0"]["es"] == "Costa de Marfil" and filas["CIV-ADM0"]["en"] == "Ivory Coast"
    assert filas["COL-ADM0"]["es"] == "Colombia NE"
    assert "es" not in filas["COL-ADM2-2"]  # solo el nivel 0


@pytest.mark.datos_reales
def test_kosovo_xkx_encuentra_su_nombre_en_ne():
    from simulacion.geo.indice_busqueda import NE_ADMIN0, nombres_paises
    from simulacion.geo.normalizar import normalizar_nombre
    if not NE_ADMIN0.exists():
        pytest.skip("sin ne_10m_admin_0_countries.zip en datos/crudos")
    ne = nombres_paises()
    assert normalizar_nombre(ne["CIV"][0]) == "costa de marfil"
    assert ne["XKX"] == ne["KOS"] and ne["FRA"][0] == "Francia"
