# asistido por SI: Claude Code (Anthropic), escritura y revisión de código; base del prototipo migrada en el hackatón
import geopandas as gpd
import pandas as pd
from shapely.geometry import MultiPolygon, Point, box

from simulacion.geo.unidades import asignar_padre_espacial, nombre_valido


def _gdf(ids, geoms):
    return gpd.GeoDataFrame({"id": ids}, geometry=geoms, crs="EPSG:4326")


def test_nombre_valido():
    assert nombre_valido("NA") is False
    assert nombre_valido("?") is False
    assert nombre_valido("Meta") is True
    for malo in (None, "", "N.A.", "n.a."):
        assert nombre_valido(malo) is False


def _padres():
    return _gdf(["A", "B"], [box(0, 0, 10, 10), box(10, 0, 20, 10)])


def test_padre_espacial_simple():
    r = asignar_padre_espacial(_gdf(["h"], [box(2, 2, 4, 4)]), _padres())
    assert r.padre_id.iloc[0] == "A" and r.cruce_ambiguo.iloc[0] == 0


def test_padre_espacial_fuera():
    r = asignar_padre_espacial(_gdf(["h"], [box(50, 50, 52, 52)]), _padres())
    assert r.padre_id.iloc[0] is None and r.cruce_ambiguo.iloc[0] == 1


def test_antimeridiano():
    from simulacion.geo.unidades import _geometria_derivada
    g = MultiPolygon([box(178, -18, 180, -16), box(-180, -18, -178, -16)])
    punto_lat, punto_lon, area = _geometria_derivada(_gdf(["f"], [g]))
    assert g.contains(Point(punto_lon.iloc[0], punto_lat.iloc[0]))
    assert 40_000 < area.iloc[0] < 100_000


def test_nombre_valido_nan_y_variantes():
    assert nombre_valido(float("nan")) is False
    assert nombre_valido("n.a.") is False
    assert nombre_valido("  ") is False


def test_reparar_vectorizado():
    from shapely.geometry import Polygon
    from simulacion.geo.unidades import _reparar
    corbata = Polygon([(0, 0), (2, 2), (2, 0), (0, 2)])
    g = _gdf(["a", "b"], [box(0, 0, 1, 1), corbata])
    assert _reparar(g) == 1
    assert g.geometry.is_valid.all()


def test_gid_invalido():
    from simulacion.geo.unidades import _gid
    assert _gid("?", "UKR", 1) == "UKR.sin_gid_1"
    assert _gid("COL.1_1", "COL", 1) == "COL.1_1"


def test_gid_padre_desde_gid2():
    from simulacion.geo.unidades import _gid_padre
    assert _gid_padre("NA", "GBR.1.6_1", "GBR") == "GBR.1_1"
    assert _gid_padre("GBR.2_1", "GBR.2.1_1", "GBR") == "GBR.2_1"
    assert _gid_padre("?", "?", "UKR") == "UKR.sin_gid_1"


def test_marcar_disputadas():
    from simulacion.geo.unidades import marcar_disputadas
    t = pd.DataFrame({"id": ["COL", "Z01", "Z09", "ZAF"], "nivel": 0, "nombre": ["Colombia", "Aksai Chin", "x", "Sudáfrica"],
                      "nombre_ascii": ["Colombia", "Aksai Chin", "x", "Sudafrica"]})
    assert marcar_disputadas(t) == 2
    assert t.nivel.tolist() == [0, 9, 9, 0]
    assert t.nombre.tolist()[1:3] == ["Zona en disputa (Z01)", "Zona en disputa (Z09)"]
    assert t.nombre.iloc[0] == "Colombia"


def test_exportar_niveles_incluye_disputadas_en_adm0(tmp_path):
    from simulacion.geo.unidades import exportar_niveles
    g = gpd.GeoDataFrame({"id": ["A", "Z01", "A.1"], "nivel": [0, 9, 1], "iso3": ["A", "Z01", "A"],
                          "padre_id": None, "nombre": ["a", "z", "b"]},
                         geometry=[box(0, 0, 1, 1)] * 3, crs="EPSG:4326")
    salida = tmp_path / "crudos"
    rutas = exportar_niveles(g, salida)
    assert set(rutas) == {0, 1, 2}
    a0 = gpd.read_file(rutas[0])
    assert a0.id.tolist() == ["A", "Z01"] and a0.nivel.tolist() == [0, 9]
    # una capa por nivel en unidades.gpkg, junto a la carpeta de salida
    import pyogrio
    assert {c[0] for c in pyogrio.list_layers(tmp_path / "unidades.gpkg")} == {"adm0", "adm1", "adm2"}


def test_bbox_y_alias_kosovo():
    from simulacion.geo.unidades import ALIAS_ISO, _tabla
    g = _gdf(["a"], [box(1, 2, 3, 4)])
    t = _tabla(g, 0, ["a"], None, ["a"], ["a"], "f", "l")
    assert t[["bbox_oeste", "bbox_sur", "bbox_este", "bbox_norte"]].iloc[0].tolist() == [1, 2, 3, 4]
    assert ALIAS_ISO == {"XKX": "XKO"}


def test_escribir_metadatos(tmp_path):
    import sqlite3
    from simulacion.geo.unidades import COLUMNAS, escribir_geo_sqlite, escribir_metadatos
    ruta = tmp_path / "g.sqlite"
    escribir_geo_sqlite(gpd.GeoDataFrame({c: [] for c in COLUMNAS}, geometry=[], crs="EPSG:4326"), ruta)
    escribir_metadatos(ruta, {"a": "x", "b": {"k": 1}})
    assert dict(sqlite3.connect(ruta).execute("select * from metadatos")) == {"a": "x", "b": '{"k": 1}'}


def test_escribir_geo_sqlite(tmp_path):
    import sqlite3
    from simulacion.geo.unidades import COLUMNAS, escribir_geo_sqlite
    filas = {c: [None] * 3 for c in COLUMNAS}
    filas.update(id=["a", "b", "c"], nivel=[0, 1, 2], area_km2=[1.0, 2.0, 3.0], cruce_ambiguo=[0, 0, 1])
    g = gpd.GeoDataFrame(filas, geometry=[box(0, 0, 1, 1)] * 3, crs="EPSG:4326")
    escribir_geo_sqlite(g, tmp_path / "g.sqlite")
    con = sqlite3.connect(tmp_path / "g.sqlite")
    cols = [r[1] for r in con.execute("pragma table_info(unidad)")]
    assert cols == COLUMNAS
    assert con.execute("select id,nivel,area_km2,cruce_ambiguo from unidad order by id").fetchall() == [
        ("a", 0, 1.0, 0), ("b", 1, 2.0, 0), ("c", 2, 3.0, 1)]


def test_nombre_tipo_invalido():
    from simulacion.geo.unidades import _nombre
    assert _nombre("NA", "NA", "X.1") == "Unidad X.1"
    assert _nombre(None, "Municipio", "X.1") == "Municipio X.1"


def _servidor_gb(estado_primario):
    import http.server, threading
    datos = b"x" * 500

    class H(http.server.BaseHTTPRequestHandler):
        def log_message(self, *a):
            pass

        def do_GET(self):
            ok = self.path == "/alt"
            self.send_response(200 if ok else estado_primario)
            self.send_header("Content-Length", str(len(datos)) if ok else "0")
            self.end_headers()
            if ok:
                self.wfile.write(datos)
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), H)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv, f"http://127.0.0.1:{srv.server_port}"


def _recurso(url):
    from simulacion.geo.descargas import Recurso
    return Recurso("x", url, "a.bin", "L", "f.md", None, None)


def test_alterna_ante_503(tmp_path):
    from simulacion.geo.unidades import descargar_con_alterna
    srv, base = _servidor_gb(503)
    try:
        f = descargar_con_alterna(_recurso(base + "/pri"), tmp_path, alt=base + "/alt", esquemas=("http",))
        assert f.read_bytes() == b"x" * 500
    finally:
        srv.shutdown()


def test_404_se_propaga(tmp_path):
    import pytest
    import requests
    from simulacion.geo.unidades import descargar_con_alterna
    srv, base = _servidor_gb(404)
    try:
        with pytest.raises(requests.HTTPError):
            descargar_con_alterna(_recurso(base + "/pri"), tmp_path, alt=base + "/alt", esquemas=("http",))
    finally:
        srv.shutdown()


def test_filtrar_hijas_validas():
    from simulacion.geo.unidades import filtrar_hijas_validas
    g = pd.DataFrame({"GID_0": ["COL", "Z01", "NA"], "GID_1": ["COL.1_1", "Z01.1_1", "NA"]})
    out, n_na, n_disp = filtrar_hijas_validas(g, {"COL"})
    assert out.GID_1.tolist() == ["COL.1_1"] and (n_na, n_disp) == (1, 1)


def test_asegurar_gpkg(tmp_path):
    import zipfile
    from simulacion.geo.unidades import asegurar_gpkg
    z = tmp_path / "g.zip"
    with zipfile.ZipFile(z, "w") as f:
        f.writestr("x.gpkg", b"datos")
    dest = tmp_path / "sub" / "x.gpkg"
    assert asegurar_gpkg(z, dest).read_bytes() == b"datos"
    dest.write_bytes(b"otro")
    z.unlink()  # si existe, ni siquiera abre el zip
    assert asegurar_gpkg(z, dest).read_bytes() == b"otro"
