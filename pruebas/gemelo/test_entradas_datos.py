# asistido por SI: Cursor (agente), escritura y revisión de código; núcleo del gemelo digital en el hackatón
# asistido por SI: Antigravity (agente), prueba de esquema T-D5 anidado en parametros_suelo.json
"""Entradas de Datos (forzantes diarios y parametros_suelo.json) y escenarios por fase ENSO (v1.1)."""
import json
import sqlite3

import numpy as np
import pandas as pd
import pytest

from conftest import RAIZ
from gemelo.api import simular
from gemelo.clima import DIAS_MES, leer_power_csv, mensual_desde_sqlite
from gemelo.textos import clave_de_aviso
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
        huecos_rellenos, naturaleza, avisos = {}, "derivado", []
        fuente = "agroversex.sqlite clima mensual (X), desagregado a diario"

    class _E:
        clima, escenario = _C(), type("e", (), {"aviso": "", "detalle": {}})()

    class _T:
        avisos = []

    class _Ens:
        theta, equilibrio = _T(), "ninguno"
    assert AVISO_MENSUAL in _avisos(_E(), _Ens())


def _sqlite_serie(ruta, filas):
    con = sqlite3.connect(ruta)
    con.execute("CREATE TABLE unidad (id TEXT, punto_lat REAL)")
    con.execute("INSERT INTO unidad VALUES ('U', 0.84)")
    con.execute("CREATE TABLE serie_mensual (unidad_id TEXT, variable TEXT, mes_id INTEGER, valor REAL, "
                "nivel TEXT, unidad TEXT, motivo TEXT)")
    con.executemany("INSERT INTO serie_mensual VALUES ('U', ?, ?, ?, ?, ?, ?)", filas)
    con.commit()
    con.close()


def test_serie_mensual_usa_la_columna_unidad(tmp_path):
    filas = []
    for m in range(24):
        dias = DIAS_MES[m % 12]
        # 2000: IMERG Final en mm/hr; 2001: Late en mm/day. Ambos equivalen a 3 mm/día.
        lluvia = ("final", "mm/hr", 3 / 24) if m < 12 else ("late", "mm/day", 3.0)
        filas.append(("precip", m, lluvia[2], lluvia[0], lluvia[1], "IMERG Late, Final no disponible" if m == 13
                      else None))
        filas += [("t2m_max", m, 295.15, "power", "K", None), ("t2m_min", m, 10.0, "power", "°C", None),
                  ("rad_sw", m, 200.0, "power", "W/m^2", None)]
    filas.append(("precip", 13, 99.0, "final", "mm/hr", "duplicado con motivo"))
    ruta = tmp_path / "a.sqlite"
    _sqlite_serie(ruta, filas)
    mensual, anios, lat, avisos = mensual_desde_sqlite(ruta, "U")
    assert list(anios) == [2000, 2001] and lat == pytest.approx(0.84)
    np.testing.assert_allclose(mensual["precip"], 3.0 * np.tile(DIAS_MES, (2, 1)))
    np.testing.assert_allclose(mensual["t2m_max"], 22.0)
    np.testing.assert_allclose(mensual["rad_sw"], 17.28)
    assert any("motivo" in a for a in avisos) and any("mm/day, mm/hr" in a for a in avisos)
    assert all(clave_de_aviso(a)["clave"] != "warning.untranslated" for a in avisos)


def test_serie_mensual_unidad_desconocida_es_error(tmp_path):
    ruta = tmp_path / "b.sqlite"
    _sqlite_serie(ruta, [("precip", 0, 1.0, "final", "in/hr", None)])
    with pytest.raises(ValueError, match="unidad de precipitación desconocida"):
        mensual_desde_sqlite(ruta, "U")


def test_parametros_suelo_anidados_td5(forzantes, tmp_path):
    from gemelo.suelo import perfil_desde_parametros_datos
    datos_td5 = {
        "lote_id": "DEMO-COL-01",
        "fuente": "SoilGrids 2.0 (ISRIC), API REST rest.isric.org",
        "naturaleza": "estimado",
        "parametros": {
            "arena": {"valor": 0.3921, "rango": [0.14, 0.6335], "unidad": "kg/kg", "etiqueta": "FUENTE",
                      "profundidad_cm": [0, 100]},
            "arcilla": {"valor": 0.28325, "rango": [0.03435, 0.6958], "unidad": "kg/kg", "etiqueta": "FUENTE",
                        "profundidad_cm": [0, 100]},
            "densidad_aparente": {"valor": 1.1815, "rango": [0.579, 1.6645], "unidad": "kg/dm3",
                                  "etiqueta": "FUENTE", "profundidad_cm": [0, 100]},
            "mo_pct": {"valor": 7.4793, "rango": [0.4836, 23.8181], "unidad": "%", "etiqueta": "INFERENCIA",
                       "profundidad_cm": [0, 100], "metodo": "MO = COS/0,58"},
            "cos_t_ha": {"valor": 186.999, "rango": [8.7185, 770.174], "unidad": "t C/ha", "etiqueta": "FUENTE",
                         "profundidad_cm": [0, 30]},
            "agua_disponible_mm_m": {"valor": 165.7, "rango": [0.0, 461.3], "unidad": "mm de agua por m de suelo",
                                     "etiqueta": "INFERENCIA", "profundidad_cm": [0, 100]},
        },
    }
    ruta = tmp_path / "parametros_suelo_td5.json"
    ruta.write_text(json.dumps(datos_td5), encoding="utf-8")
    perfil = perfil_desde_parametros_datos(ruta)
    assert perfil.valor("arena") == pytest.approx(0.3921)
    assert perfil["arena"].rango == pytest.approx((0.14, 0.6335))
    assert perfil["arena"].distribucion == "triangular"
    assert perfil["mo_pct"].etiqueta == "INFERENCIA"
    assert perfil["mo_pct"].naturaleza == "estimado"
    assert perfil.valor("densidad_aparente") == pytest.approx(1.1815)
    assert not any("fuera de dominio" in a for a in perfil.avisos)
    assert any("SoilGrids" in a and "Andisoles" in a for a in perfil.avisos)

    d = dict(ESCENARIO, clima={"fuente": "forzantes_diarios", "archivo": str(forzantes), "lat": 0.842,
                               "elevacion_m": 2934},
             suelo={"fuente": "parametros_suelo_json", "archivo": str(ruta)}, costos=None)
    doc = simular(d)
    assert doc["metadatos"]["rotulo"]["parametros"]["fuentes"] == ["source.datos_forcings", "source.datos_soil"]

    incompleto = tmp_path / "incompleto.json"
    incompleto.write_text(json.dumps({"parametros": {"arena": {"valor": 0.3}}}), encoding="utf-8")
    with pytest.raises(ValueError, match="faltan"):
        perfil_desde_parametros_datos(incompleto)
