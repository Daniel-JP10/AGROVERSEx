# asistido por SI: Claude Code (Anthropic), escritura y revisión de código; base del prototipo migrada en el hackatón
"""Climatología base desde normales WorldClim 2.1 (1970-2000) por unidad, con fixtures sintéticos."""
import numpy as np
import pandas as pd
import pytest

from simulacion import clima

M = np.arange(12)
TAVG = 15 + 8 * np.cos(2 * np.pi * (M - 6) / 12)
TMIN, TMAX = TAVG - 5, TAVG + 5            # amplitud diaria 10 °C
PREC = 60 + 40 * np.cos(2 * np.pi * (M - 5) / 12)
SRAD = 12000 + 6000 * np.cos(2 * np.pi * (M - 6) / 12)   # kJ/m²/día
N_U = 40


def _geo():
    ids = [f"N{i}" for i in range(N_U)] + ["RESP"]
    return pd.DataFrame({"iso3": "XXX", "punto_lat": 40.0, "elev_media": 100.0, "koppen": 20}, index=ids)


def _normales():
    ids = [f"N{i}" for i in range(N_U)]
    f = pd.DataFrame({"unidad_id": np.repeat(ids, 12), "mes": np.tile(M + 1, N_U), "tavg": np.tile(TAVG, N_U),
                      "tmin": np.tile(TMIN, N_U), "tmax": np.tile(TMAX, N_U), "prec": np.tile(PREC, N_U),
                      "srad": np.tile(SRAD, N_U), "fraccion_valida": 1.0})
    return f


@pytest.fixture(scope="module")
def sim():
    geo = _geo()
    return clima.generar_clima(list(geo.index), slice(None), geo=geo, normales=_normales())


def test_temperatura_sigue_normal_mas_tendencia(sim):
    # normal centrada en 1985, serie desde 2000: base + tendencia · 1,5 décadas; media 2000-2025 suma 1,296 décadas más
    tend = clima.tendencia_unidad("XXX")
    t = sim.t2m[:N_U, :312].reshape(N_U, 26, 12).mean(axis=(0, 1))
    esperado = TAVG + tend * (clima.DECADAS_NORMAL_A_BASE + 1.296)
    assert np.abs(t - esperado).max() < 0.2


def test_lluvia_y_radiacion_siguen_normal(sim):
    p = sim.precip[:N_U, :312].reshape(N_U, 26, 12).mean(axis=(0, 1))
    assert np.abs(p / PREC - 1).max() < 0.1
    r = sim.rad_sw[:N_U, :312].reshape(N_U, 26, 12).mean(axis=(0, 1))
    assert np.abs(r / (SRAD / 1000) - 1).max() < 0.06


def test_amplitud_diaria_mensual(sim):
    d = (sim.t2m_max - sim.t2m_min)[:N_U, :12]
    assert np.allclose(d, 10.0, atol=1e-6)


def test_respaldo_rotulado_y_contado(sim):
    assert sim.sin_normales.tolist() == [False] * N_U + [True]
    geo = _geo().loc[["RESP"]]
    sola = clima.generar_clima(["RESP"], slice(None), geo=geo, normales=_normales())
    np.testing.assert_array_equal(sola.t2m, sim.t2m[-1:])  # misma fórmula de antes
    assert clima.contar_sin_normales(sim) == 1


def test_sin_archivo_todo_respaldo(monkeypatch, tmp_path):
    monkeypatch.setenv("AGROVERSEX_CLIM_NORMAL", str(tmp_path / "no_existe.sqlite"))
    geo = _geo().loc[["RESP"]]
    assert clima.generar_clima(["RESP"], slice(None), geo=geo).sin_normales.all()
