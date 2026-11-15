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


# V5: rutas con barra normal, Unix temporales, de red y la carpeta de herramientas; sin re.I
@pytest.mark.parametrize("texto", [
    'const a="C:/NASA/herramientas-despliegue"',
    'const a="X:/datos/x.csv"',
    '{"r": "/mnt/c/NASA/x"}',
    '{"r": "/tmp/agro/x"}',
    '{"r": "/root/x"}',
    'const a="\\\\servidor\\compartido\\x"',
    'instalado en herramientas-despliegue',
])
def test_detecta_rutas_de_v5(tmp_path, texto):
    (tmp_path / "a.js").write_text(texto, encoding="utf-8")
    assert c.buscar_fugas(tmp_path), texto


@pytest.mark.parametrize("texto", [
    "a?b:/x/.test(c)",
    r"{e:/^\d+$/}",
    "https://gibs.earthdata.nasa.gov/wmts",
    'new RegExp("\\s*\\d")',
    "const c = 'c:/minúscula no es unidad'",
])
def test_no_confunde_codigo_minificado(tmp_path, texto):
    (tmp_path / "a.js").write_text(texto, encoding="utf-8")
    assert c.buscar_fugas(tmp_path) == [], texto


def test_la_letra_de_unidad_no_se_busca_en_binarios(tmp_path):
    (tmp_path / "a.png").write_bytes(b"\x89PNG\x00Q:/x\x00")
    assert c.buscar_fugas(tmp_path) == []
    (tmp_path / "b.png").write_bytes(b"\x89PNG\x00/Users/alguien\x00")
    assert c.buscar_fugas(tmp_path)


def test_dist_con_fugas_se_borra(tmp_path, monkeypatch):
    datos = tmp_path / "datos"
    for o in (*c.ARCHIVOS_DESPLIEGUE, "unidades.gpkg"):
        (datos / o).parent.mkdir(parents=True, exist_ok=True)
        (datos / o).write_bytes(b"x")
    dist = tmp_path / "dist"
    dist.mkdir()
    (dist / "a.js").write_text('"C:/NASA/x"', encoding="utf-8")
    monkeypatch.setattr(c, "construir_geo", lambda gpkg, salida: (salida.mkdir(parents=True, exist_ok=True), (salida / "unidades_geo.json.gz").write_bytes(b"{}"))[1])
    with pytest.raises(c.ErrorDespliegue, match="rutas locales"):
        c.desplegar(dist, {"AGROVERSEX_DATOS": str(datos)})
    assert not dist.exists()


def test_agroversex_teselas_mal_puesto_da_mensaje_claro(tmp_path):
    datos = tmp_path / "datos"
    for o in (*c.ARCHIVOS_DESPLIEGUE, "unidades.gpkg"):
        (datos / o).parent.mkdir(parents=True, exist_ok=True)
        (datos / o).write_bytes(b"x")
    dist = tmp_path / "dist"
    dist.mkdir()
    with pytest.raises(c.ErrorDespliegue, match="AGROVERSEX_TESELAS=.*no tiene adm0.pmtiles"):
        c.desplegar(dist, {"AGROVERSEX_DATOS": str(datos), "AGROVERSEX_TESELAS": str(tmp_path / "no_existe")})


def test_limites_de_pages(tmp_path, monkeypatch):
    monkeypatch.setattr(c, "MAX_ARCHIVO", 10)
    (tmp_path / "teselas").mkdir()
    (tmp_path / "teselas" / "adm2.pmtiles").write_bytes(b"x" * 50)
    (tmp_path / "chico.js").write_bytes(b"x" * 5)
    assert c.revisar_limites(tmp_path) == []
    (tmp_path / "grande.json").write_bytes(b"x" * 11)
    assert c.revisar_limites(tmp_path) == ["grande.json pesa 11 B"]
