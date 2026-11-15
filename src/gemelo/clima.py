# asistido por SI: Cursor (agente), escritura y revisión de código; núcleo del gemelo digital en el hackatón
# asistido por SI: Claude Code (Opus 5.5), bloque 2: alerta de helada D-032, lluvia alterna IMERG y avisos del suelo calibrado
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

# t2m_min_corr: mínima corregida por altura de Datos (forzantes_gemelo.md §4.3); solo para heladas, no entra en la
# física (la media, la ET0 y la suma térmica siguen con las columnas crudas, de menor sesgo frente a la estación)
VARIABLES = ("precip", "t2m", "t2m_max", "t2m_min", "rh2m", "rad_sw", "ws2m", "t2m_min_corr")
POWER_A_GEMELO = {"PRECTOTCORR": "precip", "T2M": "t2m", "T2M_MAX": "t2m_max", "T2M_MIN": "t2m_min",
                  "RH2M": "rh2m", "ALLSKY_SFC_SW_DWN": "rad_sw", "WS2M": "ws2m", "T2M_MIN_CORR": "t2m_min_corr"}
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
    avisos: list[str] = field(default_factory=list)

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


def con_precip_alterna(clima: ClimaDiario, ruta: str | Path) -> ClimaDiario:
    """Copia de `clima` con la lluvia de IMERG diario de Datos (FECHA_UTC, IMERG_PRECIP_MM_DIA) en lugar de la de
    POWER. Día UTC sin realinear a la hora solar de POWER (desfase de hasta un día, forzantes_gemelo.md §5).
    Solo para la sensibilidad a la fuente de lluvia: el resto de variables queda igual."""
    df = pd.read_csv(Path(ruta), parse_dates=["FECHA_UTC"])
    df = df.rename(columns={"FECHA_UTC": "fecha", "IMERG_PRECIP_MM_DIA": "precip"})[["fecha", "precip"]]
    alt = a_calendario_nominal(df, clima.lat, clima.elevacion_m, f"GPM IMERG Final V07 diario ({Path(ruta).name})",
                               naturaleza="estimado")
    comunes = np.intersect1d(clima.anios, alt.anios)
    if len(comunes) < len(clima.anios):
        raise ValueError(f"lluvia alterna {Path(ruta).name}: faltan años {sorted(set(clima.anios) - set(comunes))}")
    filas = np.searchsorted(alt.anios, clima.anios)
    datos = {**clima.datos, "precip": alt.datos["precip"][filas]}
    huecos = dict(clima.huecos_rellenos)
    if "precip" in alt.huecos_rellenos:
        huecos["precip_alterna"] = alt.huecos_rellenos["precip"]
    return ClimaDiario(clima.anios, datos, clima.lat, clima.elevacion_m, clima.fuente + "; lluvia de " + alt.fuente,
                       huecos, clima.naturaleza, list(clima.avisos))


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


COLUMNAS_MENSUALES = ("precip", "t2m", "t2m_max", "t2m_min", "rh2m", "rad_sw")


def _norm_unidad(u: str) -> str:
    return re.sub(r"\s+", "", str(u or "")).lower().replace("í", "i").replace("°", "").replace("^", "")


def precip_a_mm_mes(valor, unidad: str, dias_mes):
    """Lluvia a mm/mes según la unidad declarada (IMERG Final: mm/hr; Late: mm/day). Sin unidad conocida, error."""
    u = _norm_unidad(unidad)
    if u in ("mm/hr", "mm/h", "mmhr-1", "mmh-1"):
        return valor * 24 * dias_mes
    if u in ("mm/day", "mm/dia", "mm/d", "mmday-1", "mmd-1"):
        return valor * dias_mes
    if u in ("mm/month", "mm/mes", "mm"):
        return valor
    raise ValueError(f"unidad de precipitación desconocida: {unidad!r}")


def _a_unidad_gemelo(var: str, valor, unidad: str):
    u = _norm_unidad(unidad)
    if var.startswith("t2m"):
        if u in ("c", "degc", "celsius"):
            return valor
        if u in ("k", "kelvin"):
            return valor - 273.15
    elif var == "rh2m" and u in ("%", "percent", "porcentaje"):
        return valor
    elif var == "rad_sw":
        if u in ("mj/m2/day", "mj/m2/dia", "mj/m²/day", "mj/m²/dia", "mjm-2day-1", "mjm-2d-1"):
            return valor
        if u in ("w/m2", "w/m²", "wm-2"):
            return valor * 0.0864
    raise ValueError(f"unidad desconocida para {var}: {unidad!r}")


def _serie_mensual(con, unidad_id: str) -> tuple[pd.DataFrame, list[str]]:
    """Tabla larga `serie_mensual` (una fila por unidad, variable y mes) con columnas valor, unidad, nivel y motivo.

    Cada fila se convierte con su propia `unidad`. Si un mes tiene varias filas para la misma variable, gana la que
    no trae `motivo`. Devuelve un DataFrame ancho (mes_id + variables en unidades del gemelo, precip en mm/mes).
    """
    cols = [r[1] for r in con.execute("PRAGMA table_info(serie_mensual)")]
    var = next(c for c in ("variable", "variable_id") if c in cols)
    tiempo = ["mes_id"] if "mes_id" in cols else ["anio", "mes"] if {"anio", "mes"} <= set(cols) else ["periodo"]
    extra = [c for c in ("nivel", "motivo") if c in cols]
    q = f"SELECT {', '.join(tiempo)}, {var}, valor, unidad{''.join(', ' + c for c in extra)} " \
        f"FROM serie_mensual WHERE unidad_id = ?"
    df = pd.DataFrame(con.execute(q, (unidad_id,)).fetchall(), columns=[*tiempo, "variable", "valor", "unidad", *extra])
    if df.empty:
        return df, []
    if tiempo == ["anio", "mes"]:
        df["mes_id"] = (df.anio.astype(int) - 2000) * 12 + df.mes.astype(int) - 1
    elif tiempo == ["periodo"]:
        p = pd.to_datetime(df.periodo.astype(str))
        df["mes_id"] = (p.dt.year - 2000) * 12 + p.dt.month - 1
    df = df[df.variable.isin(COLUMNAS_MENSUALES) & df.valor.notna()].copy()
    for c in ("nivel", "motivo"):
        if c not in df:
            df[c] = None
    df["con_motivo"] = df.motivo.notna() & (df.motivo.astype(str).str.strip() != "")
    df = df.sort_values(["mes_id", "variable", "con_motivo"], kind="stable").drop_duplicates(["mes_id", "variable"])
    dias = DIAS_MES[(df.mes_id % 12).to_numpy()]
    df["valor"] = [precip_a_mm_mes(v, u, d) if x == "precip" else _a_unidad_gemelo(x, v, u)
                   for x, v, u, d in zip(df.variable, df.valor.astype(float), df.unidad, dias)]
    avisos = []
    marcados = df[df.con_motivo]
    if len(marcados):
        motivos = ", ".join(sorted(set(marcados.motivo.astype(str))))
        avisos.append(f"Tabla serie_mensual: {len(marcados)} valores mensuales con motivo ({motivos})")
    niveles = sorted(set(df.nivel.dropna().astype(str)))
    if niveles:
        unidades = ", ".join(sorted(set(df[df.variable == "precip"].unidad.astype(str))))
        avisos.append(f"Tabla serie_mensual: niveles {', '.join(niveles)}; lluvia leída en {unidades or '-'}")
    ancho = df.pivot(index="mes_id", columns="variable", values="valor").reset_index()
    return ancho, avisos


def mensual_desde_sqlite(ruta: str | Path, unidad_id: str
                         ) -> tuple[dict[str, np.ndarray], np.ndarray, float, list[str]]:
    """Lee el clima mensual de agroversex.sqlite (rama datos).

    Con la tabla `serie_mensual` cada valor se convierte con su columna `unidad` (no se supone ninguna). Sin ella, se
    usa la tabla `mensual`, desescalada con `variable`, con precip en mm/h. La lluvia sale en mm/mes.
    Devuelve (mensual, años, lat, avisos). Solo años con los 12 meses de precipitación y temperatura.
    """
    con = sqlite3.connect(str(ruta))
    try:
        tablas = {r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type = 'table'")}
        lat = con.execute("SELECT punto_lat FROM unidad WHERE id = ?", (unidad_id,)).fetchone() \
            if "unidad" in tablas else None
        if "serie_mensual" in tablas:
            df, avisos = _serie_mensual(con, unidad_id)
            if not df.empty:
                return (*_completar_anios(df, [c for c in COLUMNAS_MENSUALES if c in df]),
                        float(lat[0]) if lat else 0.0, avisos)
        escalas = {r[0]: (r[1], r[2] or 0.0) for r in con.execute("SELECT id, escala, desplazamiento FROM variable")}
        cols = list(COLUMNAS_MENSUALES)
        filas = con.execute(f"SELECT mes_id, {', '.join(cols)} FROM mensual WHERE unidad_id = ? ORDER BY mes_id",
                            (unidad_id,)).fetchall()
    finally:
        con.close()
    if not filas:
        raise ValueError(f"sin filas mensuales para {unidad_id}")
    df = pd.DataFrame(filas, columns=["mes_id", *cols])
    for c in cols:
        e, d = escalas.get(c, (1.0, 0.0))
        df[c] = df[c].astype(float) * e + d
    df["precip"] = precip_a_mm_mes(df.precip, "mm/hr", DIAS_MES[(df.mes_id % 12).to_numpy()])
    return (*_completar_anios(df, cols), float(lat[0]) if lat else 0.0, [])


def _completar_anios(df: pd.DataFrame, cols: list[str]) -> tuple[dict[str, np.ndarray], np.ndarray]:
    df = df.copy()
    df["anio"] = 2000 + df.mes_id // 12
    req = [c for c in ("precip", "t2m_max", "t2m_min") if c in df]
    if len(req) < 3:
        raise ValueError("clima mensual: faltan precip, t2m_max o t2m_min")
    completos = [a for a, g in df.groupby("anio") if len(g) == 12 and g[req].notna().all().all()]
    df = df[df.anio.isin(completos)].sort_values("mes_id")
    if not completos:
        raise ValueError("clima mensual: ningún año con los 12 meses completos")
    return {c: df[c].to_numpy(float).reshape(len(completos), 12) for c in cols if df[c].notna().all()}, \
        np.array(completos)
