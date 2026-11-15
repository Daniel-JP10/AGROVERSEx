# asistido por SI: Claude Code (Anthropic), escritura y revisión de código; base del prototipo migrada en el hackatón
from datetime import date

from simulacion.tiempo import dia_id, dias_del_mes, mes_a_fecha, mes_id
from simulacion.config import N_MESES


def test_mes_id_extremos():
    assert mes_id(2000, 1) == 0
    assert mes_id(2026, 11) == 322


def test_n_meses_cubre_hasta_nov_2026():
    # 323 meses: de ene-2000 a nov-2026 inclusive (INICIAR §5.1)
    assert N_MESES == mes_id(2026, 11) + 1


def test_mes_ida_vuelta():
    for m in range(N_MESES):
        assert mes_id(*mes_a_fecha(m)) == m


def test_dias_febrero_bisiesto():
    assert dias_del_mes(mes_id(2024, 2)) == 29
    assert dias_del_mes(mes_id(2015, 2)) == 28


def test_dia_id_ultimo():
    # 2000-01-01 es el día 0; 2026-11-05 cae en 9805 (INFERENCIA, cálculo manual)
    assert 9800 <= dia_id(date(2026, 11, 5)) <= 9810
    assert dia_id(date(2000, 1, 1)) == 0
