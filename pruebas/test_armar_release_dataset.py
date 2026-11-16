# asistido por SI: Claude Code (Anthropic), prueba del armado del release del dataset abierto
import hashlib
import importlib.util
import json
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location("armar", RAIZ / "herramientas" / "armar_release_dataset.py")
armar_mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(armar_mod)


def _entrada(raiz, ruta, nombre, contenido):
    return {"raiz": raiz, "ruta": ruta, "nombre": nombre, "bytes": len(contenido),
            "sha256": hashlib.sha256(contenido).hexdigest()}


def _escenario(tmp_path):
    datos, repo = tmp_path / "datos", tmp_path / "repo"
    (datos / "consolidados").mkdir(parents=True)
    (repo / "gemelo").mkdir(parents=True)
    (datos / "consolidados" / "s.csv.gz").write_bytes(b"serie")
    (repo / "gemelo" / "lote.json").write_bytes(b"{}")
    (repo / "DATASET.md").write_text("ficha", encoding="utf-8")
    lista = {"archivos": [_entrada("datos", "consolidados/s.csv.gz", "s.csv.gz", b"serie"),
                          _entrada("repo", "gemelo/lote.json", "gemelo_lote.json", b"{}")]}
    return datos, repo, lista


def test_arma_y_verifica(tmp_path):
    datos, repo, lista = _escenario(tmp_path)
    salida = tmp_path / "rel"
    assert armar_mod.armar(lista, datos, salida, repo) == []
    assert (salida / "s.csv.gz").read_bytes() == b"serie"
    assert (salida / "gemelo_lote.json").is_file()
    assert (salida / "DATASET.md").is_file()
    assert "gemelo_lote.json" in (salida / "SHA256SUMS.txt").read_text(encoding="utf-8")


def test_detecta_sha_distinto_y_faltante(tmp_path):
    datos, repo, lista = _escenario(tmp_path)
    (repo / "gemelo" / "lote.json").write_bytes(b"[]")  # mismo tamaño, otro contenido
    lista["archivos"].append(_entrada("repo", "no_existe.json", "x.json", b"a"))
    salida = tmp_path / "rel"
    errores = armar_mod.armar(lista, datos, salida, repo)
    assert any("sha256 distinto" in e for e in errores)
    assert any("falta" in e for e in errores)
    assert not (salida / "gemelo_lote.json").exists()
    assert not (salida / "SHA256SUMS.txt").exists()


def test_lista_real_sin_ghcn_ni_nombres_repetidos():
    lista = json.loads((RAIZ / "herramientas" / "dataset_lista.json").read_text(encoding="utf-8"))
    nombres = [a["nombre"] for a in lista["archivos"]]
    assert len(nombres) == len(set(nombres))
    prohibidos = ("validacion_temperatura_ipiales", "comparacion_power_imerg", "lotes_demo.json", "COM00080370")
    assert not any(p in a["ruta"] for a in lista["archivos"] for p in prohibidos)
    # Los paquetes del gemelo de DEMO-COL-01 llevan el contraste con la estación GHCN; solo entra lote.json
    assert [a["ruta"] for a in lista["archivos"] if "gemelo/DEMO-COL-01" in a["ruta"]] == ["src/web/public/gemelo/DEMO-COL-01/lote.json"]
    # Los archivos del repo de la lista siguen idénticos a lo medido
    for a in lista["archivos"]:
        if a["raiz"] == "repo":
            assert armar_mod.sha256(RAIZ / a["ruta"]) == a["sha256"], a["ruta"]
