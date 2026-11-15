# asistido por SI: Claude Code (Anthropic), pruebas de que el despliegue falla si dist o los metadatos de un .pmtiles llevan rutas locales o el usuario de la máquina
import getpass
import gzip
from pathlib import Path

import pytest

from mapa_estatico import construir as c

ORIGINAL = Path("C:/NASA/compartir/adm0.pmtiles")
LIMPIA = Path("C:/NASA/teselas_publicas/adm0.pmtiles")


def test_detecta_rutas_locales_en_texto_y_en_gz(tmp_path):
    (tmp_path / "assets").mkdir()
    (tmp_path / "assets" / "a.js").write_text('const r="C:\\\\Users\\\\x\\\\datos"', encoding="utf-8")
    (tmp_path / "b.json.gz").write_bytes(gzip.compress(b'{"origen": "/home/alguien/tmp/x.csv"}'))
    (tmp_path / "limpio.js").write_text("const ok = 'Saint Andrews'", encoding="utf-8")
    hallazgos = c.buscar_fugas(tmp_path)
    assert sorted(h.split(":")[0] for h in hallazgos) == ["assets/a.js", "b.json.gz"]


def test_detecta_el_usuario_como_segmento_de_ruta(tmp_path):
    u = getpass.getuser()
    (tmp_path / "x.html").write_text(f"<p>D:/{u}/proyecto</p>", encoding="utf-8")
    assert c.buscar_fugas(tmp_path)


@pytest.mark.skipif(not (ORIGINAL.exists() and LIMPIA.exists()), reason="sin las teselas en C:/NASA/compartir y C:/NASA/teselas_publicas")
def test_metadatos_de_pmtiles_original_y_copia_limpia(tmp_path):
    a, b = tmp_path / "a", tmp_path / "b"
    a.mkdir(), b.mkdir()
    (a / "adm0.pmtiles").write_bytes(ORIGINAL.read_bytes())
    (b / "adm0.pmtiles").write_bytes(LIMPIA.read_bytes())
    assert c.buscar_fugas(a), "la tesela original lleva la ruta interna en sus metadatos"
    assert c.buscar_fugas(b) == []


def test_el_despliegue_falla_si_hay_fugas(tmp_path, monkeypatch):
    datos = tmp_path / "datos"
    for o in (*c.ARCHIVOS_DESPLIEGUE, "unidades.gpkg"):
        (datos / o).parent.mkdir(parents=True, exist_ok=True)
        (datos / o).write_bytes(b"x")
    (datos / "indice_busqueda.json.gz").write_bytes(gzip.compress(b'["/home/alguien/indice"]'))
    dist = tmp_path / "dist"
    dist.mkdir()
    monkeypatch.setattr(c, "construir_geo", lambda gpkg, salida: (salida.mkdir(parents=True, exist_ok=True), (salida / "unidades_geo.json.gz").write_bytes(b"{}"))[1])
    with pytest.raises(c.ErrorDespliegue, match="rutas locales"):
        c.desplegar(dist, {"AGROVERSEX_DATOS": str(datos)})
