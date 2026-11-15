# asistido por SI: Cursor (agente), escritura y revisión de código; núcleo del gemelo digital en el hackatón
"""Paquete estático v1.1: indice.json, archivos por lote, rótulo, tarjetas, prioridades y textos."""
import json

import pytest
import yaml

from conftest import RAIZ
from gemelo import paquete
from gemelo.entrada import leer_entrada
from gemelo.tarjetas import SECCIONES
from gemelo.textos import catalogo

ESCENARIO = {
    "version_contrato": 1,
    "lote": {"id": "DEMO-USA-99", "nombre": "Lote de prueba", "lat": 42.03, "lon": -93.63, "clima_tipo": "templado"},
    "clima": {"fuente": "power_csv", "archivo": str(RAIZ / "datos/referencia/clima/power_ames_diario.csv")},
    "suelo": {"fuente": "soilgrids_json", "archivo": str(RAIZ / "datos/referencia/suelo/soilgrids_ames.json")},
    "escenario": {"tipo": "historico", "anios": 2, "max_miembros": 2},
    "simulacion": {"n_parametros": 2, "semilla": 3, "referencia": "A"},
    "estrategias": [
        {"id": "A", "nombre": "Maíz-soya", "temporadas": [
            {"cultivo": "maiz", "siembra": "A1-05-01", "fertilizacion": [{"dia": 0, "kg_n": 150}]},
            {"cultivo": "soya", "siembra": "A2-05-15", "etapas_variante": "centro EE. UU."}]},
        {"id": "B", "nombre": "Maíz continuo", "temporadas": [
            {"cultivo": "maiz", "siembra": "A1-05-01", "fertilizacion": [{"dia": 0, "kg_n": 150}]},
            {"cultivo": "maiz", "siembra": "A2-05-01", "fertilizacion": [{"dia": 0, "kg_n": 150}]}]},
    ],
    "optimizacion": {
        "linea_base": "A",
        "campanias": [{"nombre": "principal", "fecha": "05-01", "opciones": ["maiz", "soya"]}],
        "opciones": {"maiz": {"cultivo": "maiz", "fertilizacion": [{"dia": 0, "kg_n": 150}]},
                     "soya": {"cultivo": "soya", "etapas_variante": "centro EE. UU."}},
        "exigidos": ["maiz"],
        "busqueda": {"poblacion": 6, "generaciones": 2, "miembros_clima": 2, "muestras_parametros": 1,
                     "miembros_final": 2, "muestras_final": 2, "max_soluciones": 3},
    },
    "paquete": {"escenarios": ["historico", "seco"], "escenarios_enso": ["enso_nino"],
                "delta_precip_pct": [-10, 10], "delta_temp_c": [0], "n_parametros_grilla": 2,
                "miembros_clima_sensibilidad": 2,
                "calibraciones_tipicas": {"n_bajo": {"descripcion": "poco N", "valores": {
                    "cn.n_mineral_inicial_kg_ha": 15}}}},
}


@pytest.fixture(scope="module")
def construido(tmp_path_factory):
    tmp = tmp_path_factory.mktemp("paquete")
    yml = tmp / "escenario.yaml"
    yml.write_text(yaml.safe_dump(ESCENARIO, allow_unicode=True), encoding="utf-8")
    salida = tmp / "publicos"
    indice = paquete.construir(yml, "DEMO-USA-99", salida, registro=lambda *_: None)
    return salida, json.loads(indice.read_text(encoding="utf-8"))


@pytest.mark.lento
def test_indice_lista_todos_los_archivos(construido):
    salida, indice = construido
    assert indice["version_contrato"] == 1 and indice["version_contrato_completa"] == "1.2"
    (lote,) = indice["lotes"]
    assert lote["lote_id"] == "DEMO-USA-99" and lote["provisional"] is True
    rutas = [a for e in lote["escenarios"].values() for a in e.values()]
    rutas += [e["simulacion"] for e in lote["escenarios_enso"].values() if "simulacion" in e]
    rutas += [g["archivo"] for g in lote["personalizados"]["archivos"]]
    rutas += [c["archivo"] for c in lote["calibraciones"]]
    assert len(lote["personalizados"]["archivos"]) == 2
    assert set(lote["escenarios"]) == {"historico", "seco"}
    assert all("optimizacion" in e for e in lote["escenarios"].values())
    for r in rutas:
        assert (salida / r).exists(), r
    for idioma in ("en", "es"):
        assert (salida / indice["textos"][idioma]).exists()


@pytest.mark.lento
def test_documentos_del_paquete(construido):
    salida, indice = construido
    (lote,) = indice["lotes"]
    cat = catalogo()
    comparables = lote["conjunto_comparable"]["estrategias"]
    for g in lote["personalizados"]["archivos"]:
        doc = json.loads((salida / g["archivo"]).read_text(encoding="utf-8"))
        assert doc["escenario"]["delta_precip_pct"] == g["delta_precip_pct"]
        assert [e["id"] for e in doc["estrategias"]] == comparables
    doc = json.loads((salida / lote["escenarios"]["historico"]["optimizacion"]).read_text(encoding="utf-8"))
    assert doc["lote"]["id"] == "DEMO-USA-99"
    assert doc["metadatos"]["rotulo"]["en"] == "Model simulation with NASA POWER and SoilGrids 2.0 data"
    assert doc["metadatos"]["rotulo"]["es"] == "Simulación del modelo con datos NASA POWER y SoilGrids 2.0"
    ids = [doc["linea_base"]["id"], *(f["id"] for f in doc["frente"])]
    assert set(doc["tarjetas"]) == set(ids)
    supuestos = {p["clave"] for p in doc["parametros"] if p["etiqueta"] == "SUPUESTO"}
    for t in doc["tarjetas"].values():
        assert set(SECCIONES) <= set(t) and all(t[s] for s in SECCIONES)
        for s in SECCIONES:
            for entrada in t[s]:
                assert entrada["clave"] in cat["en"] and entrada["clave"] in cat["es"]
        for v in t["vacios"]:
            if v["clave"] == "card.gap.changes_order":
                assert v["valores"]["parametro"] in supuestos
    assert set(doc["prioridades"]["pesos_iguales"]["orden"]) == set(ids)
    assert "sensibilidad_supuestos" in doc


def test_lote_demo_valida_formato(tmp_path):
    with pytest.raises(ValueError, match="DEMO-"):
        leer_entrada(dict(ESCENARIO, lote={**ESCENARIO["lote"], "id": "DEMO-col-1"}))
    with pytest.raises(ValueError, match="DEMO-"):
        paquete.construir_lote(RAIZ / "ejemplos/escenario_ames.yaml", "ames-demo", tmp_path)
