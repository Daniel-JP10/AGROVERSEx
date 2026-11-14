# asistido por SI: Cursor (agente), escritura y revisión de código; núcleo del gemelo digital en el hackatón
"""Forzamiento ambiental e(t): lectura de NASA POWER, calendario nominal, ET0 FAO-56 y desagregación mensual a diaria.

Unidades: precip mm/día; temperaturas °C; rh2m %; rad_sw MJ/m²/día; ws2m m/s; et0 mm/día.
Calendario nominal: años de 365 días (se descarta el 29 de febrero) para que una fecha de siembra signifique lo
mismo en todos los años del ensamble. Día t = 365 * año + (día del año - 1).
"""
import re
import sqlite3
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import pandas as pd

VARIABLES = ("precip", "t2m", "t2m_max", "t2m_min", "rh2m", "rad_sw", "ws2m")
POWER_A_GEMELO = {"PRECTOTCORR": "precip", "T2M": "t2m", "T2M_MAX": "t2m_max", "T2M_MIN": "t2m_min",
                  "RH2M": "rh2m", "ALLSKY_SFC_SW_DWN": "rad_sw", "WS2M": "ws2m"}
DIAS_MES = np.array([31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31])
INICIO_MES = np.concatenate([[0], np.cumsum(DIAS_MES)[:-1]])
MES_DE_DIA = np.repeat(np.arange(12), DIAS_MES)  # mes (0-11) de cada día nominal 0-364
SIGMA = 4.903e-9  # MJ K^-4 m^-2 día^-1 (FAO-56 ec. 39)
GSC = 0.0820      # MJ m^-2 min^-1 (FAO-56 ec. 21)


@dataclass
class ClimaDiario:
    """Serie diaria por años nominales: cada variable es un arreglo (n_anios, 365)."""
    anios: np.ndarray
    datos: dict[str, np.ndarray]
    lat: float
    elevacion_m: float
    fuente: str
    huecos_rellenos: dict[str, int] = field(default_factory=dict)
    naturaleza: str = "observado"

    @property
    def n_anios(self) -> int:
        return len(self.anios)

    def precip_anual(self) -> np.ndarray:
        return self.datos["precip"].sum(axis=1)

    def resumen(self) -> dict:
        p = self.precip_anual()
        return {"fuente": self.fuente, "anios": [int(self.anios[0]), int(self.anios[-1])], "lat": self.lat,
                "elevacion_m": self.elevacion_m, "naturaleza": self.naturaleza,
                "precip_anual_media_mm": float(p.mean()), "precip_anual_p10_p90_mm": [float(np.percentile(p, 10)),
                                                                                   float(np.percentile(p, 90))],
                "t2m_media_c": float(self.datos["t2m"].mean()), "huecos_rellenos": self.huecos_rellenos}


# ------------------------------------------------------------------------------------------------ lectura

def leer_power_csv(ruta: str | Path) -> tuple[pd.DataFrame, dict]:
    """CSV diario de la API de NASA POWER (comunidad AG). Devuelve DataFrame con fecha y metadatos del encabezado."""
    texto = Path(ruta).read_text(encoding="utf-8")
    fin = texto.index("-END HEADER-")
    encabezado = texto[:fin]
    meta = {"fuente": f"NASA POWER diario ({Path(ruta).name})"}
    m = re.search(r"latitude\s+(-?[\d.]+)\s+longitude\s+(-?[\d.]+)", encabezado)
    if m:
        meta["lat"], meta["lon"] = float(m.group(1)), float(m.group(2))
    m = re.search(r"=\s*(-?[\d.]+)\s*meters", encabezado)
    meta["elevacion_m"] = float(m.group(1)) if m else 0.0
    df = pd.read_csv(Path(ruta), skiprows=encabezado.count("\n") + 1)
    df = df.replace(-999.0, np.nan)
    df["fecha"] = pd.to_datetime(df["YEAR"].astype(str), format="%Y") + pd.to_timedelta(df["DOY"] - 1, unit="D")
    df = df.rename(columns=POWER_A_GEMELO)
    return df[["fecha", *[v for v in VARIABLES if v in df.columns]]], meta


def a_calendario_nominal(df: pd.DataFrame, lat: float, elevacion_m: float, fuente: str,
                         naturaleza: str = "observado") -> ClimaDiario:
    """Quita el 29 de febrero, exige años completos y rellena huecos cortos por interpolación (contados)."""
    df = df[~((df.fecha.dt.month == 2) & (df.fecha.dt.day == 29))].copy()
    df["anio"] = df.fecha.dt.year
    cuenta = df.groupby("anio").size()
    completos = cuenta[cuenta == 365].index.to_numpy()
    if len(completos) == 0:
        raise ValueError("no hay ningún año completo en la serie diaria")
    df = df[df.anio.isin(completos)].sort_values("fecha")
    datos, huecos = {}, {}
    for v in VARIABLES:
        if v not in df.columns:
            continue
        s = df[v].astype(float)
        n = int(s.isna().sum())
        if n:
            s = s.interpolate(limit=5, limit_direction="both")
            if s.isna().any():
                raise ValueError(f"{v}: huecos de más de 5 días; no se rellenan")
            huecos[v] = n
        datos[v] = s.to_numpy().reshape(len(completos), 365)
    return ClimaDiario(completos, datos, lat, elevacion_m, fuente, huecos, naturaleza)


def cargar_power(ruta: str | Path) -> ClimaDiario:
    """NASA POWER es reanálisis (MERRA-2) más CERES: se marca 'estimado', no 'observado'."""
    df, meta = leer_power_csv(ruta)
    return a_calendario_nominal(df, meta.get("lat", 0.0), meta["elevacion_m"],
                                meta["fuente"] + "; MERRA-2 y CERES, celda 0,5° x 0,625°", naturaleza="estimado")


def cargar_forzantes(ruta: str | Path, lat: float, elevacion_m: float) -> ClimaDiario:
    """Forzantes diarios de Datos (T-D5, contratos/forzantes_gemelo.md): columna `fecha` (AAAA-MM-DD) y las
    variables del gemelo en sus unidades (precip mm/día, t2m/t2m_max/t2m_min °C, rh2m %, rad_sw MJ/m²/día,
    ws2m m/s). CSV o Parquet. Son productos satelitales y de reanálisis: naturaleza 'estimado'."""
    ruta = Path(ruta)
    df = pd.read_parquet(ruta) if ruta.suffix == ".parquet" else pd.read_csv(ruta)
    if "fecha" not in df.columns:
        raise ValueError(f"forzantes {ruta.name}: falta la columna fecha")
    faltan = [v for v in ("precip", "rad_sw") if v not in df.columns]
    if faltan or not ({"t2m"} <= set(df.columns) or {"t2m_max", "t2m_min"} <= set(df.columns)):
        raise ValueError(f"forzantes {ruta.name}: faltan columnas {faltan or ['t2m o t2m_max y t2m_min']}")
    df["fecha"] = pd.to_datetime(df["fecha"])
    return a_calendario_nominal(df[["fecha", *[v for v in VARIABLES if v in df.columns]]], float(lat),
                                float(elevacion_m), f"forzantes diarios de Datos ({ruta.name})",
                                naturaleza="estimado")


# ------------------------------------------------------------------------------------- FAO-56: radiación y ET0

def radiacion_extraterrestre(lat_grados, doy):
    """Ra en MJ/m²/día (FAO-56 ec. 21-25)."""
    phi = np.deg2rad(lat_grados)
    j = np.asarray(doy, float)
    dr = 1 + 0.033 * np.cos(2 * np.pi * j / 365)
    delta = 0.409 * np.sin(2 * np.pi * j / 365 - 1.39)
    ws = np.arccos(np.clip(-np.tan(phi) * np.tan(delta), -1, 1))
    return 24 * 60 / np.pi * GSC * dr * (ws * np.sin(phi) * np.sin(delta) + np.cos(phi) * np.cos(delta) * np.sin(ws))


def presion_saturacion(t):
    """e°(T) en kPa (FAO-56 ec. 11)."""
    return 0.6108 * np.exp(17.27 * t / (t + 237.3))


def eto_penman_monteith(tmax, tmin, rs, lat, doy, elevacion_m, rh=None, u2=2.0, ea=None, albedo=0.23):
    """ET0 FAO Penman-Monteith diaria (FAO-56 ec. 6), mm/día. ea en kPa; si falta, se usa rh media (ec. 19)."""
    tmax, tmin, rs = (np.asarray(x, float) for x in (tmax, tmin, rs))
    tmed = (tmax + tmin) / 2
    p = 101.3 * ((293 - 0.0065 * elevacion_m) / 293) ** 5.26               # ec. 7
    gamma = 0.665e-3 * p                                                   # ec. 8
    delta = 4098 * presion_saturacion(tmed) / (tmed + 237.3) ** 2          # ec. 13
    es = (presion_saturacion(tmax) + presion_saturacion(tmin)) / 2         # ec. 12
    if ea is None:
        ea = np.asarray(rh, float) / 100 * es                               # ec. 19 (RH media)
    ra = radiacion_extraterrestre(lat, doy)
    rso = (0.75 + 2e-5 * elevacion_m) * ra                                  # ec. 37
    rns = (1 - albedo) * rs                                                 # ec. 38
    rel = np.minimum(rs / np.maximum(rso, 1e-6), 1.0)                     # Rs/Rso <= 1 (ec. 39)
    rnl = SIGMA * ((tmax + 273.16) ** 4 + (tmin + 273.16) ** 4) / 2 * (0.34 - 0.14 * np.sqrt(np.maximum(ea, 0))) \
        * (1.35 * rel - 0.35)                                               # ec. 39
    rn = rns - rnl
    num = 0.408 * delta * rn + gamma * 900 / (tmed + 273) * u2 * (es - ea)
    return np.maximum(num / (delta + gamma * (1 + 0.34 * u2)), 0.0)


def eto_hargreaves(tmax, tmin, tmed, lat, doy):
    """ET0 de Hargreaves-Samani (FAO-56 ec. 52), mm/día. Respaldo cuando falta radiación, humedad o viento."""
    ra = radiacion_extraterrestre(lat, doy) * 0.408
    return np.maximum(0.0023 * (np.asarray(tmed) + 17.8) * np.sqrt(np.maximum(np.asarray(tmax) - tmin, 0)) * ra, 0)


def calcular_eto(datos: dict, lat: float, elevacion_m: float, viento_respaldo: float = 2.0) -> tuple[np.ndarray, str]:
    """ET0 (…, 365) y el método usado. Penman-Monteith si hay radiación y humedad; si no, Hargreaves."""
    doy = np.arange(1, 366)
    shape = datos["t2m_max"].shape
    doy = np.broadcast_to(doy, shape)
    if "rad_sw" in datos and "rh2m" in datos:
        u2 = datos.get("ws2m", np.full(shape, viento_respaldo))
        metodo = "penman_monteith_fao56" + ("" if "ws2m" in datos else "_viento_2ms")
        return eto_penman_monteith(datos["t2m_max"], datos["t2m_min"], datos["rad_sw"], lat, doy, elevacion_m,
                                   rh=datos["rh2m"], u2=u2), metodo
    tmed = datos.get("t2m", (datos["t2m_max"] + datos["t2m_min"]) / 2)
    return eto_hargreaves(datos["t2m_max"], datos["t2m_min"], tmed, lat, doy), "hargreaves_samani_fao56"


# --------------------------------------------------------------------------------- desagregación mensual

LLUVIA_POR_DIA_HUMEDO_MM = 10.0  # SUPUESTO: lluvia media por día húmedo para estimar el número de días de lluvia


def _interpolar_mensual(mensual: np.ndarray) -> np.ndarray:
    """Valores medios mensuales (n_anios, 12) -> diarios (n_anios, 365), anclados a mitad de mes, lineal."""
    n = mensual.shape[0]
    plano = mensual.reshape(-1)
    centros = (np.arange(n)[:, None] * 365 + INICIO_MES[None, :] + DIAS_MES[None, :] / 2.0).reshape(-1)
    dias = np.arange(n * 365) + 0.5
    return np.interp(dias, centros, plano).reshape(n, 365)


def desagregar_mensual(mensual: dict[str, np.ndarray], anios, lat: float, elevacion_m: float, semilla: int,
                       dias_lluvia: np.ndarray | None = None, fuente: str = "mensual") -> ClimaDiario:
    """Clima mensual (n_anios, 12) -> diario conservando exactamente la lluvia mensual.

    precip en mm/mes; el resto como media mensual. La lluvia se reparte en n días húmedos elegidos al azar (con
    semilla) y montos exponenciales normalizados al total del mes. Sin `dias_lluvia`, n = ceil(P / 10 mm) (SUPUESTO).
    """
    rng = np.random.default_rng(semilla)
    p_m = np.asarray(mensual["precip"], float)
    n_anios = p_m.shape[0]
    precip = np.zeros((n_anios, 365))
    for a in range(n_anios):
        for m in range(12):
            total = p_m[a, m]
            if not np.isfinite(total) or total <= 0:
                continue
            nd = int(DIAS_MES[m])
            n = int(dias_lluvia[a, m]) if dias_lluvia is not None else int(np.ceil(total / LLUVIA_POR_DIA_HUMEDO_MM))
            n = min(max(n, 1), nd)
            dias = rng.choice(nd, size=n, replace=False)
            montos = rng.exponential(1.0, size=n)
            precip[a, INICIO_MES[m] + dias] = total * montos / montos.sum()
    datos = {"precip": precip}
    for v in VARIABLES[1:]:
        if v in mensual:
            datos[v] = _interpolar_mensual(np.asarray(mensual[v], float))
    return ClimaDiario(np.asarray(anios), datos, lat, elevacion_m, fuente, naturaleza="derivado")


def mensual_desde_sqlite(ruta: str | Path, unidad_id: str) -> tuple[dict[str, np.ndarray], np.ndarray, float]:
    """Lee la tabla `mensual` de agroversex.sqlite (rama datos) y desescala con la tabla `variable`.

    precip se guarda como tasa media en mm/h: se convierte a mm/mes. Devuelve (mensual, años, lat).
    Solo años con los 12 meses de precipitación y temperatura.
    """
    con = sqlite3.connect(str(ruta))
    try:
        escalas = {r[0]: (r[1], r[2] or 0.0) for r in con.execute("SELECT id, escala, desplazamiento FROM variable")}
        cols = ["precip", "t2m", "t2m_max", "t2m_min", "rh2m", "rad_sw"]
        filas = con.execute(f"SELECT mes_id, {', '.join(cols)} FROM mensual WHERE unidad_id = ? ORDER BY mes_id",
                            (unidad_id,)).fetchall()
        lat = con.execute("SELECT punto_lat FROM unidad WHERE id = ?", (unidad_id,)).fetchone()
    finally:
        con.close()
    if not filas:
        raise ValueError(f"sin filas mensuales para {unidad_id}")
    df = pd.DataFrame(filas, columns=["mes_id", *cols])
    for c in cols:
        e, d = escalas.get(c, (1.0, 0.0))
        df[c] = df[c].astype(float) * e + d
    df["anio"] = 2000 + df.mes_id // 12
    df["mes"] = df.mes_id % 12
    df["precip"] = df.precip * 24 * DIAS_MES[df.mes.to_numpy()]
    completos = [a for a, g in df.groupby("anio") if len(g) == 12 and g[["precip", "t2m_max", "t2m_min"]].notna().all().all()]
    df = df[df.anio.isin(completos)]
    mensual = {c: df[c].to_numpy().reshape(len(completos), 12) for c in cols if df[c].notna().all()}
    return mensual, np.array(completos), float(lat[0]) if lat else 0.0
