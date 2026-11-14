# asistido por SI: Claude Code (Anthropic), escritura y revisión de código; base del prototipo migrada en el hackatón
"""Clima mensual sintético: temperatura, lluvia, humedad, radiación y heladas (Task 5).

Estructura: T = clim(mes) + tendencia + forzante ENSO + ruido AR(1); lluvia = clim * factor lognormal
* (1 + ENSO) * eventos. Todo vectorizado por bloque de unidades; el azar sale de rng_unidad por unidad,
así un bloque da lo mismo que la corrida completa.
"""
import os
import sqlite3
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

from simulacion import config
from simulacion.azar import rng_unidad
from simulacion.incertidumbre import banda_p10_p90, err_precip
from simulacion.productos import aplicar_cobertura
from simulacion.referencias import cargar as ref
from simulacion.tiempo import dias_del_mes
from simulacion.variables import B_HUECO, B_PROVISIONAL

N = config.N_MESES
AQUI = Path(__file__).resolve().parent / "referencias"
_MES = np.arange(N) % 12
_DIAS = np.array([dias_del_mes(m) for m in range(N)])

# SUPUESTO (revisión 2026-11-13), sin ficha: constantes del generador
GRADIENTE_C_KM = 6.5       # atmósfera estándar
INTENSIDAD_EVENTO_SD = 2.0  # sequía -2, inundación +2 desviaciones estándar
SIGMA_T = 0.8              # desviación interanual de T mensual, °C (también escala de eventos de calor)
SIGMA_P = 0.35             # sigma del factor lognormal de lluvia (también escala de eventos de lluvia)
PHI_T = 0.5                # autocorrelación mensual de T
SD_DIARIA_TMIN = 2.5       # dispersión diaria de la mínima, °C (conteo de heladas)
SD_DIARIA_T = 4.0          # dispersión diaria de T, °C (días extremos)
Z95 = 1.645
# Coeficiente de lluvia por °C de RONI en las regiones de 2 fuentes: la ficha no trae cifra (coef NULL)
COEF_LLUVIA_DOS_FUENTES = 0.10
# Colombia Caribe y Andina, dos fuentes (EV-ENS-008 IDEAM/PNUD 2014, Bogotá-Cund.: lluvia hasta -60 % y T hasta
# +0,5 °C con El Niño; EV-ENS-015). Las fichas dan el máximo, no el coeficiente: -0,25/°C y +0,20 °C/°C son SUPUESTO
# (RONI máximo ~2,3). Es la única rama con coeficiente propio; el resto usa COEF_LLUVIA_DOS_FUENTES.
COLOMBIA = "Colombia (Caribe y Andina)"
COEF_COLOMBIA = (-0.25, 0.20)


def _leyenda() -> dict[int, str]:
    d = yaml.safe_load((AQUI / "koppen_leyenda.yaml").read_text(encoding="utf-8"))
    return {n: c["codigo"] for n, c in d["clases"].items()}


_COD = _leyenda()
_IDX = {c: i for i, c in enumerate(_COD[n] for n in sorted(_COD))}  # código -> índice 0..29


def _tabla_koppen():
    # SUPUESTO: órdenes de magnitud por clase (no el punto medio de los criterios de Beck 2023, que no tengo transcritos)
    anual = dict(Af=2500, Am=2200, Aw=1100, BWh=100, BWk=150, BSh=350, BSk=400, Csa=600, Csb=800, Csc=900,
                 Cwa=1100, Cwb=1100, Cwc=1000, Cfa=1200, Cfb=1000, Cfc=1100, Dsa=400, Dsb=500, Dsc=550,
                 Dsd=500, Dwa=700, Dwb=650, Dwc=500, Dwd=400, Dfa=800, Dfb=700, Dfc=600, Dfd=450, ET=300, EF=150)
    k = len(_IDX)
    a, s, inv, dtr, cont = (np.zeros(k) for _ in range(5))
    for c, i in _IDX.items():
        a[i] = anual[c]
        s[i] = {"Af": .1, "Am": .5, "Aw": .8}.get(c, .3 if c[0] == "B" else .2 if c[0] == "E" else
                                                  .8 if c[1] in "sw" and c[0] in "CD" and c[2] != "d" else
                                                  .7 if c[1] == "s" else .2)
        inv[i] = len(c) > 1 and c[0] in "CD" and c[1] == "s"  # lluvia de invierno
        dtr[i] = dict(A=8, B=14, C=10, D=11, E=8)[c[0]]
        cont[i] = c[0] == "D"
    return a, s, inv.astype(bool), dtr, cont.astype(bool)


_P_ANUAL, _P_EST, _P_INV, _DTR, _CONT = _tabla_koppen()


def _clase_respaldo(tm, lat):
    # Respaldo, sin Köppen (SUPUESTO): por temperatura media y latitud
    cod = np.select([tm < -10, tm < 0, tm < 10, (tm >= 18) & (np.abs(lat) < 23.5), tm >= 18, tm >= 10],
                    ["EF", "ET", "Dfc", "Aw", "Cfa", "Cfb"], "Cfb")
    return np.array([_IDX[c] for c in cod])


def _t_anual(lat, elev):
    # SUPUESTO: parábola en latitud (no calibrada con los 22 sitios de POWER) y gradiente vertical
    return 28.0 - 0.0068 * lat**2 - GRADIENTE_C_KM * elev / 1000.0


def _clim(lat, elev, cls):
    """Vectorizada: devuelve t_media (n,12), precip (n,12), dtr (n,), respaldo (n,)."""
    lat, elev = np.asarray(lat, float), np.nan_to_num(np.asarray(elev, float))
    cls = np.asarray(cls, int)
    t0 = _t_anual(lat, elev)
    resp = cls < 0
    cls = np.where(resp, _clase_respaldo(t0, lat), cls)
    amp = np.minimum(0.3 * np.abs(lat), 22.0) * np.where(_CONT[cls], 1.25, 1.0)
    pico_t = np.where(lat >= 0, 6, 0)[:, None]
    m = np.arange(12)[None, :]
    t = t0[:, None] + amp[:, None] * np.cos(2 * np.pi * (m - pico_t) / 12)
    # pico de lluvia: verano del hemisferio, o invierno en las clases de verano seco
    pico_p = np.where(_P_INV[cls], (pico_t[:, 0] + 6) % 12, pico_t[:, 0])[:, None]
    p = _P_ANUAL[cls][:, None] / 12 * (1 + _P_EST[cls][:, None] * np.cos(2 * np.pi * (m - pico_p) / 12))
    return t, p, _DTR[cls], resp


# --- normales WorldClim 2.1 (1970-2000) por unidad ---

# INFERENCIA: las normales están centradas en ~1985 y la serie arranca en 2000; la climatología se lleva a la
# línea base sumando la tendencia de la unidad por 15 años (1,5 décadas). La lluvia y la radiación no se desplazan.
DECADAS_NORMAL_A_BASE = 1.5
_VARS_NORMAL = ("tavg", "tmin", "tmax", "prec", "srad")


def cargar_normales(ruta=None) -> pd.DataFrame | None:
    """Tabla clim_normal (unidad_id, mes 1..12, tavg, tmin, tmax, prec, srad). Ruta: argumento, AGROVERSEX_CLIM_NORMAL o
    procesados/clim_normal.sqlite. Sin archivo devuelve None y todas las unidades usan la fórmula de respaldo."""
    r = Path(ruta or os.environ.get("AGROVERSEX_CLIM_NORMAL") or config.PROCESADOS / "clim_normal.sqlite")
    if not r.exists():
        return None
    con = sqlite3.connect(f"file:{r.as_posix()}?mode=ro", uri=True)
    try:
        return pd.read_sql("SELECT unidad_id, mes, tavg, tmin, tmax, prec, srad FROM clim_normal", con)
    finally:
        con.close()


def _matrices_normales(nor: pd.DataFrame, ids) -> tuple[dict, np.ndarray]:
    """(variable -> (n,12) con NaN donde falta, tiene (n,) bool: unidad con las 5 variables en los 12 meses)."""
    f = nor.set_index(["unidad_id", "mes"])
    mat = {v: f[v].unstack("mes").reindex(index=list(ids), columns=range(1, 13)).to_numpy(float)
           for v in _VARS_NORMAL}
    tiene = np.all([np.isfinite(m).all(1) for m in mat.values()], axis=0)
    return mat, tiene


def contar_sin_normales(c) -> int:
    return int(np.sum(c.sin_normales))


def climatologia_unidad(punto_lat, elev_media, koppen_moda) -> dict:
    cls = -1 if koppen_moda is None or pd.isna(koppen_moda) else int(koppen_moda)
    t, p, dtr, resp = _clim([punto_lat], [elev_media], [cls])
    return {"t_media": t[0], "precip": p[0], "amplitud_diaria": float(dtr[0]), "respaldo": bool(resp[0])}


# --- tendencia y ENSO ---

_REGION = yaml.safe_load((AQUI / "iso3_a_region.yaml").read_text(encoding="utf-8"))["paises"]


def tendencia_unidad(iso3: str) -> float:
    # °C/década. Berkeley 2000-2020 por región (INFERENCIA); extendida a 2021-2026 con la misma tasa (SUPUESTO, §5.3).
    # Sin región: tendencia global de estaciones GISTEMP, porque el repositorio no trae bandas zonales (PENDIENTE)
    reg = (_REGION.get(iso3) or {}).get("berkeley")
    tasas = ref.cargar_berkeley()
    return float(tasas[reg]) if reg in tasas else float(ref.cargar_gistemp_tendencia()["valor"])


def forzante_enso(macroregion: str, roni: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """(anomalía fraccional de lluvia, anomalía de T en °C). Ceros fuera de las regiones con dos fuentes. Si la
    fuente solo cubre El Niño (nina_aplica falso), La Niña no tiene efecto."""
    r = np.nan_to_num(np.asarray(roni, float))
    tc = ref.cargar_teleconexiones()
    fila = tc[tc.macroregion == macroregion]
    if fila.empty:
        return np.zeros_like(r), np.zeros_like(r)
    fila = fila.iloc[0]
    if not fila.nina_aplica:
        r = np.maximum(r, 0.0)
    if macroregion == COLOMBIA:
        return COEF_COLOMBIA[0] * r, COEF_COLOMBIA[1] * r
    signo = -1.0 if fila.signo_nino.startswith("menos") else 1.0
    if fila.temporada == "DJF":  # solo dic-ene-feb, como dice la fuente
        r = r * np.isin(_MES[:len(r)] + 1, (12, 1, 2))
    return signo * COEF_LLUVIA_DOS_FUENTES * r, np.zeros_like(r)


_ADM1_ENSO = yaml.safe_load((AQUI / "iso3_a_region.yaml").read_text(encoding="utf-8"))


def _enso_por_adm1(reg, iso3, adm1):
    """Regiones ENSO acotadas por ADM1 y exclusiones (Colombia Pacífica); sin ADM1 la unidad no entra."""
    if adm1 is None:
        return reg
    reg = reg.copy()
    for region, paises in _ADM1_ENSO["enso_adm1"].items():
        for iso, lista in paises.items():
            reg[(iso3 == iso) & np.isin(adm1, lista)] = region
    for iso, lista in _ADM1_ENSO["enso_excluye_adm1"].items():
        reg[(iso3 == iso) & np.isin(adm1, lista)] = None
    return reg


# --- eventos ---

_EV_ISO3 = yaml.safe_load((AQUI / "eventos_iso3.yaml").read_text(encoding="utf-8"))["eventos"]


# ev07 (Australia 2019, "+1,52 °C" nacional, INV-CLI §4): la evidencia no nombra región y la tasa de Berkeley
# 2000-2020 (0,381 °C/década) ya incluye ese año; aplicarlo sumaba +0,071 °C/década (> 0,06, Task 12).
# SUPUESTO (rev. 2026-11-13): se mantiene el déficit de lluvia y se desactiva el pulso térmico nacional.
SIN_EFECTO_T = frozenset({"ev07"})


def _efecto_evento(tipo: str) -> tuple[float, float]:
    # (signo en lluvia, signo en temperatura) según el texto del tipo
    t = tipo.lower()
    lluvia = -1 if "sequía" in t else 1 if ("inundación" in t or "ciclón" in t) else 0
    temp = 1 if "calor" in t else -1 if "helada" in t else 0
    return lluvia, temp


def imprimir_eventos(precip, t2m, unidad_ids, eventos, iso3=None, adm1=None) -> None:
    """Aplica en el sitio la anomalía de cada evento FUENTE a las unidades de sus países (todos los meses de sus años)."""
    if iso3 is None:
        g = cargar_geo().reindex(list(unidad_ids))
        iso3, adm1 = g.iso3.to_numpy(), g.adm1.to_numpy()
    iso3 = np.asarray(iso3)
    adm1 = np.full(len(iso3), None, object) if adm1 is None else np.asarray(adm1, object)
    for e in eventos:
        paises = _EV_ISO3.get(e["id"])
        if not paises:
            continue
        if isinstance(paises, dict):  # país: lista de ADM1; la unidad nacional (sin ADM1) no entra
            filas = np.zeros(len(iso3), bool)
            for iso, lista in paises.items():
                filas |= (iso3 == iso) & np.isin(adm1, lista)
        else:
            filas = np.isin(iso3, paises)
        sl = slice(max((e["inicio"] - 2000) * 12, 0), min((e["fin"] - 2000) * 12 + 12, N))
        sl_p, sl_t = _efecto_evento(e["tipo"])
        if filas.any() and sl_p:
            precip[filas, sl] *= np.exp(sl_p * INTENSIDAD_EVENTO_SD * SIGMA_P)
        if filas.any() and sl_t and e["id"] not in SIN_EFECTO_T:
            t2m[filas, sl] += sl_t * INTENSIDAD_EVENTO_SD * SIGMA_T


# --- datos de las unidades ---


def cargar_geo(ruta=None) -> pd.DataFrame:
    """Índice id; columnas iso3, punto_lat, elev_media, koppen (clase moda 1..30, -1 sin Köppen).

    Solo lectura. Ruta: argumento, o AGROVERSEX_GEO_SQLITE, o config.GEO_SQLITE; si no tiene clase_fraccion, el respaldo.
    """
    ruta = Path(ruta or os.environ.get("AGROVERSEX_GEO_SQLITE") or config.GEO_SQLITE)
    candidatas = [ruta, ruta.with_name(ruta.name + ".bak_prereconstruccion")]
    for r in candidatas:
        try:
            con = sqlite3.connect(f"file:{r.as_posix()}?mode=ro", uri=True)
            try:
                kop = pd.read_sql("SELECT unidad_id, clase, fraccion FROM clase_fraccion WHERE esquema='koppen'", con)
                if kop.empty:
                    continue
                u = pd.read_sql("SELECT id, nivel, iso3, padre_id, nombre, punto_lat, punto_lon FROM unidad", con)
                el = pd.read_sql("SELECT unidad_id AS id, media AS elev_media FROM estatico "
                                 "WHERE variable_id='elev_media'", con)
            finally:
                con.close()
        except sqlite3.Error:
            continue
        moda = kop.sort_values("fraccion").groupby("unidad_id").clase.last().astype(int)
        # ADM1 de cada unidad: ella misma en nivel 1, su padre en nivel 2, nada en nivel 0
        n1 = u[u.nivel == 1].set_index("id").nombre
        u["adm1"] = np.where(u.nivel == 1, u.nombre, u.padre_id.map(n1))
        df = u.merge(el, on="id", how="left").set_index("id")[["iso3", "punto_lat", "punto_lon", "adm1", "elev_media"]]
        df["koppen"] = moda.reindex(df.index).fillna(-1).astype(int)
        return df
    raise FileNotFoundError(f"sin geo.sqlite utilizable en {ruta} ni su respaldo")


# --- generador ---


@dataclass
class Clima:
    precip: np.ndarray
    precip_err: np.ndarray
    precip_frac: np.ndarray
    t2m: np.ndarray
    t2m_p10: np.ndarray
    t2m_p90: np.ndarray
    t2m_max: np.ndarray
    t2m_min: np.ndarray
    rh2m: np.ndarray
    rad_sw: np.ndarray
    dias_helada: np.ndarray
    dias_extremo: np.ndarray
    bandera: np.ndarray
    # Metadatos por unidad (no van al bitmask)
    sin_koppen: np.ndarray        # respaldo por latitud y elevación
    enso_no_documentado: np.ndarray  # B_ENSO_NO_DOCUMENTADO: sin teleconexión documentada
    sin_normales: np.ndarray      # climatología de respaldo (fórmula) por falta de normales WorldClim


def _phi(x):
    # Normal estándar; erf de Abramowitz-Stegun 7.1.26 (error < 1,5e-7). No hay scipy en el venv
    z = np.abs(x) / np.sqrt(2)
    t = 1 / (1 + 0.3275911 * z)
    erf = 1 - (((((1.061405429 * t - 1.453152027) * t) + 1.421413741) * t - 0.284496736) * t + 0.254829592) * t * np.exp(-z * z)
    return 0.5 * (1 + np.sign(x) * erf)


def _conteo(dias, p, z):
    # Binomial por aproximación normal (shortcut: sin cola exacta en p muy chico)
    return np.clip(np.rint(dias * p + np.sqrt(dias * p * (1 - p)) * z), 0, dias)


def _rad_extraterrestre(lat):
    # FAO-56 ec. 21, día medio de cada mes; MJ/m²/día, (n,12)
    j = np.array([15, 46, 74, 105, 135, 166, 196, 227, 258, 288, 319, 349])[None, :]
    phi = np.radians(lat)[:, None]
    dr = 1 + 0.033 * np.cos(2 * np.pi * j / 365)
    dec = 0.409 * np.sin(2 * np.pi * j / 365 - 1.39)
    ws = np.arccos(np.clip(-np.tan(phi) * np.tan(dec), -1, 1))
    return 37.586 * dr * (ws * np.sin(phi) * np.sin(dec) + np.cos(phi) * np.cos(dec) * np.sin(ws))


def generar_clima(unidad_ids: list[str], bloque: slice, geo: pd.DataFrame | None = None,
                  normales: pd.DataFrame | None = None) -> Clima:
    ids = list(unidad_ids)[bloque]
    n = len(ids)
    g = (geo if geo is not None else cargar_geo()).reindex(ids)
    lat, iso3 = g.punto_lat.to_numpy(float), g.iso3.to_numpy()
    adm1 = g["adm1"].to_numpy(object) if "adm1" in g else None
    cls = g.koppen.fillna(-1).to_numpy(int) - 1  # 1..30 -> índice 0..29; -1 sin Köppen queda en -2
    cls = np.where(cls < 0, -1, cls)
    t_cl, p_cl, dtr, resp = _clim(lat, g.elev_media.to_numpy(float), cls)
    dtr = np.repeat(dtr[:, None], 12, 1)

    # Azar por unidad (un solo tirón de 4 filas); el resto es vectorizado
    z = np.stack([rng_unidad(u, "clima").standard_normal((4, N)) for u in ids]) if n else np.zeros((0, 4, N))
    ar = np.empty((n, N))
    ar[:, 0] = SIGMA_T * z[:, 0, 0]
    for t in range(1, N):  # AR(1): bucle sobre el tiempo, vectorizado entre unidades
        ar[:, t] = PHI_T * ar[:, t - 1] + np.sqrt(1 - PHI_T**2) * SIGMA_T * z[:, 0, t]

    # ENSO: forzante por macrorregión; el resto de las unidades no lleva teleconexión
    roni = np.nan_to_num(ref.cargar_enso().roni.to_numpy())
    # El ENSO aporta variabilidad, no tendencia: la de Berkeley ya incluye los El Niño del periodo
    roni = roni - np.polyval(np.polyfit(np.arange(N), roni, 1), np.arange(N))
    a_p, a_t = np.zeros((n, N)), np.zeros((n, N))
    reg = np.array([(_REGION.get(i) or {}).get("enso") for i in iso3], dtype=object)
    reg = _enso_por_adm1(reg, iso3, adm1)
    for r in {x for x in reg if x}:
        f = reg == r
        a_p[f], a_t[f] = forzante_enso(r, roni)
    sin_enso = np.array([x is None for x in reg])

    tend = np.array([tendencia_unidad(i) for i in sorted(set(iso3))])
    tend = tend[np.searchsorted(sorted(set(iso3)), iso3)] if n else tend
    # Normales WorldClim donde existen; el resto queda con la fórmula (sin_normales)
    nor = normales if normales is not None else cargar_normales()
    tiene = np.zeros(n, bool)
    srad = None
    if nor is not None and n:
        mat, tiene = _matrices_normales(nor, ids)
        t_cl[tiene] = mat["tavg"][tiene] + tend[tiene, None] * DECADAS_NORMAL_A_BASE
        p_cl[tiene] = mat["prec"][tiene]
        dtr[tiene] = (mat["tmax"] - mat["tmin"])[tiene]
        srad = mat["srad"] / 1000.0  # kJ/m²/día a MJ/m²/día
    clim_t = t_cl[:, _MES]
    t2m =clim_t + tend[:, None] * (np.arange(N) / 120.0)[None, :] + a_t + ar
    precip = p_cl[:, _MES] * np.exp(SIGMA_P * z[:, 1] - SIGMA_P**2 / 2) * np.maximum(1 + a_p, 0.05)
    imprimir_eventos(precip, t2m, ids, ref.cargar_eventos(), iso3=iso3, adm1=adm1)
    precip = np.maximum(precip, 0.0)

    # Derivadas
    dtr_t = dtr[:, _MES]
    t_max, t_min = t2m + dtr_t / 2, t2m - dtr_t / 2
    t_p10, t_p90 = banda_p10_p90(t2m, SIGMA_T)
    rh = np.clip(30 + 55 * (1 - np.exp(-precip / 120)), 10, 98)  # SUPUESTO: humedad por lluvia (rev. 2026-11-13)
    ra = _rad_extraterrestre(lat)[:, _MES]
    def f_nub(p):  # SUPUESTO: nubosidad por lluvia (0,75, 0,4, 300 mm; rev. 2026-11-13)
        return 0.75 - 0.4 * np.clip(p / 300, 0, 1)
    rad = ra * f_nub(precip)
    if srad is not None:  # normal de radiación, modulada por la lluvia del mes respecto de su normal
        rad = np.where(tiene[:, None], srad[:, _MES] * f_nub(precip) / f_nub(p_cl[:, _MES]), rad)
    rad = np.clip(rad, 0, 35)
    helada = np.rint(_DIAS * _phi(-t_min / SD_DIARIA_TMIN))
    desv = t2m - clim_t
    desv = desv - desv[:, :192].mean(1, keepdims=True)  # base 2000-2015: p95 diario (INICIAR §5.5)
    extremo = _conteo(_DIAS, 1 - _phi(Z95 - desv / SD_DIARIA_T), z[:, 3])

    # Cobertura: IMERG para lluvia, POWER para meteorología. Mes parcial: suma solo de los días cubiertos
    precip, frac, b_imerg = aplicar_cobertura(precip, "imerg")
    precip = precip * frac
    bandera = np.broadcast_to(b_imerg, (n, N)).copy()
    err = np.where((bandera & B_PROVISIONAL) > 0, err_precip(precip, frac, True), err_precip(precip, frac, False))
    campos = []
    for a in (t2m, t_p10, t_p90, t_max, t_min, rh, rad, helada, extremo):
        v, fp, b = aplicar_cobertura(a, "power")
        campos.append(v)
        bandera |= b | np.where((fp > 0) & (fp < 1), B_HUECO, 0)  # mes parcial de POWER (nov-2026, hasta el día 5)
    t2m, t_p10, t_p90, t_max, t_min, rh, rad, helada, extremo = campos
    return Clima(precip, err, np.broadcast_to(frac, (n, N)).copy(), t2m, t_p10, t_p90, t_max, t_min, rh, rad,
                 helada, extremo, bandera, resp, sin_enso, ~tiene)
