# asistido por SI: Claude Code (Anthropic), pruebas del motor de agregación zonal mensual (T-D2)
import numpy as np
import pytest
import shapely

from simulacion.geo import zonal_mensual as zm


def _grilla(alto=4, ancho=4, lat_norte=2.0, d=1.0, lon0=0.0):
    # celdas de d grados, borde norte en lat_norte, borde oeste en lon0
    lon = lon0 + d * (np.arange(ancho) + 0.5)
    lat = lat_norte - d * (np.arange(alto) + 0.5)
    return zm.grilla_desde_centros(lon, lat[::-1])  # entra creciente, como IMERG


def _caja(x0, y0, x1, y1):
    return shapely.box(x0, y0, x1, y1)


def test_raster_constante_da_la_constante_y_fraccion_uno():
    pytest.importorskip("exactextract")  # se salta sin exactextract (Windows)
    g = _grilla()
    p = zm.calcular_pesos(g, [_caja(0.3, -1.6, 3.4, 1.2)])
    r = zm.agregar(p, g, np.full(g.alto * g.ancho, 7.5, "float64"), umbral=0.5)
    assert r["valor"][0] == pytest.approx(7.5) and r["frac_valida"][0] == pytest.approx(1.0)
    assert r["p10"][0] == pytest.approx(7.5) and r["p90"][0] == pytest.approx(7.5)


def test_mitad_nan_da_frac_valida_exacta():
    pytest.importorskip("exactextract")  # se salta sin exactextract (Windows)
    g = _grilla()
    x = np.full((4, 4), 1.0)
    x[:, :2] = np.nan  # la unidad cubre las 4 filas y 4 columnas: la mitad oeste sin dato
    p = zm.calcular_pesos(g, [_caja(0, -2, 4, 2)])
    r = zm.agregar(p, g, x.ravel(), umbral=0.4)
    assert r["frac_valida"][0] == pytest.approx(0.5, abs=1e-6) and r["valor"][0] == pytest.approx(1.0)


def test_unidad_igual_a_una_celda_da_el_valor_de_la_celda():
    pytest.importorskip("exactextract")  # se salta sin exactextract (Windows)
    g = _grilla()
    x = np.arange(16, dtype="float64").reshape(4, 4)
    p = zm.calcular_pesos(g, [_caja(2, 0, 3, 1)])  # fila 1 (de 0 al norte), columna 2
    r = zm.agregar(p, g, x.ravel(), umbral=0.5)
    assert r["valor"][0] == pytest.approx(x[1, 2])


def test_gradiente_de_latitud_coincide_con_el_calculo_analitico_por_area():
    pytest.importorskip("exactextract")  # se salta sin exactextract (Windows)
    lat_c = np.arange(0.5, 60, 1.0)
    g = zm.grilla_desde_centros(np.array([0.5, 1.5]), lat_c)
    x = np.repeat(lat_c[::-1, None], 2, axis=1)  # norte arriba: cada celda vale su latitud
    p = zm.calcular_pesos(g, [_caja(0, 0, 2, 60)])
    r = zm.agregar(p, g, x.ravel(), umbral=0.5)
    a = np.sin(np.radians(lat_c + 0.5)) - np.sin(np.radians(lat_c - 0.5))
    esperado = (a * lat_c).sum() / a.sum()
    assert r["valor"][0] == pytest.approx(esperado, rel=1e-6)
    assert abs(esperado - lat_c.mean()) > 0.3  # sin peso de latitud daría otra cifra


def test_percentiles_ponderados_inferiores():
    pytest.importorskip("exactextract")  # se salta sin exactextract (Windows)
    g = _grilla(2, 4, lat_norte=1.0)  # filas simétricas respecto del ecuador: misma área
    x = np.tile([1.0, 2.0, 3.0, 4.0], 2)
    p = zm.calcular_pesos(g, [_caja(0, -1, 4, 1)])
    r = zm.agregar(p, g, x, umbral=0.5)
    assert r["p10"][0] == 1.0 and r["p90"][0] == 4.0  # con pesos iguales se acota al mínimo y al máximo
    # la celda de 4 pesa 97 %: p90 queda en 4 y p10 se interpola entre 3 y 4 (cuantil con posiciones a mitad de peso)
    cult = np.tile([0.01, 0.01, 0.01, 0.97], 2)
    r2 = zm.agregar(p, g, x, cultivo=cult, umbral=0.5)
    assert r2["p90"][0] == 4.0 and 3.0 < r2["p10"][0] < 4.0 and r2["valor"][0] > 3.8
    uno = zm.agregar(zm.calcular_pesos(g, [_caja(1.2, 0.1, 1.8, 0.9)]), g, x, umbral=0.5)  # dentro de una celda
    assert uno["p10"][0] == uno["p90"][0] == uno["valor"][0] == 2.0


def test_bajo_el_umbral_sale_nan_con_motivo_y_sin_cobertura_tambien():
    pytest.importorskip("exactextract")  # se salta sin exactextract (Windows)
    g = _grilla()
    x = np.full((4, 4), np.nan)
    x[0, 0] = 2.0
    p = zm.calcular_pesos(g, [_caja(0, -2, 4, 2)])
    r = zm.agregar(p, g, x.ravel(), umbral=0.5)
    assert np.isnan(r["valor"][0]) and r["motivo"][0] == "frac_valida_bajo_umbral"
    assert r["frac_valida"][0] == pytest.approx(g.areas_fila()[0] / (4 * g.areas_fila().sum()), rel=1e-6)
    r0 = zm.agregar(p, g, np.full(16, np.nan), umbral=0.5)
    assert r0["motivo"][0] == "sin_celdas_validas" and r0["frac_valida"][0] == 0.0


def test_unidad_diminuta_y_antimeridiano_tienen_pesos():
    pytest.importorskip("exactextract")  # se salta sin exactextract (Windows)
    lon = np.arange(-179.5, 180, 1.0)
    lat = np.arange(-89.5, 90, 1.0)
    g = zm.grilla_desde_centros(lon, lat)
    mini = _caja(10.1, 5.1, 10.2, 5.2)  # 0,01 grados cuadrados dentro de una celda
    fiyi = shapely.MultiPolygon([_caja(179.5, -17, 180, -16), _caja(-180, -17, -179.5, -16)])
    p = zm.calcular_pesos(g, [mini, fiyi])
    assert set(p.u) == {0, 1}
    cols = p.c[p.u == 1] % g.ancho
    assert 0 in cols and g.ancho - 1 in cols
    assert p.cov[p.u == 0].sum() == pytest.approx(0.01, rel=1e-3)


def test_alineacion_origen_tamano_y_firma():
    g = zm.grilla_desde_centros(np.array([-179.95, -179.85, -179.75]), np.array([-0.05, 0.05]))
    assert (g.x0, g.y0, g.dx, g.dy) == pytest.approx((-180.0, 0.1, 0.1, 0.1))
    assert (g.alto, g.ancho) == (2, 3)
    g2 = zm.grilla_desde_centros(np.array([-179.95, -179.85, -179.75]), np.array([0.05, -0.05]))
    assert g.firma() == g2.firma()  # el orden de entrada no cambia la grilla
    g3 = zm.grilla_desde_centros(np.array([-179.95, -179.85, -179.75, -179.65]), np.array([-0.05, 0.05]))
    assert g3.firma() != g.firma()


def test_cache_se_invalida_al_cambiar_firma_o_unidades(tmp_path, monkeypatch):
    pytest.importorskip("exactextract")  # se salta sin exactextract (Windows)
    g = _grilla()
    ids, geoms = ["a"], [_caja(0, -1, 2, 1)]
    llamadas = []
    original = zm.calcular_pesos
    monkeypatch.setattr(zm, "calcular_pesos", lambda *a, **k: (llamadas.append(1), original(*a, **k))[1])
    zm.pesos_con_cache(g, ids, geoms, tmp_path)
    zm.pesos_con_cache(g, ids, geoms, tmp_path)
    assert len(llamadas) == 1  # la segunda sale de la caché
    zm.pesos_con_cache(g, ids, [_caja(0, -1, 2.5, 1)], tmp_path)  # otra geometría
    zm.pesos_con_cache(_grilla(ancho=5), ids, geoms, tmp_path)  # otra grilla
    assert len(llamadas) == 3


def test_fraccion_de_cultivo_desde_clases_no_interpola():
    clases = np.array([[12, 12, 7, 7], [12, 14, 7, 7], [7, 7, 7, 7], [7, 7, 7, 12]])
    f = zm.fraccion_clase(clases, 2, {12})
    assert f.tolist() == [[0.75, 0.0], [0.0, 0.25]]
    assert set(np.unique(f)) <= {0.0, 0.25, 0.5, 0.75, 1.0}
    with pytest.raises(ValueError):
        zm.fraccion_clase(clases, 3, {12})  # el bloque no divide la malla


def test_fraccion_de_cultivo_exacta_sobre_malla_gruesa_desalineada():
    pytest.importorskip("exactextract")  # se salta sin exactextract (Windows)
    # fino de 0,25 grados con clases 3 y 9; gruesa de 1 grado desplazada 0,5: cuenta por área, sin interpolar
    fino = zm.grilla_desde_centros(np.arange(0.125, 4, 0.25), np.arange(0.125, 4, 0.25))
    clases = np.full((16, 16), 9)
    clases[:8, :8] = 3  # cuadrante noroeste (lat 2 a 4, lon 0 a 2) es cultivo
    gruesa = zm.grilla_desde_centros(np.array([0.0, 1.0, 2.0]), np.array([1.0, 2.0, 3.0]))  # bordes en -0,5, 0,5...
    f = zm.fraccion_cultivo(gruesa, clases, fino, {1, 2, 3}, (-0.5, 0.5, 2.5, 3.5)).reshape(3, 3)
    # filas de norte a sur (lat 3, 2, 1) y columnas de oeste a este (lon 0, 1, 2)
    assert f[1, 2] == pytest.approx(0.25)  # un cuarto de la celda (lon 1,5-2 y lat 2-2,5) es cultivo
    assert f[1, 1] == pytest.approx(0.5)  # lat 1,5-2,5: mitad norte; lon 0,5-1,5 entera
    assert f[2, 0] == 0.0 and f[0, 1] == pytest.approx(1.0)
    assert set(np.unique(f)) <= {0.0, 0.25, 0.5, 0.75, 1.0}  # solo fracciones de conteo, no mezclas interpoladas


@pytest.mark.datos_reales
def test_contra_exactextract_directo_en_municipios_de_colombia():
    import os
    from pathlib import Path

    import pyogrio
    from exactextract import exact_extract
    from exactextract.raster import NumPyRasterSource

    from simulacion.geo import lectura_nasa as L
    base = os.environ.get("AGRO_COPIA")
    if not base or not (Path(base) / "crudos").exists():
        pytest.skip("sin copia de crudos en WSL (AGRO_COPIA)")
    u = pyogrio.read_dataframe(Path(base) / "proc" / "unidades.gpkg", layer="adm2", where="iso3='COL'",
                               columns=["unidad_id"]).sample(60, random_state=7).reset_index(drop=True)
    g = L.GRILLAS["imerg"]
    f = L.archivos(Path(base) / "crudos", "imerg_final")["2020-01"]
    campo, _ = L.leer_campo(f, "imerg_final", 1, (True, True, True))
    p = zm.calcular_pesos(g, list(u.geometry))
    r = zm.agregar(p, g, campo.ravel(), umbral=0.0)
    # referencia: exactextract directo con la media ponderada por área de fila (peso de latitud)
    ext = (g.x0, g.y0 - g.alto * g.dy, g.x0 + g.ancho * g.dx, g.y0)
    wkt = zm._wkt4326()
    val = NumPyRasterSource(campo.astype("float32"), *ext, srs_wkt=wkt, nodata=np.nan)
    peso = NumPyRasterSource(np.broadcast_to(g.areas_fila().astype("float32")[:, None], campo.shape).copy(), *ext, srs_wkt=wkt)
    u2 = u.assign(uid=np.arange(len(u)))[["uid", "geometry"]]
    d = exact_extract(val, u2, ["weighted_mean"], weights=peso, include_cols=["uid"], output="pandas")
    dif = np.abs(d["weighted_mean"].to_numpy() - r["valor"][d["uid"].to_numpy()])
    print("diferencia maxima contra exactextract directo (mm/hr):", np.nanmax(dif))
    assert np.nanmax(dif) < 1e-4
