# asistido por SI: Claude Code (Anthropic), pruebas de lectura y descarga CGAZ (T-D1)
import geopandas as gpd
import pytest
from shapely.geometry import box

from simulacion.geo import unidades as u


def test_leer_cgaz_declara_wgs84_y_normaliza_columnas(tmp_path):
    # el GPKG de CGAZ trae un SRS sin nombre; se declara EPSG:4326 (SUPUESTO documentado en la ficha)
    g = gpd.GeoDataFrame({"shapeName": ["Pasto"], "shapeID": ["7082276B1"], "shapeGroup": ["COL"], "shapeType": ["ADM2"]},
                         geometry=[box(0, 0, 1, 1)], crs="EPSG:4326")
    ruta = tmp_path / "geoBoundariesCGAZ_ADM2.gpkg"
    g.to_file(ruta, driver="GPKG", layer="globalADM2")
    r = u.leer_cgaz(ruta, 2)
    assert r.crs.to_epsg() == 4326
    assert r.iso3.tolist() == ["COL"] and r.nivel_real.tolist() == ["ADM2"] and r.shape_id.tolist() == ["7082276B1"]


def test_hash_verificado_rechaza_archivo_distinto(tmp_path):
    f = tmp_path / "x.gpkg"
    f.write_bytes(b"abc")
    esperado = "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"  # sha256("abc")
    u.verificar_hash(f, esperado)
    with pytest.raises(ValueError):
        u.verificar_hash(f, "0" * 64)
