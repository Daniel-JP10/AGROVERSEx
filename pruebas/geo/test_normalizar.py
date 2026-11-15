# asistido por SI: Claude Code (Anthropic), escritura y revisión de código; base del prototipo migrada en el hackatón
from simulacion.geo.normalizar import normalizar_nombre


def test_extraer_una_sola_vez(tmp_path):
    import zipfile
    from simulacion.geo.extraer import extraer
    z = tmp_path / "a.zip"
    with zipfile.ZipFile(z, "w") as f:
        f.writestr("x/y.txt", "hola")
    assert extraer(z, tmp_path / "out") is True
    assert (tmp_path / "out/x/y.txt").read_text() == "hola"
    assert extraer(z, tmp_path / "out") is False


def test_normalizar():
    assert normalizar_nombre("Bogotá, D.C.") == "bogota d c"
    assert normalizar_nombre("  São   Paulo ") == "sao paulo"
    assert normalizar_nombre("Nariño") == "narino"
    assert normalizar_nombre(None) == ""
