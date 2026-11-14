# asistido por SI: Claude Code (Anthropic), pruebas de la orientación de lecturas netCDF con puntos de control (T-D2)
import os
from pathlib import Path

import numpy as np
import pytest

from simulacion.geo import lectura_nasa as L


def _imerg_sintetico():
    # verdad en (lat, lon) norte arriba: Chocó, Borneo, Amazonia, Congo, Pacífico oeste húmedos; desiertos secos
    g = L.GRILLAS["imerg"]
    v = np.full((g.alto, g.ancho), 0.2)
    for la, lo, val in [(23, 10, 0.0), (22, 45, 0.0), (-24, -69, 0.0)]:
        v[int((g.y0 - la) / g.dy), int((lo - g.x0) / g.dx)] = val
    return v


def test_imerg_con_el_primer_eje_espejado_se_recupera_con_los_controles():
    verdad = _imerg_sintetico()
    # lo que entrega GDAL: (lon, lat) con lat creciente y el primer eje (lon) espejado
    crudo = verdad[::-1].T[::-1]
    a, regla = L.orientar(crudo, "imerg_final", 1)
    assert regla == (True, True, True) and np.array_equal(a, verdad)


def test_lectura_sin_voltear_no_pasa_los_controles():
    verdad = _imerg_sintetico()
    mal = verdad[::-1].T  # lat creciente, lon en orden normal: no es lo que da GDAL
    a, regla = L.orientar(mal, "imerg_final", 1)
    assert np.array_equal(a, verdad)  # igual la deduce: pone cada punto donde la física lo exige
    with pytest.raises(RuntimeError):
        L.orientar(np.full_like(verdad.T, 0.2), "imerg_final", 1)  # campo uniforme: ninguna variante pasa


@pytest.mark.datos_reales
def test_orientacion_de_cada_producto_con_datos_reales():
    base = os.environ.get("AGRO_COPIA")
    if not base or not (Path(base) / "crudos").exists():
        pytest.skip("sin copia de crudos en WSL (AGRO_COPIA)")
    esperado = {"imerg_final": (True, True, True), "t2m": (False,) * 3, "humedad_radicular": (False,) * 3,
                "ndvi": (False, True, False)}
    for prod, regla in esperado.items():
        archivos = L.archivos(Path(base) / "crudos", prod)
        mes = sorted(archivos)[0]
        assert L.leer_campo(archivos[mes], prod, int(mes[5:]))[1] == regla
