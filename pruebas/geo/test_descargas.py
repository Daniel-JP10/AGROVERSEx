# asistido por SI: Claude Code (Anthropic), escritura y revisión de código; base del prototipo migrada en el hackatón
import functools
import http.server
import threading
from pathlib import Path

import pytest

from simulacion.geo.descargas import (
    Recurso, _descargar, cargar_manifiesto, registrar_hash, sha256_archivo,
)

ENTRADA = (
    "- id: {id}\n  url: {url}\n  archivo: a.bin\n  licencia: L\n"
    "  ficha: f.md\n  sha256: null\n  bytes_esperados: null\n"
)


def _manifiesto(tmp_path, *entradas):
    ruta = tmp_path / "m.yaml"
    ruta.write_text("".join(entradas), encoding="utf-8")
    return ruta


def test_manifiesto_rechaza_id_repetido(tmp_path):
    e = ENTRADA.format(id="x", url="https://a.org/a")
    with pytest.raises(ValueError):
        cargar_manifiesto(_manifiesto(tmp_path, e, e))


def test_manifiesto_rechaza_http(tmp_path):
    e = ENTRADA.format(id="x", url="http://a.org/a")
    with pytest.raises(ValueError):
        cargar_manifiesto(_manifiesto(tmp_path, e))


def test_sha256_conocido(tmp_path):
    f = tmp_path / "abc"
    f.write_bytes(b"abc")
    assert sha256_archivo(f) == (
        "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"
    )


def test_registrar_hash(tmp_path):
    ruta = _manifiesto(tmp_path, ENTRADA.format(id="x", url="https://a.org/a"))
    registrar_hash(ruta, "x", "ab" * 32)
    assert cargar_manifiesto(ruta)[0].sha256 == "ab" * 32


def test_descargar_detecta_hash_erroneo(tmp_path):
    srv_dir = tmp_path / "srv"
    srv_dir.mkdir()
    (srv_dir / "a.bin").write_bytes(b"abc")
    h = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(srv_dir))
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), h)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    try:
        r = Recurso("x", f"http://127.0.0.1:{srv.server_port}/a.bin", "a.bin",
                    "L", "f.md", "0" * 64, None)
        dest = tmp_path / "out"
        with pytest.raises(ValueError):
            _descargar(r, dest, esquemas=("http", "https"))
        assert not (dest / "a.bin").exists()
    finally:
        srv.shutdown()


DATOS = bytes(range(256)) * 40


class _Manejador(http.server.BaseHTTPRequestHandler):
    modo = "range"  # "range" entiende Range; "ignora" siempre responde 200

    def log_message(self, *a):
        pass

    def do_GET(self):
        rango = self.headers.get("Range")
        if rango and self.modo == "range":
            ini = int(rango.split("=")[1].rstrip("-"))
            if ini >= len(DATOS):
                self.send_response(416)
                self.send_header("Content-Range", f"bytes */{len(DATOS)}")
                self.send_header("Content-Length", "0")
                self.end_headers()
                return
            self.send_response(206)
            self.send_header("Content-Range", f"bytes {ini}-{len(DATOS)-1}/{len(DATOS)}")
            cuerpo = DATOS[ini:]
        else:
            self.send_response(200)
            cuerpo = DATOS
        self.send_header("Content-Length", str(len(cuerpo)))
        self.end_headers()
        self.wfile.write(cuerpo)


@pytest.fixture
def servidor():
    def crear(modo="range"):
        clase = type("M", (_Manejador,), {"modo": modo})
        srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), clase)
        threading.Thread(target=srv.serve_forever, daemon=True).start()
        servidores.append(srv)
        return f"http://127.0.0.1:{srv.server_port}/a.bin"
    servidores = []
    yield crear
    for s in servidores:
        s.shutdown()


H = __import__("hashlib").sha256(DATOS).hexdigest()
HTTP = ("http", "https")


def _rec(url, sha=H, n=None):
    return Recurso("x", url, "a.bin", "L", "f.md", sha, n)


def test_reanuda_con_206(servidor, tmp_path):
    (tmp_path / "a.bin.parcial").write_bytes(DATOS[:1000])
    f = _descargar(_rec(servidor()), tmp_path, HTTP)
    assert f.read_bytes() == DATOS and sha256_archivo(f) == H


def test_servidor_ignora_range(servidor, tmp_path):
    (tmp_path / "a.bin.parcial").write_bytes(DATOS[:1000])
    f = _descargar(_rec(servidor("ignora")), tmp_path, HTTP)
    assert f.read_bytes() == DATOS


def test_416_con_parcial_basura_sin_esperado(servidor, tmp_path):
    (tmp_path / "a.bin.parcial").write_bytes(b"x" * (len(DATOS) + 50))
    f = _descargar(_rec(servidor(), sha=None), tmp_path, HTTP)
    assert f.read_bytes() == DATOS


def test_416_con_parcial_exacto_basura_sin_esperado(servidor, tmp_path):
    (tmp_path / "a.bin.parcial").write_bytes(b"x" * len(DATOS))
    f = _descargar(_rec(servidor(), sha=None), tmp_path, HTTP)
    assert f.read_bytes() == DATOS


def test_archivo_en_subcarpeta_inexistente(servidor, tmp_path):
    r = Recurso("x", servidor(), "sub/dir/a.bin", "L", "f.md", H, None)
    assert _descargar(r, tmp_path / "nuevo", HTTP).read_bytes() == DATOS
    assert (tmp_path / "nuevo/sub/dir/a.bin").exists()


def test_bytes_esperados_erroneo(servidor, tmp_path):
    with pytest.raises(ValueError):
        _descargar(_rec(servidor(), sha=None, n=len(DATOS) + 1), tmp_path, HTTP)
    assert not (tmp_path / "a.bin").exists()
