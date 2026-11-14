# asistido por SI: Claude Code (Anthropic), escritura y revisión de código; base del prototipo migrada en el hackatón
import math

import geopandas as gpd
import numpy as np
import pytest
from shapely.geometry import box

# la ruta raster corre en WSL (rasterio y exactextract no cargan en Windows por Control de aplicaciones)
rasterio = pytest.importorskip("rasterio")
pytest.importorskip("exactextract")
from rasterio.transform import from_origin  # noqa: E402

from simulacion.geo.zonal import (fracciones_clase, media_ponderada, medias_ponderadas, moda,  # noqa: E402
                                  pesos_area_geograficos, ponderar_profundidad)


def _raster(ruta, datos, crs="EPSG:3857", nodata=-9999.0, tam=1.0, origen=(0.0, 4.0)):
    datos = np.asarray(datos, dtype="float32")
    with rasterio.open(ruta, "w", driver="GTiff", height=datos.shape[0], width=datos.shape[1],
                       count=1, dtype="float32", crs=crs, nodata=nodata,
                       transform=from_origin(origen[0], origen[1], tam, tam)) as d:
        d.write(datos, 1)
    return ruta


def _unidades(*cajas, crs="EPSG:3857"):
    return gpd.GeoDataFrame({"id": [f"u{i}" for i in range(len(cajas))]},
                            geometry=list(cajas), crs=crs)


def test_media_ponderada_exacta(tmp_path):
    r = _raster(tmp_path / "a.tif", [[10, 10, 30, 30]] * 4)
    out = media_ponderada(r, _unidades(box(1, 0, 3, 4)), 1.0)
    assert out.valor[0] == pytest.approx(20)
    assert out.fraccion_valida[0] == pytest.approx(1)


def test_nodata_es_null(tmp_path):
    r = _raster(tmp_path / "a.tif", np.full((4, 4), -9999.0))
    out = media_ponderada(r, _unidades(box(0, 0, 4, 4)), 1.0)
    assert out.valor[0] is None
    assert out.fraccion_valida[0] == 0


def test_nodata_parcial(tmp_path):
    r = _raster(tmp_path / "a.tif", [[-9999, -9999, 10, 30]] * 4)
    out = media_ponderada(r, _unidades(box(0, 0, 4, 4)), 1.0)
    assert out.fraccion_valida[0] == pytest.approx(0.5)
    assert out.valor[0] == pytest.approx(20)


def test_fracciones_suman_uno(tmp_path):
    r = _raster(tmp_path / "c.tif", [[1, 1, 2, 3]] * 4, nodata=0)
    fr = fracciones_clase(r, _unidades(box(0, 0, 4, 4)), {1, 2, 3})
    assert fr.groupby("id").fraccion.sum().iloc[0] == pytest.approx(1, abs=0.001)
    assert moda(fr)["u0"] == 1


def test_pesos_geograficos():
    w = pesos_area_geograficos(from_origin(0, 60, 1, 1), 60, 1)
    esperado = math.cos(math.radians(0.5)) / math.cos(math.radians(59.5))
    assert w[-1] / w[0] == pytest.approx(esperado, rel=0.01)
    assert w.sum() == pytest.approx(1)


def test_factor_soilgrids(tmp_path):
    r = _raster(tmp_path / "s.tif", np.full((4, 4), 65.0))
    out = media_ponderada(r, _unidades(box(0, 0, 4, 4)), 10.0)
    assert out.valor[0] == pytest.approx(6.5)


def test_ponderar_profundidad():
    assert ponderar_profundidad(10, 20, 30) == (50 + 200 + 450) / 30


def test_varios_rasters_igual_a_uno_por_uno(tmp_path):
    datos = [np.arange(16).reshape(4, 4) * k for k in (1.0, 2.5)]
    datos[1][0, :] = -9999
    rs = [_raster(tmp_path / f"r{i}.tif", d) for i, d in enumerate(datos)]
    u = _unidades(box(0, 0, 4, 4), box(0.5, 0.5, 2.2, 3), box(0, 3, 4, 4))
    junto = medias_ponderadas(rs, u, [10.0, 1.0])
    for r, f in zip(rs, (10.0, 1.0)):
        solo = media_ponderada(r, u, f)
        assert junto[r].fraccion_valida.tolist() == pytest.approx(solo.fraccion_valida.tolist())
        assert junto[r].valor.tolist() == pytest.approx(solo.valor.tolist(), nan_ok=True)


def test_igh_no_infla_area_en_groenlandia():
    from simulacion.geo.zonal import proyectar_igh
    # la caja cruza la interrupción norte (-40) como Groenlandia
    u = _unidades(box(-60, 60, -20, 80), crs="EPSG:4326")
    geod = u.to_crs("EPSG:6933").area[0]
    assert 0.95 < proyectar_igh(u, "ESRI:54052").area[0] / geod < 1.05


def test_fracciones_clase_ponderan_por_latitud(tmp_path):
    # mitad norte (lat 30-60) clase 1, mitad sur (0-30) clase 2: la sur pesa más que la norte
    datos = np.vstack([np.full((30, 2), 1), np.full((30, 2), 2)])
    r = _raster(tmp_path / "k.tif", datos, crs="EPSG:4326", nodata=0, origen=(0.0, 60.0))
    fr = fracciones_clase(r, _unidades(box(0, 0, 2, 60), crs="EPSG:4326"), {1, 2}).set_index("clase")
    esperado = (math.sin(math.radians(30)) - 0) / math.sin(math.radians(60))
    assert fr.fraccion[2] == pytest.approx(esperado, rel=0.01) and fr.fraccion[2] > 0.55


def test_varios_rasters_geograficos_con_pesos(tmp_path):
    # CRS geográfico + varios rasters: exactextract nombra "<raster>__weighted_mean" (doble guion bajo)
    datos = [np.full((4, 4), 5.0), np.full((4, 4), 7.0)]
    rs = [_raster(tmp_path / f"g{i}.tif", d, crs="EPSG:4326", origen=(0.0, 4.0)) for i, d in enumerate(datos)]
    u = _unidades(box(0.5, 0.5, 2.2, 3), crs="EPSG:4326")
    junto = medias_ponderadas(rs, u, [1.0, 1.0])
    assert junto[rs[0]].valor.tolist() == pytest.approx([5.0]) and junto[rs[1]].valor.tolist() == pytest.approx([7.0])
