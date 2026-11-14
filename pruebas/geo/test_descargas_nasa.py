# asistido por SI: Claude Code (Anthropic), pruebas de la descarga con subconjunto de NASA (T-D3)
import json
import threading

import pytest

from simulacion.geo.descargas_nasa import RegistroHashes, bajar_subconjunto, url_dap4

HDF = b"\x89HDF\r\n\x1a\n" + b"x" * 100


class Resp:
    def __init__(self, status=200, cuerpo=HDF):
        self.status_code, self.cuerpo = status, cuerpo

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError(f"http {self.status_code}")

    def iter_content(self, n):
        yield self.cuerpo


class Sesion:
    def __init__(self, *respuestas):
        self.respuestas, self.llamadas = list(respuestas), 0

    def get(self, url, **kw):
        self.llamadas += 1
        r = self.respuestas.pop(0)
        if isinstance(r, Exception):
            raise r
        return r


def test_url_dap4_codifica_rutas_y_separador():
    u = url_dap4("https://h/x", ["/G/a b", "/G/c"])
    assert u == "https://h/x.dap.nc4?dap4.ce=/G/a%20b;/G/c"


def test_reintenta_y_deja_el_archivo_final(tmp_path):
    s = Sesion(ConnectionError("x"), Resp(503), Resp())
    n, h = bajar_subconjunto(s, "https://h/x", tmp_path / "a.nc4", espera=0)
    assert s.llamadas == 3 and n == len(HDF) and len(h) == 64
    assert (tmp_path / "a.nc4").exists() and not (tmp_path / "a.nc4.parcial").exists()


def test_rechaza_cuerpo_que_no_es_hdf5(tmp_path):
    s = Sesion(*[Resp(cuerpo=b"<html>error</html>")] * 3)
    with pytest.raises(RuntimeError):
        bajar_subconjunto(s, "https://h/x", tmp_path / "a.nc4", reintentos=3, espera=0)
    assert not (tmp_path / "a.nc4").exists()


def test_archivo_existente_no_se_vuelve_a_pedir(tmp_path):
    (tmp_path / "a.nc4").write_bytes(HDF)
    s = Sesion()
    n, _ = bajar_subconjunto(s, "https://h/x", tmp_path / "a.nc4", espera=0)
    assert s.llamadas == 0 and n == len(HDF)


def test_registro_de_hashes_sin_carreras(tmp_path):
    reg = RegistroHashes(tmp_path / "h.jsonl")

    def escribir(k):
        for i in range(50):
            reg.anotar(f"id{k}_{i}", 1, "a" * 64)

    hilos = [threading.Thread(target=escribir, args=(k,)) for k in range(8)]
    [t.start() for t in hilos]
    [t.join() for t in hilos]
    filas = [json.loads(l) for l in (tmp_path / "h.jsonl").read_text().splitlines()]
    assert len(filas) == 400


@pytest.mark.datos_reales
def test_mod13c2_hashes_registrados_coinciden_con_los_archivos():
    import os
    from pathlib import Path
    from simulacion.geo.descargas import sha256_archivo
    datos = Path(os.environ.get("AGRO_DATOS", "datos"))
    ruta = datos / "crudos/registros/hashes_mod13c2.jsonl"
    if not ruta.exists():
        pytest.skip("sin descarga")
    filas = {json.loads(l)["id"]: json.loads(l) for l in ruta.read_text().splitlines()}
    for id_, f in list(filas.items())[:5]:  # muestra: el hash completo de 300 archivos tarda
        arch = datos / "crudos/mod13c2" / (id_.removeprefix("mod13c2_") + ".nc4")
        assert arch.stat().st_size == f["bytes"] and sha256_archivo(arch) == f["sha256"]
        assert arch.read_bytes()[:8] == b"\x89HDF\r\n\x1a\n"
