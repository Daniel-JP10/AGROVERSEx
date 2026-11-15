# asistido por SI: Claude Code (Anthropic), escritura y revisión de código; base del prototipo migrada en el hackatón
import pytest

# estaticos importa zonal (rasterio, exactextract): solo corre en WSL
pytest.importorskip("exactextract")

from simulacion.geo.estaticos import RANGOS, _variable, limpiar_partes  # noqa: E402


def test_limpiar_partes_vacia_pkl_y_tmp(tmp_path):
    for n in ("0.pkl", "1.pkl", "2.tmp", "otro.txt"):
        (tmp_path / n).write_bytes(b"x")
    assert limpiar_partes(tmp_path) == 2
    assert [f.name for f in tmp_path.iterdir()] == ["otro.txt"]


def test_variable_lleva_rango_fisico():
    v = _variable("phh2o_0_30", "n", "pH", "p", "2", "d", "r", "c", "f", "e")
    assert (v[6], v[7]) == (3, 11) == RANGOS["phh2o"]
    assert _variable("elev_min", "n", "m", "p", "2", "d", "r", "c", "f", "e")[6:8] == (-500, 9000)
