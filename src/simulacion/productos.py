# asistido por SI: Claude Code (Anthropic), escritura y revisión de código; base del prototipo migrada en el hackatón
"""Calendario de cobertura por producto: fracción de días, huecos y banderas (INICIAR §5.2)."""
from dataclasses import dataclass
from datetime import date, timedelta

import numpy as np

from simulacion.config import FECHA_FIN_DIARIA, FECHA_INICIO, N_MESES
from simulacion.tiempo import dias_del_mes
from simulacion.variables import (  # noqa: F401  (se reexportan las banderas)
    B_CALIDAD_BAJA, B_FUERA_COBERTURA, B_HUECO, B_NIEVE, B_NUBE, B_PROVISIONAL,
)


@dataclass(frozen=True)
class Cobertura:
    producto: str
    inicio: date
    fin: date | None  # None: hasta FECHA_FIN_DIARIA
    huecos: tuple[tuple[date, date], ...]
    provisional_desde: date | None
    ficha: str
    calidad_baja: tuple[date, date] | None = None


def _meses(*pares: tuple[int, int]) -> tuple[tuple[date, date], ...]:
    # Cada (año, mes) se vuelve un hueco del primer al último día del mes
    return tuple((date(a, m, 1), date(a, m, dias_del_mes((a - 2000) * 12 + m - 1))) for a, m in pares)


_D = date
# FUENTE INICIAR 5.2, ficha EV-AGU-012: 33 meses sin solución (20 GRACE, 11 de hueco, 2 GRACE-FO)
# El CSV rotula 2018 como 2017 en ene-may del hueco; aquí van los meses reales.
_GRACE_NA = _meses(
    (2002, 6), (2002, 7), (2003, 6), (2011, 1), (2011, 6), (2012, 5), (2012, 10),
    (2013, 3), (2013, 8), (2013, 9), (2014, 2), (2014, 7), (2014, 12),
    (2015, 6), (2015, 10), (2015, 11), (2016, 4), (2016, 9), (2016, 10), (2017, 2),
    *[(2017, m) for m in range(7, 13)], *[(2018, m) for m in range(1, 6)],
    (2018, 8), (2018, 9),
)

_L3_HUECOS = ((_D(2019, 6, 19), _D(2019, 7, 23)), (_D(2022, 8, 6), _D(2022, 9, 20)))  # FUENTE INICIAR 5.2, ficha EV-AGU

COBERTURAS: dict[str, Cobertura] = {c.producto: c for c in (
    Cobertura("smap_l3", _D(2015, 3, 31), None, _L3_HUECOS, None, "EV-AGU"),
    Cobertura("smap_l4", _D(2015, 3, 31), None, (), None, "EV-AGU"),
    Cobertura("gldas", _D(2000, 1, 1), _D(2026, 7, 31), (), None, "EV-AGU"),
    # Final hasta 2025-09-30; después Late V07 provisional (SUPUESTO, decisión 15.2-A, revisión 2026-11-13)
    # Calidad reducida ene-may 2000: FUENTE INICIAR 5.2, ficha EV-AGU
    Cobertura("imerg", _D(2000, 1, 1), None, (), _D(2025, 10, 1), "EV-AGU",
              calidad_baja=(_D(2000, 1, 1), _D(2000, 5, 31))),
    # Meteorología desde 1981 y radiación desde 1984: cubre todo el periodo
    Cobertura("power", _D(1981, 1, 1), None, (), None, "EV-AGU, EV-CLI"),
    # GF hasta 2025-12-31; 2026 con MOD16A2 sin relleno. Inicio y fin en 2026 SUPUESTO: no están en §5.2
    Cobertura("mod16", FECHA_INICIO, None, (), _D(2026, 1, 1), "EV-VEG"),
    Cobertura("mod13", _D(2000, 2, 1), _D(2026, 10, 31), (), None, "EV-VEG"),
    Cobertura("mod11", _D(2000, 2, 1), None, (), None, "EV-VEG, EV-STK"),
    Cobertura("grace", _D(2002, 4, 1), _D(2026, 8, 31), _GRACE_NA, None, "EV-AGU-012"),
    # Solo se declara para la ficha: no tiene columna en mensual ni en lote_diario
    Cobertura("ecostress", _D(2018, 7, 9), None,
              ((_D(2018, 9, 29), _D(2018, 12, 4)), (_D(2019, 3, 14), _D(2019, 5, 14)), (_D(2020, 2, 17), _D(2020, 2, 17))),
              None, "EV-AGU"),
)}

_N_DIAS = (date(2026, 11, 30) - FECHA_INICIO).days + 1
_MES_DE_DIA = np.array([(d.year - 2000) * 12 + d.month - 1
                        for d in (FECHA_INICIO + timedelta(i) for i in range(_N_DIAS))])
_DIAS_MES = np.array([dias_del_mes(m) for m in range(N_MESES)])


def _dias(desde: date, hasta: date) -> np.ndarray:
    # Máscara de días (desde 2000-01-01) dentro de [desde, hasta]
    d = np.zeros(_N_DIAS, bool)
    a, z = max((desde - FECHA_INICIO).days, 0), (hasta - FECHA_INICIO).days
    d[a:z + 1] = True
    return d


def _por_mes(mascara: np.ndarray) -> np.ndarray:
    return np.bincount(_MES_DE_DIA, weights=mascara, minlength=N_MESES)


def _rango(c: Cobertura) -> np.ndarray:
    return _dias(c.inicio, c.fin or FECHA_FIN_DIARIA)


def fraccion_dias(producto: str) -> np.ndarray:
    c = COBERTURAS[producto]
    d = _rango(c)
    for a, z in c.huecos:
        d &= ~_dias(a, z)
    return _por_mes(d) / _DIAS_MES


def bandera_mes(producto: str) -> np.ndarray:
    c = COBERTURAS[producto]
    en_rango = _por_mes(_rango(c))
    sin_hueco = fraccion_dias(producto) * _DIAS_MES
    b = np.zeros(N_MESES, np.int64)
    b[en_rango == 0] |= B_FUERA_COBERTURA
    b[(en_rango > 0) & (sin_hueco < en_rango)] |= B_HUECO
    if c.provisional_desde:
        b[_por_mes(_rango(c) & _dias(c.provisional_desde, date(2026, 11, 30))) > 0] |= B_PROVISIONAL
    if c.calidad_baja:
        b[_por_mes(_dias(*c.calidad_baja)) > 0] |= B_CALIDAD_BAJA
    return b


def aplicar_cobertura(valor: np.ndarray, producto: str) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    # Sin cobertura el valor es NaN (nunca 0); la bandera dice por qué
    frac = fraccion_dias(producto)
    return np.where(frac > 0, valor, np.nan), frac, bandera_mes(producto)
