# asistido por SI: Claude Code, pruebas de la máscara Fmask de HLS (T-D5 Parte B)
import numpy as np

from lotes_demo.hls_validez import clasificar, tabla_mensual


def test_bits_cloud_adjacent_shadow_snow_invalidan():
    f = np.array([0, 2, 4, 8, 16, 32, 255], dtype=np.uint8)
    obs, ok = clasificar(f)
    # 0 claro; 2 nube; 4 adyacente; 8 sombra; 16 nieve invalidan; 32 agua es válida; 255 sin dato
    assert ok.tolist() == [True, False, False, False, False, True, False]
    assert obs.tolist() == [True] * 6 + [False]


def test_aerosol_no_invalida():
    obs, ok = clasificar(np.array([64 + 128], dtype=np.uint8))
    assert ok[0] and obs[0]


def test_tabla_mensual_fraccion_por_pixel_y_mes():
    # dos escenas de enero: pixel 0 válido 1 de 2, pixel 1 válido 2 de 2
    esc = [("2023-01-05", np.array([True, True]), np.array([True, True])),
           ("2023-01-10", np.array([True, True]), np.array([False, True]))]
    t = tabla_mensual(esc)
    assert t["2023-01"]["fraccion_pixel"].tolist() == [0.5, 1.0]
    assert t["2023-01"]["n_escenas"] == 2
