# asistido por SI: Claude Code (Anthropic), escritura y revisión de código; base del prototipo migrada en el hackatón
import numpy as np

from simulacion.azar import rng_unidad
from simulacion.incertidumbre import (
    banda_p10_p90, err_lst, err_precip, err_sm_l4, err_sm_sin_campo, err_tws, nivel_confianza,
)


def test_banda_ordenada():
    r = np.random.default_rng(1)
    v, d = r.normal(size=(5, 50)), r.random((5, 50))
    p10, p90 = banda_p10_p90(v, d)
    assert (p10 <= v).all() and (v <= p90).all()


def test_err_no_negativo():
    r = np.random.default_rng(2)
    x, frac = r.random((4, 30)) * 10, r.random((4, 30))
    assert (err_precip(x, frac) >= 0).all()
    assert (err_precip(x, frac, provisional=True) >= err_precip(x, frac)).all()
    assert (err_sm_l4(x / 10) >= 0).all()
    assert (err_sm_sin_campo(7) >= 0).all() and err_sm_sin_campo(7).shape == (7,)
    assert (err_tws(x - 5, 1.5) >= 0).all()
    assert (err_lst(x + 280, r.integers(0, 4, x.shape)) >= 0).all()


def test_confianza_regla():
    f = np.array([0.9, 0.9, 0.3, 0.9])
    assert nivel_confianza(f[:1], "observado", True)[0] == 2
    assert nivel_confianza(f[:1], "reanalisis", True)[0] == 1
    assert nivel_confianza(f[2:3], "observado", True)[0] == 0
    assert nivel_confianza(f[3:], "observado", False)[0] == 0


def _ruido(ids):
    return np.stack([rng_unidad(i, "ruido").normal(size=323) for i in ids])


def test_bloque_invariante():
    ids = [f"u{i}" for i in range(10)]
    assert np.array_equal(_ruido(ids), np.vstack([_ruido(ids[:5]), _ruido(ids[5:])]))
