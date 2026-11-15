# asistido por SI: Claude Code (Anthropic), escritura y revisión de código; base del prototipo migrada en el hackatón
"""Escritura de clim_normal.sqlite (la estadística zonal corre en WSL y se prueba con datos reales)."""
import sqlite3

import pandas as pd

from simulacion import clima
from simulacion.geo import clim_normal


def test_escribir_y_releer_con_clima(tmp_path):
    filas = pd.DataFrame({"unidad_id": ["A"] * 12 + ["B"] * 12, "mes": list(range(1, 13)) * 2, "tavg": 10.0,
                          "tmin": 5.0, "tmax": 15.0, "prec": 50.0, "srad": 15000.0, "fraccion_valida": 1.0})
    filas.loc[filas.unidad_id == "B", ["tavg", "fraccion_valida"]] = [None, 0.0]  # isla sin celda
    ruta = tmp_path / "clim_normal.sqlite"
    clim_normal.escribir(ruta, filas)
    con = sqlite3.connect(ruta)
    assert con.execute("SELECT count(*) FROM clim_normal").fetchone()[0] == 24
    assert "PRIMARY KEY" in con.execute("SELECT sql FROM sqlite_master WHERE name='clim_normal'").fetchone()[0]
    con.close()
    mat, tiene = clima._matrices_normales(clima.cargar_normales(ruta), ["A", "B", "C"])
    assert tiene.tolist() == [True, False, False]  # B con NULL y C ausente caen al respaldo
