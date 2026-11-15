# asistido por SI: Cursor (agente), escritura y revisión de código; núcleo del gemelo digital en el hackatón
"""El documento JSON cumple contratos/gemelo_api.md: claves, unidades, percentiles, procedencia y avisos."""
import json
import sqlite3

import pytest

from conftest import RAIZ
from gemelo.api import definiciones, simular
from gemelo.cli import main
from gemelo.entrada import leer_entrada
from gemelo.salida import AVISO_SIMULADO, guardar_json, guardar_sqlite

ESCENARIO = {
    "version_contrato": 1,
    "lote": {"id": "prueba", "nombre": "Lote de prueba", "lat": 42.03, "lon": -93.63, "clima_tipo": "templado"},
    "clima": {"fuente": "power_csv", "archivo": str(RAIZ / "datos/referencia/clima/power_ames_diario.csv")},
    "suelo": {"fuente": "soilgrids_json", "archivo": str(RAIZ / "datos/referencia/suelo/soilgrids_ames.json")},
    "escenario": {"tipo": "historico", "anios": 2, "max_miembros": 2},
    "simulacion": {"n_parametros": 2, "semilla": 3, "referencia": "B"},
    "calibracion": {"cn.n_mineral_inicial_kg_ha": 25},
    "costos": {"moneda": "USD", "riego_por_mm": 0.5, "n_por_kg": 1.2, "labranza": 30,
               "semilla": {"maiz": 250, "soya": 120}},
    "estrategias": [
        {"id": "A", "nombre": "Maíz continuo", "temporadas": [
            {"cultivo": "maiz", "siembra": "A1-05-01", "fertilizacion": [{"dia": 0, "kg_n": 150}]},
            {"cultivo": "maiz", "siembra": "A2-05-01", "fertilizacion": [{"dia": 0, "kg_n": 150}],
             "riego": {"modo": "automatico", "tope_mm": 100}}]},
        {"id": "B", "nombre": "Maíz-soya", "temporadas": [
            {"cultivo": "maiz", "siembra": "A1-05-01", "fertilizacion": [{"dia": 0, "kg_n": 150}]},
            {"cultivo": "soya", "siembra": "A2-05-15", "etapas_variante": "centro EE. UU."}]},
    ],
}


@pytest.fixture(scope="module")
def doc():
    return simular(ESCENARIO)


def test_estructura_del_documento(doc):
    for k in ("metadatos", "lote", "clima", "escenario", "suelo", "parametros", "estrategias", "comparacion_p50",
              "avisos"):
        assert k in doc
    m = doc["metadatos"]
    assert m["version_contrato"] == 1 and m["naturaleza"] == "simulado" and m["semilla"] == 3
    assert m["miembros"] == {"estrategias": 2, "clima": 2, "parametros": 2, "total": 8}
    assert m["carbono"]["estrategia_referencia"] == "B"
    assert len(m["huella_parametros"]) == 16
    assert AVISO_SIMULADO in doc["avisos"]
    json.dumps(doc, allow_nan=False)


def test_indicadores_con_percentiles_y_unidades(doc):
    for e in doc["estrategias"]:
        for k, v in e["indicadores"].items():
            assert {"p10", "p50", "p90", "unidad", "definicion"} <= set(v), k
            if v["p50"] is not None:
                assert v["p10"] <= v["p50"] <= v["p90"]
        assert e["indicadores"]["cierre_balance_agua_mm"]["p90"] < 1e-9
        assert len(e["estado_final_p50"]) == 5
        assert len(e["trayectoria_mensual"]["W"]["p50"]) == 24
        for t in e["temporadas"]:
            assert t["siembra"].startswith("A") and "cosecha" in t and len(t["etapas_dias"]) == 4
    costo = doc["estrategias"][0]["indicadores"]["costo_anio"]
    assert costo["p50"] > 0


def test_procedencia_de_parametros(doc):
    claves = {p["clave"]: p for p in doc["parametros"]}
    assert claves["cn.n_mineral_inicial_kg_ha"]["etiqueta"] == "FUENTE"
    assert claves["cn.n_mineral_inicial_kg_ha"]["naturaleza"] == "observado"
    assert claves["cultivo.maiz.kc_mid"]["ficha"] == "EV-ROT-010"
    for p in doc["parametros"]:
        assert p["etiqueta"] in ("FUENTE", "INFERENCIA", "SUPUESTO") and p["unidad"]


def test_costo_pendiente_sin_precios():
    d = dict(ESCENARIO, costos=None)
    doc = simular(d)
    c = doc["estrategias"][0]["indicadores"]["costo_anio"]
    assert c["p50"] is None and c["etiqueta"] == "PENDIENTE"


def test_guardar_json_y_sqlite(doc, tmp_path):
    ruta = guardar_json(doc, tmp_path / "x.json")
    assert json.loads(ruta.read_text(encoding="utf-8"))["metadatos"]["tipo"] == "simulacion"
    cid = guardar_sqlite(doc, tmp_path / "g.sqlite")
    con = sqlite3.connect(tmp_path / "g.sqlite")
    n = con.execute("SELECT COUNT(*) FROM indicador WHERE corrida_id = ?", (cid,)).fetchone()[0]
    p50 = con.execute("SELECT p50 FROM indicador WHERE estrategia_id = 'A' AND indicador = 'riego_mm_anio'").fetchone()
    con.close()
    assert n == sum(len(e["indicadores"]) for e in doc["estrategias"])
    assert p50[0] == doc["estrategias"][0]["indicadores"]["riego_mm_anio"]["p50"]


def test_errores_de_entrada_claros():
    with pytest.raises(ValueError, match="version_contrato"):
        leer_entrada(dict(ESCENARIO, version_contrato=99))
    with pytest.raises(ValueError, match="repetidos"):
        leer_entrada(dict(ESCENARIO, estrategias=ESCENARIO["estrategias"] + [ESCENARIO["estrategias"][0]]))
    with pytest.raises(KeyError):
        simular(dict(ESCENARIO, simulacion={"referencia": "Z"}))
    with pytest.raises(ValueError, match="fecha nominal"):
        leer_entrada(dict(ESCENARIO, estrategias=[{"id": "X", "temporadas": [{"cultivo": "maiz", "siembra": "1-5"}]}]))


def test_cli_y_definiciones(capsys):
    assert main(["cultivos"]) == 0
    assert "trebol_berseem" in capsys.readouterr().out
    d = definiciones()
    assert "produccion_relativa_anio" in d["indicadores"] and "carbono" in d["objetivos"]
    assert main(["simular", str(RAIZ / "no_existe.yaml"), "-o", "x.json"]) == 2
