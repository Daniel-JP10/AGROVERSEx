# asistido por SI: Claude Code (Anthropic), pruebas de la regla de días válidos de IMERG Late (D-011)
import numpy as np
import pytest

from simulacion.geo.imerg_late import mensual_late, unidades_validas

FILL = -9999.9004


def _dias(n, h=1, w=3):
    return np.full((n, h, w), 2.0, dtype="float32")


def test_celda_con_80_por_ciento_es_valida_y_con_menos_es_nan():
    d = _dias(30)
    d[:6, 0, 0] = FILL          # 24 de 30 = 80 %: valida
    d[:7, 0, 1] = FILL          # 23 de 30 = 76,7 %: NaN
    media, n = mensual_late(d, 30, 0.8)
    assert media[0, 0] == pytest.approx(2.0) and np.isnan(media[0, 1])
    assert list(n[0]) == [24, 23, 30]


def test_mes_incompleto_queda_nan_aunque_todos_los_dias_sean_validos():
    media, _ = mensual_late(_dias(13), 30, 0.8)  # mes en curso: 13 de 30
    assert np.isnan(media).all()


def test_fill_no_entra_al_promedio_ni_se_cuenta_como_cero():
    d = _dias(30)
    d[:2, 0, 0] = FILL
    d[2:4, 0, 0] = 5.0
    media, _ = mensual_late(d, 30, 0.8)
    assert media[0, 0] == pytest.approx((26 * 2.0 + 2 * 5.0) / 28)


def test_unidad_valida_si_alguna_celda_valida():
    media = np.array([[np.nan, 1.0, np.nan]])
    celdas_por_unidad = [np.array([0, 2]), np.array([1, 2]), np.array([0])]
    assert list(unidades_validas(media, celdas_por_unidad)) == [False, True, False]
