# asistido por SI: Claude Code (Anthropic), escritura y revisión de código; base del prototipo migrada en el hackatón
"""Variables físicas de agroversex.sqlite y su conversión a enteros escalados (INICIAR §5.2, §8.3)."""
from dataclasses import dataclass
from pathlib import Path

import numpy as np

AQUI = Path(__file__).parent
INT_NULO = -(2**31)  # centinela interno; escribir_sqlite lo traduce a NULL

# Bits de bandera_motivo (INICIAR §8.3; B_CALIDAD_BAJA es decisión técnica del controlador)
B_HUECO, B_NUBE, B_NIEVE, B_PROVISIONAL, B_FUERA_COBERTURA, B_CALIDAD_BAJA = (1 << i for i in range(6))


@dataclass(frozen=True)
class Var:
    id: str
    columna: str
    unidad_medida: str
    escala: float
    desplazamiento: float
    relleno: int | None  # entero de relleno del producto; None si no tiene o es PENDIENTE
    valido_min: float  # físico
    valido_max: float
    nivel_dato: str  # observado|modelo|reanalisis|indice|real_contexto
    producto: str
    version: str
    inicio: str
    fin: str
    etiqueta: str
    fuente_id: str


def _v(id, unidad, escala, vmin, vmax, nivel, producto, version, inicio, fin, etiqueta, fuente, relleno=None):
    return Var(id, id, unidad, escala, 0.0, relleno, vmin, vmax, nivel, producto, version, inicio, fin,
               etiqueta, fuente)


_SUP = "SUPUESTO (escala de diseño, revisión 2026-11-13)"
_IM = ("observado", "GPM IMERG Final V07 (Late V07 desde 2025-10)", "V07", "2000-01", "2026-11")
_PW = ("reanalisis", "NASA POWER", "v2.10.3", "2000-01", "2026-11")
_ET = ("observado", "MODIS MOD16A2GF (MOD16A2 en 2026)", "6.1", "2000-01", "2026-11")
_ND = ("indice", "MODIS MOD13Q1/MYD13Q1", "6.1", "2000-02", "2026-10")
_LS = ("observado", "MODIS MOD11A2", "6.1", "2000-02", "2026-11")
_SM = ("modelo", "SMAP L4 / L3 / GLDAS-2.1", "V008 / V006 / 2.1", "2000-01", "2026-11")
_GR = ("observado", "GRACE/GRACE-FO mascons JPL", "RL06.3M v04", "2002-04", "2026-08")
_HL = ("observado", "HLS HLSL30/HLSS30", "v2.0", "2013-04", "2026-11")

# precip: IMERG mensual publica mm/h (INICIAR §5.2); escribir_sqlite convierte desde mm/mes
# FUENTE §5.2: NDVI (escala, relleno -3000), LST (escala, relleno 0). ET: escala 0,1 de §5.2; relleno 32761
# de EV-VEG-003 (el catálogo trae solo 32761; la guía MOD16 lista 32761 a 32767, y 32762..32767 quedan
# fuera del rango válido). Fracciones y el resto: escala SUPUESTO.
_L = [
    _v("precip", "mm/h", 0.001, 0, 50, *_IM, "FUENTE producto, escala SUPUESTO", "EV-AGU"),
    _v("precip_err", "mm/h", 0.001, 0, 50, *_IM, _SUP, "EV-AGU"),
    _v("t2m", "°C", 0.01, -60, 60, *_PW, "FUENTE producto, escala SUPUESTO", "EV-AGU"),
    _v("t2m_p10", "°C", 0.01, -60, 60, *_PW, _SUP, "EV-AGU"),
    _v("t2m_p90", "°C", 0.01, -60, 60, *_PW, _SUP, "EV-AGU"),
    _v("t2m_max", "°C", 0.01, -60, 70, *_PW, _SUP, "EV-AGU"),
    _v("t2m_min", "°C", 0.01, -70, 60, *_PW, _SUP, "EV-AGU"),
    _v("rh2m", "%", 0.1, 0, 100, *_PW, _SUP, "EV-AGU"),
    _v("rad_sw", "MJ/m²/día", 0.01, 0, 35, *_PW, _SUP, "EV-AGU"),
    _v("et", "kg/m²/8 días", 0.1, 0, 3276, *_ET, "FUENTE §5.2; relleno FUENTE EV-VEG-003", "EV-VEG", 32761),
    _v("et_p10", "kg/m²/8 días", 0.1, 0, 3276, *_ET, _SUP, "EV-VEG"),
    _v("et_p90", "kg/m²/8 días", 0.1, 0, 3276, *_ET, _SUP, "EV-VEG"),
    _v("ndvi", "adimensional", 0.0001, -0.2, 1.0, *_ND, "FUENTE §5.2", "EV-VEG", -3000),
    _v("ndvi_p10", "adimensional", 0.0001, -0.2, 1.0, *_ND, "FUENTE §5.2", "EV-VEG", -3000),
    _v("ndvi_p90", "adimensional", 0.0001, -0.2, 1.0, *_ND, "FUENTE §5.2", "EV-VEG", -3000),
    _v("lst_dia", "K", 0.02, 250, 340, *_LS, "FUENTE §5.2", "EV-VEG", 0),
    _v("lst_err", "K", 0.02, 0, 50, *_LS, _SUP, "EV-VEG"),
    _v("sm_sup", "m³/m³", 0.001, 0, 0.9, *_SM, _SUP, "EV-AGU"),
    _v("sm_raiz", "m³/m³", 0.001, 0, 0.9, *_SM, _SUP, "EV-AGU"),
    _v("sm_err", "m³/m³", 0.001, 0, 0.9, *_SM, _SUP, "EV-AGU"),
    _v("tws", "cm", 0.01, -500, 500, *_GR, _SUP, "EV-AGU"),
    _v("tws_err", "cm", 0.01, 0, 500, *_GR, _SUP, "EV-AGU"),
    _v("nbr2", "adimensional", 0.0001, -1.0, 1.0, *_HL, _SUP, "EV-VEG"),
    _v("sm_verdad", "m³/m³", 0.001, 0, 0.9, "modelo", "simulación de lote", "demo", "2000-01", "2026-11", _SUP, "demo"),
    _v("sm_sensor", "m³/m³", 0.001, 0, 0.9, "modelo", "simulación de lote", "demo", "2000-01", "2026-11", _SUP, "demo"),
]
# Fracciones de cobertura válida, 0 a 1, tres cifras
_L += [_v(f"{p}_frac", "fraccion", 0.001, 0, 1, "indice", "derivado", "demo", "2000-01", "2026-11", _SUP, "demo")
       for p in ("precip", "et", "ndvi", "lst", "sm", "tws")]

VARIABLES: dict[str, Var] = {v.id: v for v in _L}


def a_entero(v: np.ndarray, var: Var) -> np.ndarray:
    """int32 escalado; NaN pasa a INT_NULO."""
    v = np.asarray(v, dtype=np.float64)
    ent = np.rint((np.where(np.isnan(v), 0.0, v) - var.desplazamiento) / var.escala)
    return np.where(np.isnan(v), INT_NULO, ent).astype(np.int32)


def de_entero(i: np.ndarray, var: Var) -> np.ndarray:
    i = np.asarray(i)
    return np.where(i == INT_NULO, np.nan, i * var.escala + var.desplazamiento)


def crear_esquema(con) -> None:
    """Crea las 18 tablas: primero las compartidas con la fase 1, luego las de la fase 2."""
    con.executescript((AQUI / "geo" / "esquema_geo.sql").read_text(encoding="utf-8"))
    con.executescript((AQUI / "esquema_agroversex.sql").read_text(encoding="utf-8"))
