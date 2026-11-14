# asistido por SI: Claude Code, pruebas de la lectura puntual de IMERG diario (T-D5 Parte B)
import math

import pytest

from lotes_demo.imerg_diario import indices_celda, parsear_ascii, url_dia

ASCII = """Dataset: x.nc4
precipitation.lat, 40.95
precipitation.precipitation[precipitation.time=16232][precipitation.lon=102.95], 0
precipitation_cnt.precipitation_cnt[precipitation_cnt.time=16232][precipitation_cnt.lon=102.95], 48
"""


def test_indices_celda_usa_y_colombia():
    # centro de celda de 0,1 grados: el punto debe caer dentro de la celda
    assert indices_celda(41.165, -96.477) == (835, 1311)
    assert indices_celda(0.842, -77.661) == (1023, 908)


def test_parsear_ascii_lluvia_y_conteo():
    assert parsear_ascii(ASCII) == (0.0, 48.0)


def test_relleno_es_nan_no_cero():
    t = ASCII.replace(", 0\n", ", -9999.9\n")
    p, _ = parsear_ascii(t)
    assert math.isnan(p)


def test_url_dia_lleva_version_y_fecha():
    u = url_dia("2024-06-15", 835, 1311)
    assert "GPM_3IMERGDF.07/2024/06/" in u and "20240615" in u and "[835:835][1311:1311]" in u


def test_indices_fuera_de_rango():
    with pytest.raises(ValueError):
        indices_celda(95.0, 0.0)
