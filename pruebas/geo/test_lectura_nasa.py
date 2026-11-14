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


def _media_caja(a, g, lat0, lat1, lon0, lon1):
    # promedio de la caja [lat0, lat1] x [lon0, lon1] sobre el campo norte arriba
    i0, i1 = int((g.y0 - lat1) / g.dy), int((g.y0 - lat0) / g.dy)
    j0, j1 = int((lon0 - g.x0) / g.dx), int((lon1 - g.x0) / g.dx)
    return float(np.nanmean(a[i0:i1, j0:j1]))


def _lluvia_enero_2000():
    base = os.environ.get("AGRO_COPIA")
    if not base or not (Path(base) / "crudos").exists():
        pytest.skip("sin copia de crudos en WSL (AGRO_COPIA)")
    f = L.archivos(Path(base) / "crudos", "imerg_final")["2000-01"]
    a = L.leer_campo(f, "imerg_final", 1)[0]
    # AGRO_ESPEJO=1 fuerza a propósito la lectura espejada, para demostrar que las pruebas la detectan
    return (a[:, ::-1] if os.environ.get("AGRO_ESPEJO") else a), L.GRILLAS["imerg"]


@pytest.mark.datos_reales
def test_imerg_enero_pacifico_oeste_llueve_mas_que_el_sahara():
    # solo control de plausibilidad: el espejo del Pacífico occidental cae en el Atlántico húmedo, no discrimina
    a, g = _lluvia_enero_2000()
    pacifico, sahara = _media_caja(a, g, 0, 10, 130, 160), _media_caja(a, g, 20, 28, 0, 20)
    assert pacifico > 0.1 and pacifico > 10 * sahara


@pytest.mark.datos_reales
def test_imerg_signo_de_longitud_borneo_y_colombia():
    a, g = _lluvia_enero_2000()
    esp = a[:, ::-1]  # lectura espejada en longitud (el error original de GDAL)
    # Borneo (+109 a +119 E) es húmedo y su espejo (109 a 119 O, Pacífico oriental) casi seco en enero de 2000
    assert _media_caja(a, g, -2, 4, 109, 119) > 0.3 > 0.05 > _media_caja(esp, g, -2, 4, 109, 119)
    # Chocó (longitudes negativas) más húmedo que el mar Arábigo en su longitud espejo; el campo espejado invierte la relación
    assert _media_caja(a, g, 4, 8, -78, -74) > 1.3 * _media_caja(a, g, 4, 8, 74, 78)
    assert _media_caja(esp, g, 4, 8, -78, -74) < _media_caja(esp, g, 4, 8, 74, 78)


@pytest.mark.datos_reales
def test_imerg_banda_ecuatorial_120e_frente_a_120o_con_un_ano():
    # continente marítimo (120E) frente a Pacífico oriental (120O), media de 12 meses de 2000; el espejo las intercambia
    base = os.environ.get("AGRO_COPIA")
    if not base or not (Path(base) / "crudos").exists():
        pytest.skip("sin copia de crudos en WSL (AGRO_COPIA)")
    arch = L.archivos(Path(base) / "crudos", "imerg_final")
    _, regla = L.leer_campo(arch["2000-01"], "imerg_final", 1)  # la regla se deduce en enero y se reutiliza
    campos = [L.leer_campo(arch[f"2000-{m:02d}"], "imerg_final", m, regla)[0] for m in range(1, 13)]
    a = np.nanmean(campos, axis=0)
    if os.environ.get("AGRO_ESPEJO"):
        a = a[:, ::-1]
    g = L.GRILLAS["imerg"]
    este, oeste = _media_caja(a, g, -5, 5, 115, 125), _media_caja(a, g, -5, 5, -125, -115)
    assert este > 1.5 * oeste
