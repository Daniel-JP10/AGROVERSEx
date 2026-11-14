# asistido por SI: Claude Code, pruebas de lotes_demo.json (T-D5 Parte B)
import json
from pathlib import Path

import geopandas as gpd
import pytest
from shapely.geometry import shape

RUTA = Path(__file__).resolve().parents[2] / "datos" / "lotes" / "lotes_demo.json"
GPKG = Path("C:/NASA/AGROVERSEx/datos/procesados/unidades.gpkg")


def _lotes():
    return json.loads(RUTA.read_text(encoding="utf-8"))["lotes"]


def test_ids_y_etiqueta_demo():
    ids = {x["lote_id"] for x in _lotes()}
    assert ids == {"DEMO-USA-01", "DEMO-COL-01"}
    assert all(x["etiqueta"] == "DEMO" and x["clima_tipo"] in ("templado", "tropical") for x in _lotes())


def test_contiene_campos_del_contrato_web():
    for x in _lotes():
        assert {"lote_id", "unidad_id", "nombre", "geometria"} <= set(x)


def test_coordenadas_tres_decimales():
    for x in _lotes():
        for lon, lat in x["geometria"]["coordinates"][0]:
            assert round(lon, 3) == lon and round(lat, 3) == lat


@pytest.mark.skipif(not GPKG.exists(), reason="sin unidades.gpkg")
def test_poligono_dentro_de_su_unidad_adm2():
    g = gpd.read_file(GPKG, layer="adm2")
    for x in _lotes():
        u = g[g.unidad_id == x["unidad_id"]].geometry.iloc[0]
        assert u.contains(shape(x["geometria"])), x["lote_id"]
