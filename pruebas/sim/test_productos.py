# asistido por SI: Claude Code (Anthropic), escritura y revisión de código; base del prototipo migrada en el hackatón
import numpy as np
import pytest

from simulacion.config import N_MESES
from simulacion.productos import (
    B_CALIDAD_BAJA, B_FUERA_COBERTURA, B_HUECO, B_PROVISIONAL,
    aplicar_cobertura, bandera_mes, fraccion_dias,
)
from simulacion.tiempo import mes_id


def test_smap_l3_marzo_2015():
    f = fraccion_dias("smap_l3")
    assert f.shape == (N_MESES,)
    assert f[mes_id(2015, 3)] == pytest.approx(1 / 31)
    assert f[mes_id(2015, 2)] == 0


def test_smap_l3_huecos():
    f = fraccion_dias("smap_l3")
    assert f[mes_id(2019, 6)] == pytest.approx(18 / 30)
    assert 0 < f[mes_id(2022, 8)] < 1
    assert 0 < f[mes_id(2022, 9)] < 1
    assert (f[mes_id(2015, 3):] > 0).all()


def test_smap_l4_sin_huecos():
    assert fraccion_dias("smap_l4")[mes_id(2019, 6)] == 1


def test_gldas_termina_julio_2026():
    f = fraccion_dias("gldas")
    assert f[mes_id(2026, 7)] == 1 and f[mes_id(2026, 8)] == 0


def test_imerg_final_hasta_septiembre_2025():
    b = bandera_mes("imerg")
    assert not b[mes_id(2025, 9)] & B_PROVISIONAL
    assert b[mes_id(2025, 10)] & B_PROVISIONAL
    assert b[mes_id(2000, 3)] & B_CALIDAD_BAJA
    assert not b[mes_id(2000, 6)] & B_CALIDAD_BAJA


def test_mod13_fechas():
    f = fraccion_dias("mod13")
    assert f[mes_id(2000, 1)] == 0 and f[mes_id(2000, 2)] > 0 and f[mes_id(2026, 11)] == 0


def test_mod16_2026_provisional():
    b = bandera_mes("mod16")
    assert b[mes_id(2026, 1)] & B_PROVISIONAL
    assert not b[mes_id(2025, 12)] & B_PROVISIONAL


def test_grace_33_huecos():
    f = fraccion_dias("grace")
    a, z = mes_id(2002, 4), mes_id(2026, 8)
    assert (f[a:z + 1] == 0).sum() == 33
    assert (f[mes_id(2017, 7):mes_id(2018, 5) + 1] == 0).all()
    assert f[a - 1] == 0 and bandera_mes("grace")[a - 1] & B_FUERA_COBERTURA
    assert bandera_mes("grace")[mes_id(2017, 8)] & B_HUECO


def test_aplicar_cobertura_nunca_cero():
    v = np.ones((2, N_MESES))
    out, frac, ban = aplicar_cobertura(v, "gldas")
    m = mes_id(2026, 8)
    assert np.isnan(out[:, m]).all() and frac[m] == 0 and ban[m] & B_FUERA_COBERTURA
    assert out[0, mes_id(2026, 7)] == 1
