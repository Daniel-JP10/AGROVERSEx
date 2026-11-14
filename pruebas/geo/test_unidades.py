# asistido por SI: Claude Code (Anthropic), pruebas de unidades CGAZ (T-D1)
import sqlite3

import geopandas as gpd
import pandas as pd
import pytest
from shapely.geometry import MultiPolygon, Point, Polygon, box

from simulacion.geo import unidades as u


def _gdf(ids, geoms, **extra):
    return gpd.GeoDataFrame({"unidad_id": ids, **extra}, geometry=geoms, crs="EPSG:4326")


def test_formato_unidad_id():
    ids = u.construir_ids(["COL", "COL", "XKX", "111"], [0, 1, 2, 0], [None, "13589884B81785725414319", "7082276B1", None])
    assert list(ids) == ["COL-ADM0", "COL-ADM1-13589884B81785725414319", "XKX-ADM2-7082276B1", "111-ADM0"]


def test_duplicados_detecta_repetidos():
    df = pd.DataFrame({"unidad_id": ["A", "B", "A"], "nivel": [1, 1, 1]})
    assert u.duplicados(df) == 1
    assert u.duplicados(df.iloc[:2]) == 0
    # mismo id en niveles distintos no es duplicado por nivel pero sí global
    df2 = pd.DataFrame({"unidad_id": ["A", "A"], "nivel": [1, 2]})
    assert u.duplicados(df2) == 1


def _padres():
    return _gdf(["A-ADM0", "B-ADM0"], [box(0, 0, 10, 10), box(10, 0, 20, 10)], iso3=["A", "B"])


def test_padre_espacial_simple():
    r = u.asignar_padre_espacial(_gdf(["h"], [box(2, 2, 4, 4)]), _padres())
    assert r.padre_id.iloc[0] == "A-ADM0" and r.cruce_ambiguo.iloc[0] == 0


def test_padre_espacial_fuera():
    r = u.asignar_padre_espacial(_gdf(["h"], [box(50, 50, 52, 52)]), _padres())
    assert r.padre_id.iloc[0] is None and r.cruce_ambiguo.iloc[0] == 1


def test_corregir_padres_reasigna_al_del_mismo_pais():
    hijos = _gdf(["h1", "h2", "h3"], [box(2, 2, 4, 4), box(12, 2, 14, 4), box(50, 50, 52, 52)],
                 iso3=["A", "A", "B"], nivel=1)
    padres = _padres()
    p = u.asignar_padre_espacial(hijos, padres)
    hijos["padre_id"] = p.padre_id
    out, stats = u.corregir_padres(hijos, padres)
    # h2 cae en B pero es de A: se reasigna a A; h3 no cae en nada: se asigna al más cercano de su país
    assert out.padre_id.tolist() == ["A-ADM0", "A-ADM0", "B-ADM0"]
    assert stats == {"distinto_pais": 1, "sin_padre": 1}


def test_antimeridiano():
    g = MultiPolygon([box(178, -18, 180, -16), box(-180, -18, -178, -16)])
    lat, lon, area = u._geometria_derivada(_gdf(["f"], [g]))
    assert g.contains(Point(lon.iloc[0], lat.iloc[0]))
    assert 40_000 < area.iloc[0] < 100_000


def test_reparar_vectorizado():
    corbata = Polygon([(0, 0), (2, 2), (2, 0), (0, 2)])
    g = _gdf(["a", "b"], [box(0, 0, 1, 1), corbata])
    assert u._reparar(g) == 1
    assert g.geometry.is_valid.all()


def test_area_proyectada_vs_geodesica():
    g = _gdf(["a", "b"], [box(-75, 0, -74, 1), box(10, 60, 11, 61)])
    _, _, proy = u._geometria_derivada(g)
    geo = u.area_geodesica_km2(g.geometry)
    assert (proy.values / geo).tolist() == pytest.approx([1, 1], abs=u.TOLERANCIA_AREA)
    assert 12_000 < geo[0] < 12_500  # 1 grado en el ecuador, unos 12.3 mil km2


def test_codigos_huerfanos_con_sql():
    t = pd.DataFrame({"unidad_id": ["XKX-ADM0", "XKO-ADM1-1", "COL-ADM2-2"], "nivel": [0, 1, 2],
                      "iso3": ["XKX", "XKO", "COL"]})
    assert u.codigos_huerfanos(t) == {"XKO", "COL"}
    assert u.codigos_huerfanos(t.iloc[[0]]) == set()


def test_paises_sin_nivel2_se_derivan():
    adm2 = pd.DataFrame({"iso3": ["COL", "COL", "AND", "LBY", "LBY"],
                         "nivel_real": ["ADM2", "ADM2", "ADM1", "ADM1", "ADM1"]})
    assert u.paises_sin_nivel2(adm2) == ["AND", "LBY"]


def test_escribir_gpkg_parcial_indice_y_capas(tmp_path):
    import pyogrio
    g = _gdf(["A-ADM0", "A-ADM1-1", "A-ADM2-1"], [box(0, 0, 1, 1)] * 3, nivel=[0, 1, 2], iso3="A", padre_id=None, nombre="x")
    ruta = tmp_path / "unidades.gpkg"
    u.escribir_gpkg(g, ruta)
    assert ruta.exists() and not (tmp_path / "unidades.parcial.gpkg").exists()
    assert {c[0] for c in pyogrio.list_layers(ruta)} == {"adm0", "adm1", "adm2"}
    con = sqlite3.connect(ruta)
    nombres = {r[0] for r in con.execute("select name from sqlite_master")}
    assert "rtree_adm1_geom" in nombres and "idx_adm1_unidad_id" in nombres
    assert pyogrio.read_dataframe(ruta, layer="adm1", where="unidad_id='A-ADM1-1'").shape[0] == 1


def test_exportar_niveles_geojson(tmp_path):
    g = _gdf(["A-ADM0", "111-ADM0", "A-ADM1-1"], [box(0, 0, 1, 1)] * 3, nivel=[0, 0, 1],
             iso3=["A", "111", "A"], padre_id=None, nombre=["a", "z", "b"])
    rutas = u.exportar_niveles(g, tmp_path)
    assert set(rutas) == {0, 1, 2}
    assert gpd.read_file(rutas[0]).unidad_id.tolist() == ["A-ADM0", "111-ADM0"]


def test_area_geodesica_con_hueco_y_orientacion():
    # el hueco resta y la orientación del anillo no cambia el signo
    ext = [(0, 0), (0, 2), (2, 2), (2, 0)]
    hueco = [(0.5, 0.5), (1.5, 0.5), (1.5, 1.5), (0.5, 1.5)]
    con = Polygon(ext, [hueco])
    pleno = u.area_geodesica_km2([Polygon(ext)])[0]
    assert u.area_geodesica_km2([con])[0] == pytest.approx(pleno * 0.75, rel=1e-3)
    assert u.area_geodesica_km2([Polygon(ext[::-1])])[0] == pytest.approx(pleno)


def test_reparar_deja_solo_poligonos():
    antena = Polygon([(0, 0), (4, 0), (4, 4), (2, 4), (2, 6), (2, 4), (0, 4)])
    degenerado = Polygon([(0, 0), (1, 1), (2, 2), (0, 0)])
    g = _gdf(["a", "b", "c"], [box(0, 0, 1, 1), antena, degenerado])
    assert u._reparar(g) == 2
    # la antena pierde la línea; el polígono degenerado se conserva como un polígono mínimo
    assert set(g.geometry.geom_type) <= {"Polygon", "MultiPolygon"}
    assert g.geometry.iloc[1].area == pytest.approx(16)
    assert 0 < g.geometry.iloc[2].area < 1e-4  # ancho 2e-5 grados por 2,8 de largo


def test_area_usa_proyeccion_de_igual_area_elipsoidal():
    assert u.CRS_AREA_UNIDADES == "EPSG:6933"
    # un grado cuadrado a 60 N: la esfera de Mollweide se desvía más que la proyección elipsoidal
    g = _gdf(["a"], [box(10, 60, 11, 61)])
    _, _, proy = u._geometria_derivada(g)
    geo = u.area_geodesica_km2(g.geometry)[0]
    assert abs(proy.iloc[0] / geo - 1) < 0.001  # más estricta que la tolerancia declarada


def test_area_con_bordes_largos_coincide_densificando():
    # un borde de 120 grados: sin densificar, la geodésica y la proyectada difieren mucho
    g = _gdf(["a"], [box(-60, 60, 60, 61)])
    _, _, proy = u._geometria_derivada(g)
    geo = u.area_geodesica_km2(g.geometry)[0]
    assert abs(proy.iloc[0] / geo - 1) < u.TOLERANCIA_AREA


def test_reparar_linea_pura_pasa_a_poligono():
    linea = Polygon([(0, 0), (1, 1), (0, 0)])
    g = _gdf(["a"], [linea])
    u._reparar(g)
    assert g.geometry.iloc[0].geom_type == "Polygon" and g.geometry.is_valid.all()
