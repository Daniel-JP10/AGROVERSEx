# asistido por SI: Claude Code (Anthropic), pruebas de teselas con unidad_id de CGAZ (T-D1)
import subprocess
from pathlib import Path

import pytest

from simulacion.config import PROCESADOS
from simulacion.geo.teselas import (comando_mapshaper, comando_tippecanoe, contar_ids,
                                    ruta_wsl, partir_por_pais, simplificado_vigente, unir_geojson, completar_perdidos, SIMPLIFICADOS, TESELAS, HERRAMIENTAS)


def test_ruta_wsl():
    p = Path(r"C:\Proyectos personales\AGROVERSERx\x.geojson")
    assert ruta_wsl(p) == "/mnt/c/Proyectos personales/AGROVERSERx/x.geojson"


def test_comando_tippecanoe_flags():
    c = comando_tippecanoe("/in", "/out", "adm2", 5, 12)
    for f in ("--no-simplification-of-shared-nodes", "--no-tiny-polygon-reduction",
              "--no-feature-limit"):
        assert f in c
    # /usr/bin/time -v deja en el registro el tiempo y el pico de RAM de tippecanoe
    assert c[c.index("--") + 1:c.index("--") + 4] == ["/usr/bin/time", "-v", "tippecanoe"]
    assert "--drop-densest-as-needed" not in c
    assert "--coalesce-densest-as-needed" not in c
    assert c[-1] == "/in" and c[c.index("-Z") + 1] == "5" and c[c.index("-z") + 1] == "12"


def test_comando_mapshaper_keep_shapes():
    c = comando_mapshaper([Path("a.geojson")], Path("salida"), 10)
    assert "keep-shapes" in c and "combine-files" in c
    assert "10%" in c


def test_contar_ids(tmp_path):
    f = tmp_path / "x.geojson"
    f.write_text('{"features": [{"properties": {"unidad_id": "A.1_1", "padre_id": "A"}},\n'
                 '{"properties": {"unidad_id": "A.2_1", "padre_id": "A"}}]}', encoding="utf-8")
    assert contar_ids(f) == {"A.1_1", "A.2_1"}


def test_partir_y_unir_conserva_ids(tmp_path):
    f = tmp_path / "adm2.geojson"
    filas = [f'{{ "type": "Feature", "properties": {{ "unidad_id": "{i}", "iso3": "{i[:3]}" }}, "geometry": null }}'
             for i in ("AAA.1", "AAA.2", "BBB.1", "CCC.1")]
    f.write_text('{\n"features": [\n' + ",\n".join(filas) + "\n]\n}\n", encoding="utf-8")
    partes = partir_por_pais(f, tmp_path / "p", max_bytes=1)
    assert len(partes) == 3  # AAA no se parte aunque pase el máximo
    for p in partes:  # cada parte es un GeoJSON válido; mapshaper escribe sin espacios
        p.write_text(p.read_text().replace('{ "type": "Feature"', '{"type":"Feature"'))
    out = tmp_path / "u.geojson"
    unir_geojson(partes, out)
    assert contar_ids(out) == {"AAA.1", "AAA.2", "BBB.1", "CCC.1"}
    import json
    assert len(json.loads(out.read_text())["features"]) == 4


def test_simplificado_solo_se_reutiliza_si_es_mas_nuevo(tmp_path):
    import os
    crudo, simple = tmp_path / "c.geojson", tmp_path / "s.geojson"
    crudo.write_text("c")
    assert not simplificado_vigente(crudo, simple)  # no existe
    simple.write_text("s")
    os.utime(crudo, (2000, 2000))
    os.utime(simple, (1000, 1000))
    assert not simplificado_vigente(crudo, simple)  # más viejo que el crudo
    os.utime(simple, (3000, 3000))
    assert simplificado_vigente(crudo, simple)


def test_completar_perdidos(tmp_path):
    crudo, simple = tmp_path / "c.geojson", tmp_path / "s.geojson"
    f = lambda i: f'{{ "type": "Feature", "properties": {{ "unidad_id": "{i}" }}, "geometry": null }}'
    crudo.write_text('{\n"features": [\n' + ",\n".join(map(f, ["A", "B", "C"])) + "\n]\n}\n")
    simple.write_bytes(b'{"type":"FeatureCollection","features":[\n'
                       b'{"type":"Feature","properties":{"unidad_id":"A"}}\n]}\n')
    assert completar_perdidos(crudo, simple) == 2
    import json
    assert contar_ids(simple) == {"A", "B", "C"} and len(json.loads(simple.read_text())["features"]) == 3
    assert completar_perdidos(crudo, simple) == 0


@pytest.mark.datos_reales
@pytest.mark.skipif(not (SIMPLIFICADOS / "adm2.geojson").exists(), reason="falta construir")
@pytest.mark.parametrize("nivel", [0, 1, 2])
def test_simplificacion_conserva_ids(nivel):
    import pyogrio
    gp = PROCESADOS / "unidades.gpkg"
    unidades = set(pyogrio.read_dataframe(gp, layer=f"adm{nivel}", read_geometry=False, columns=["unidad_id"])["unidad_id"])
    assert contar_ids(SIMPLIFICADOS / f"adm{nivel}.geojson") == unidades


@pytest.mark.datos_reales
@pytest.mark.skipif(not (TESELAS / "adm2.pmtiles").exists(), reason="falta construir")
def test_pmtiles_adm2_capa_y_zoom():
    cmd = f"tippecanoe-decode '{ruta_wsl(TESELAS / 'adm2.pmtiles')}' 12 0 0 2>&1 | grep -a -o '\"generator_options\": *\"[^\"]*\"'"
    out = subprocess.run(["wsl", "-d", "Ubuntu-24.04", "--", "bash", "-c", cmd], capture_output=True, text=True,
                         encoding="utf-8").stdout
    assert "-l adm2" in out and "-z 12" in out and "-Z 5" in out


def test_completar_perdidos_con_cierre_sin_salto_final(tmp_path):
    # mapshaper cierra el archivo con "\n]}" sin salto de línea al final
    crudo, simple = tmp_path / "c.geojson", tmp_path / "s.geojson"
    f = lambda i: f'{{ "type": "Feature", "properties": {{ "unidad_id": "{i}" }}, "geometry": null }}'
    crudo.write_text('{\n"features": [\n' + ",\n".join(map(f, ["A", "B"])) + "\n]\n}\n")
    simple.write_bytes(b'{"type":"FeatureCollection", "features": [\n{"type":"Feature","properties":{"unidad_id":"A"}}\n]}')
    assert completar_perdidos(crudo, simple) == 1
    import json
    assert [x["properties"]["unidad_id"] for x in json.loads(simple.read_text())["features"]] == ["A", "B"]


def test_herramientas_se_puede_apuntar_con_variable(monkeypatch, tmp_path):
    import importlib
    import simulacion.geo.teselas as t
    monkeypatch.setenv("AGRO_HERRAMIENTAS", str(tmp_path))
    try:
        assert importlib.reload(t).HERRAMIENTAS == tmp_path
    finally:
        monkeypatch.delenv("AGRO_HERRAMIENTAS")
        importlib.reload(t)


def _ids_en_teselas(ruta: Path) -> set[str]:
    # tippecanoe-decode (WSL) recorre todas las teselas; sort -u deja un id por línea
    cmd = (f"tippecanoe-decode '{ruta_wsl(ruta)}' | grep -a -o '\"unidad_id\": *\"[^\"]*\"' | sort -u")
    out = subprocess.run(["wsl", "-d", "Ubuntu-24.04", "--", "bash", "-c", cmd], capture_output=True, text=True,
                         encoding="utf-8", check=True).stdout
    return {l.split('"')[3] for l in out.splitlines() if l}


@pytest.mark.datos_reales
@pytest.mark.parametrize("nivel", [0, 1, 2])
def test_ids_de_teselas_son_los_ids_de_las_unidades(nivel):
    import pyogrio
    pm = TESELAS / f"adm{nivel}.pmtiles"
    gp = PROCESADOS / "unidades.gpkg"
    if not (pm.exists() and gp.exists()):
        pytest.skip("falta construir teselas o unidades")
    esperados = set(pyogrio.read_dataframe(gp, layer=f"adm{nivel}", read_geometry=False, columns=["unidad_id"])["unidad_id"])
    assert _ids_en_teselas(pm) == esperados


@pytest.mark.datos_reales
@pytest.mark.skipif(not (TESELAS / "adm0.pmtiles").exists(), reason="falta construir")
def test_teselas_llevan_solo_cinco_propiedades():
    cmd = (f"tippecanoe-decode '{ruta_wsl(TESELAS / 'adm0.pmtiles')}' | "
           "grep -a -m1 -o '\"properties\": { \"[^}]*\"unidad_id\"[^}]*}'")
    linea = subprocess.run(["wsl", "-d", "Ubuntu-24.04", "--", "bash", "-c", cmd], capture_output=True, text=True,
                           encoding="utf-8").stdout
    import re
    assert set(re.findall(r'"(\w+)":', linea)) - {"properties"} == {"unidad_id", "nombre", "nivel", "iso3", "padre_id"}
