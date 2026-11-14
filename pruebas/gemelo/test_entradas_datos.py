# asistido por SI: Cursor (agente), escritura y revisión de código; núcleo del gemelo digital en el hackatón
"""Entradas de Datos (forzantes diarios y parametros_suelo.json) y escenarios por fase ENSO (v1.1)."""
import json

import pandas as pd
import pytest

from conftest import RAIZ
from gemelo.api import simular
from gemelo.clima import leer_power_csv
from gemelo.enso import FASES, clasificar_oni, fases_por_anio
from gemelo.entrada import leer_entrada
from gemelo.escenarios import construir
from test_contrato import ESCENARIO


@pytest.fixture(scope="module")
def forzantes(tmp_path_factory):
    """CSV con el formato esperado de Datos, armado desde el POWER de Ames (mismas variables y unidades)."""
    df, _ = leer_power_csv(RAIZ / "datos/referencia/clima/power_ames_diario.csv")
    ruta = tmp_path_factory.mktemp("datos") / "forzantes.csv"
    df.assign(fecha=df.fecha.dt.strftime("%Y-%m-%d")).to_csv(ruta, index=False)
    return ruta


def test_forzantes_diarios_y_suelo_de_datos(forzantes, tmp_path):
    suelo = tmp_path / "parametros_suelo.json"
    suelo.write_text(json.dumps({"arena": 0.3, "arcilla": 0.25, "mo_pct": 3.5, "cos_t_ha": 70, "cn_suelo": 11,
                                 "fuente": "SoilGrids 2.0 zonal"}), encoding="utf-8")
    d = dict(ESCENARIO, clima={"fuente": "forzantes_diarios", "archivo": str(forzantes), "lat": 42.03,
                               "elevacion_m": 300},
             suelo={"fuente": "parametros_suelo_json", "archivo": str(suelo)}, costos=None)
    e = leer_entrada(d)
    assert e.clima.naturaleza == "estimado" and e.clima.n_anios >= 10
    assert e.suelo["arena"].naturaleza == "estimado"
    doc = simular(d)
    assert doc["metadatos"]["rotulo"]["parametros"]["fuentes"] == ["source.datos_forcings", "source.datos_soil"]


def test_forzantes_sin_columnas_es_error(tmp_path):
    ruta = tmp_path / "malo.csv"
    pd.DataFrame({"fecha": ["2020-01-01"], "precip": [1.0]}).to_csv(ruta, index=False)
    with pytest.raises(ValueError, match="faltan"):
        leer_entrada(dict(ESCENARIO, clima={"fuente": "forzantes_diarios", "archivo": str(ruta), "lat": 0,
                                            "elevacion_m": 0}))


def test_clasificacion_oni_interina():
    fases = clasificar_oni()
    assert fases[2015] == "nino" and fases[2010] in FASES and fases[2022] == "nina"
    _, meta = fases_por_anio()
    assert meta["interina"] and meta["etiqueta"] == "INFERENCIA"


def test_clasificacion_de_datos_reemplaza_la_interina(tmp_path, clima_ames):
    ruta = tmp_path / "fases.json"
    ruta.write_text(json.dumps({str(a): "nina" for a in clima_ames.anios}), encoding="utf-8")
    esc = construir(clima_ames, "enso_nina", 2, enso_archivo=str(ruta))
    assert esc.detalle["clasificacion_enso"]["interina"] is False
    assert len(esc.detalle["anios_analogos"]) == clima_ames.n_anios
    with pytest.raises(ValueError, match="ningún año"):
        construir(clima_ames, "enso_nino", 2, enso_archivo=str(ruta))


def test_escenario_enso_y_resultados_por_fase(clima_ames):
    fases, _ = fases_por_anio()
    esc = construir(clima_ames, "enso_nino", 2)
    assert all(fases[int(clima_ames.anios[i])] == "nino" for m in esc.miembros for i in m)
    doc = simular(dict(ESCENARIO, costos=None, escenario={"tipo": "historico", "anios": 2, "max_miembros": 6}))
    g = doc["indicadores_por_fase_enso"]
    n = sum(v["n_miembros"] for v in g["estrategias"]["A"].values())
    assert n == doc["estrategias"][0]["n_miembros"]
    assert g["clasificacion"]["interina"] is True


def test_sqlite_mensual_avisa_que_es_solo_contexto():
    from gemelo.salida import AVISO_MENSUAL, _avisos

    class _C:
        huecos_rellenos, naturaleza = {}, "derivado"
        fuente = "agroversex.sqlite tabla mensual (X), desagregado a diario"

    class _E:
        clima, escenario = _C(), type("e", (), {"aviso": "", "detalle": {}})()

    class _T:
        avisos = []

    class _Ens:
        theta, equilibrio = _T(), "ninguno"
    assert AVISO_MENSUAL in _avisos(_E(), _Ens())
