# asistido por SI: Claude Code (Anthropic), escritura y revisión de código; base del prototipo migrada en el hackatón
import sqlite3
import subprocess
from pathlib import Path

import pytest

from simulacion.config import GEO_SQLITE, PROCESADOS
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
    assert "--drop-densest-as-needed" not in c
    assert "--coalesce-densest-as-needed" not in c
    assert c[-1] == "/in" and c[c.index("-Z") + 1] == "5" and c[c.index("-z") + 1] == "12"


def test_comando_mapshaper_keep_shapes():
    c = comando_mapshaper([Path("a.geojson")], Path("salida"), 10)
    assert "keep-shapes" in c and "combine-files" in c
    assert "10%" in c


def test_contar_ids(tmp_path):
    f = tmp_path / "x.geojson"
    f.write_text('{"features": [{"properties": {"id": "A.1_1", "padre_id": "A"}},\n'
                 '{"properties": {"id": "A.2_1", "padre_id": "A"}}]}', encoding="utf-8")
    assert contar_ids(f) == {"A.1_1", "A.2_1"}


def test_partir_y_unir_conserva_ids(tmp_path):
    f = tmp_path / "adm2.geojson"
    filas = [f'{{ "type": "Feature", "properties": {{ "id": "{i}", "iso3": "{i[:3]}" }}, "geometry": null }}'
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
    f = lambda i: f'{{ "type": "Feature", "properties": {{ "id": "{i}" }}, "geometry": null }}'
    crudo.write_text('{\n"features": [\n' + ",\n".join(map(f, ["A", "B", "C"])) + "\n]\n}\n")
    simple.write_bytes(b'{"type":"FeatureCollection","features":[\n'
                       b'{"type":"Feature","properties":{"id":"A"}}\n]}\n')
    assert completar_perdidos(crudo, simple) == 2
    import json
    assert contar_ids(simple) == {"A", "B", "C"} and len(json.loads(simple.read_text())["features"]) == 3
    assert completar_perdidos(crudo, simple) == 0


@pytest.mark.datos_reales
@pytest.mark.skipif(not (SIMPLIFICADOS / "adm2.geojson").exists(), reason="falta construir")
@pytest.mark.parametrize("nivel", [0, 1, 2])
def test_simplificacion_conserva_ids(nivel):
    crudo = contar_ids(PROCESADOS / f"limites_crudos/adm{nivel}.geojson")
    simple = contar_ids(SIMPLIFICADOS / f"adm{nivel}.geojson")
    con = sqlite3.connect(GEO_SQLITE)
    # adm0 lleva también las zonas en disputa (nivel 9)
    niveles = (0, 9) if nivel == 0 else (nivel, nivel)
    n = con.execute("select count(*) from unidad where nivel in (?, ?)", niveles).fetchone()[0]
    con.close()
    assert simple == crudo and len(simple) == n


@pytest.mark.datos_reales
@pytest.mark.skipif(not (TESELAS / "adm2.pmtiles").exists(), reason="falta construir")
def test_pmtiles_adm2_capa_y_zoom():
    out = subprocess.run([str(HERRAMIENTAS / "bin/pmtiles.exe"), "show",
                          str(TESELAS / "adm2.pmtiles")],
                         capture_output=True, text=True, check=True).stdout
    assert "adm2" in out and "max zoom: 12" in out
