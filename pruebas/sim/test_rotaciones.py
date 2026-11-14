# asistido por SI: Claude Code (Anthropic), escritura y revisión de código; base del prototipo migrada en el hackatón
import sqlite3
from pathlib import Path

import pytest

from simulacion import config, rotaciones
from simulacion.referencias.cargar import cargar_kluger
from simulacion.variables import crear_esquema

EVIDENCIA = config.RAIZ / "evidencia"
CONTRASTE = "contraste, no rotación"


def _sistemas():
    return rotaciones.filas_sistema_rotacion()


def _por_region(filas, prefijo):
    return [f for f in filas if f[1].startswith(prefijo)]


def test_diez_regiones_y_estados():
    filas = _sistemas()
    assert len({f[1] for f in filas}) == 10
    # R-4: Llanos y Andina pasan a FUENTE con alternativa; Pampa sigue PENDIENTE
    for prefijo in ("Llanos", "Andina Colombia"):
        (fila,) = _por_region(filas, prefijo)
        assert fila[3] and fila[6] == "FUENTE"
    assert {f[6] for f in _por_region(filas, "Pampa")} == {"PENDIENTE"}
    assert [f[6] for f in _por_region(filas, "Europa")] == ["INFERENCIA"]


def test_pampa_dos_mas_contraste():
    pampa = _por_region(_sistemas(), "Pampa")
    contrastes = [f for f in pampa if CONTRASTE in f]
    reales = [f for f in pampa if CONTRASTE not in f]
    assert len(contrastes) == 1
    assert len(reales) == 1
    # la Pampa quedó PENDIENTE (R-4): sin estrategia inventada, el contraste va en fila aparte
    assert reales[0][2] is None and reales[0][3] is None and reales[0][6] == "PENDIENTE"


@pytest.mark.skipif(not EVIDENCIA.exists(), reason="sin carpeta evidencia/")
def test_ninguna_estrategia_inventada():
    for f in _sistemas():
        if f[6] != "PENDIENTE":
            assert f[5] is not None
            assert (EVIDENCIA / f"{f[5]}.yaml").exists()


def test_sin_sistemas_ni_filas_de_procedencia_china():
    assert not any("china" in f[0].lower() or "china" in f[1].lower() for f in _sistemas())
    ante = rotaciones.filas_efecto_antecesor()
    assert len(ante) == 34
    assert not any("china" in f[0].lower() for f in ante)
    assert "procedencia_china" not in cargar_kluger().columns
    assert not hasattr(rotaciones, "REGION_CHINA") and not hasattr(rotaciones, "ROTULO_CHINA")


def test_kluger_significativo_es_mascara_de_cuatro_banderas():
    # bit 0 efecto2, bit 1 eff_div, bit 2 beta_lluvia, bit 3 beta_t
    filas = rotaciones.filas_efecto_antecesor()
    assert all(0 <= f[7] <= 15 for f in filas)
    # primera fila de Kluger: las cuatro banderas en True
    assert filas[0][7] == 15


def test_cultivo_fao56_valores():
    cultivos = {f[1]: f for f in rotaciones.filas_cultivo()}
    assert len(cultivos) == 15
    maiz = cultivos["Maíz grano"]
    assert maiz[4] == "1,20"  # kc_mid
    assert maiz[9] == 0.55  # p
    assert cultivos["Café"][10] is None  # agua_min sin FAO-56
    assert "PENDIENTE" in cultivos["Café"][17]


def test_intervalos_sanitarios():
    reglas = rotaciones.filas_regla_sucesion()
    papa = [r for r in reglas if r[0] == "Papa" and r[1] == "Verticillium"]
    assert (papa[0][2], papa[0][3]) == (3.0, 4.0)
    brasicas = [r for r in reglas if r[0].startswith("Brásicas") and r[1] == "Hernia"]
    assert (brasicas[0][2], brasicas[0][3]) == (4.0, 7.0)  # rango, no promedio


def test_sin_analogos_sin_decision():
    assert rotaciones.DECISION_15_2_H is None
    assert all(f[15] is None for f in rotaciones.filas_cultivo())
    ids = " ".join(f[0].lower() for f in rotaciones.filas_cultivo())
    assert not any(n in ids for n in ("centeno", "veza", "mucuna", "canavalia", "crotalaria", "rábano"))


def test_filas_entran_en_el_esquema_sin_error():
    con = sqlite3.connect(":memory:")
    crear_esquema(con)
    tablas = {
        "sistema_rotacion": rotaciones.filas_sistema_rotacion(),
        "efecto_antecesor": rotaciones.filas_efecto_antecesor(),
        "cultivo": rotaciones.filas_cultivo(),
        "regla_sucesion": rotaciones.filas_regla_sucesion(),
    }
    for tabla, filas in tablas.items():
        marcas = ",".join("?" * len(filas[0]))
        con.executemany(f"INSERT INTO {tabla} VALUES ({marcas})", filas)
        assert con.execute(f"SELECT COUNT(*) FROM {tabla}").fetchone()[0] == len(filas)
