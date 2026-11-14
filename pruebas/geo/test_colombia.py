# asistido por SI: Claude Code (Anthropic), pruebas de la comparación de Colombia con DIVIPOLA (T-D1)
import pandas as pd

from simulacion.geo.colombia import comparar_divipola


def _cgaz(filas):
    return pd.DataFrame(filas, columns=["unidad_id", "nombre", "dpto"])


def _dane(filas):
    return pd.DataFrame(filas, columns=["cod_mpio", "nom_mpio", "dpto", "tipo_municipio"])


def test_exactos_variantes_y_diferencias():
    cgaz = _cgaz([("c1", "Pasto", "Nariño"), ("c2", "Santuario", "Antioquia"),
                  ("c3", "Mapiripana", "Guainía"), ("c4", "Bogotá, D.c.", "Bogota Capital District")])
    dane = _dane([("52001", "PASTO", "NARIÑO", "Municipio"), ("05697", "EL SANTUARIO", "ANTIOQUIA", "Municipio"),
                  ("94001", "INÍRIDA", "GUAINÍA", "Municipio"), ("11001", "BOGOTÁ, D.C.", "BOGOTÁ, D.C.", "Municipio")])
    r = comparar_divipola(cgaz, dane)
    assert r["cgaz"] == 4 and r["dane"] == 4
    assert r["exactos"] == 2  # Pasto y Bogotá (el departamento se empareja por nombre parecido)
    assert [p["cgaz"] for p in r["variantes"]] == ["Santuario"]
    assert r["sobran_en_cgaz"] == ["Mapiripana"] and r["faltan_en_cgaz"] == ["INÍRIDA"]
    # único resto del departamento: se propone como candidato pero sigue contando como diferencia
    assert [(p["cgaz"], p["dane"]) for p in r["candidatos_por_exclusion"]] == [("Mapiripana", "INÍRIDA")]


def test_ipiales_en_narino():
    from simulacion.geo.colombia import padre_de
    u = pd.DataFrame({"unidad_id": ["n", "i"], "nombre": ["Nariño", "Ipiales"], "padre_id": [None, "n"]})
    assert padre_de(u, "Ipiales") == "Nariño"


def test_contiene_y_exclusion_por_departamento():
    cgaz = _cgaz([("c1", "Cali", "Valle del Cauca"), ("c2", "Buga", "Valle del Cauca"),
                  ("c3", "Distrito Especial, Industrial Y Portuario De Barr*", "Atlántico"),
                  ("c4", "Soledad", "Atlántico")])
    dane = _dane([("76001", "SANTIAGO DE CALI", "VALLE DEL CAUCA", "Municipio"),
                  ("76111", "GUADALAJARA DE BUGA", "VALLE DEL CAUCA", "Municipio"),
                  ("08001", "BARRANQUILLA", "ATLÁNTICO", "Municipio"), ("08758", "SOLEDAD", "ATLÁNTICO", "Municipio")])
    r = comparar_divipola(cgaz, dane)
    assert {v["cgaz"]: v["metodo"] for v in r["variantes"]} == {"Cali": "contiene", "Buga": "contiene"}
    assert r["exactos"] == 1
    assert r["sobran_en_cgaz"] == ["Distrito Especial, Industrial Y Portuario De Barr*"]
    assert r["faltan_en_cgaz"] == ["BARRANQUILLA"]
    assert r["candidatos_por_exclusion"][0]["dane"] == "BARRANQUILLA"
