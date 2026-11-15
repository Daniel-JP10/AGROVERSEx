# asistido por SI: Claude Code (Anthropic), escritura y revisión de código; base del prototipo migrada en el hackatón
from calendar import monthrange
from datetime import date

from simulacion.config import FECHA_INICIO


def mes_id(anio: int, mes: int) -> int:
    # Índice mensual: 0 es ene-2000 (INICIAR §8.3)
    return (anio - 2000) * 12 + mes - 1


def mes_a_fecha(m: int) -> tuple[int, int]:
    return 2000 + m // 12, m % 12 + 1


def dias_del_mes(m: int) -> int:
    return monthrange(*mes_a_fecha(m))[1]


def dia_id(d: date) -> int:
    # Días desde 2000-01-01
    return (d - FECHA_INICIO).days
