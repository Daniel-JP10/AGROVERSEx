# asistido por SI: Claude Code (Anthropic), lectura orientada de los netCDF de T-D3 con puntos de control (T-D2)
"""Lee un campo mensual de los productos de T-D3 y lo deja norte arriba y longitud creciente.

Por qué existe: GDAL invierte sin avisar el primer eje de los netCDF sin georreferencia cuando su
coordenada es creciente (IMERG: dims lon, lat; el eje lon sale espejado). Aquí la orientación no se
supone: se prueban las variantes de volteo y se acepta la única que pasa los puntos de control físicos
(tierra y mar, desiertos y selvas, hemisferios). Si ninguna o varias pasan, se detiene."""
import glob
import itertools
import re
import warnings
from pathlib import Path

import numpy as np

from simulacion.geo.zonal_mensual import Grilla, grilla_desde_centros

warnings.filterwarnings("ignore", message=".*NotGeoreferenced.*")
warnings.filterwarnings("ignore", category=UserWarning, module="rasterio")


def _g(lon0, dlon, nlon, lat0, dlat, nlat):
    return grilla_desde_centros(lon0 + dlon * np.arange(nlon), lat0 + dlat * np.arange(nlat))


# mallas declaradas en las fichas de T-D3 (centros de celda); IMERG y MERRA-2 se contrastan con los ejes del archivo
GRILLAS = {
    "imerg": _g(-179.95, 0.1, 3600, -89.95, 0.1, 1800),
    "merra2": _g(-180.0, 0.625, 576, -90.0, 0.5, 361),
    "gldas": _g(-179.875, 0.25, 1440, -59.875, 0.25, 600),
    "mod13c2": _g(-179.975, 0.05, 7200, -89.975, 0.05, 3600),
}

# puntos de control: (lat, lon, "alto"|"bajo"|"valido"|"invalido", umbral en unidades del producto)
_IMERG = [(5.5, -76.5, "alto", 0.1), (23, 10, "bajo", 0.05), (-0.5, 114, "alto", 0.1), (-3, -60, "alto", 0.05),
          (-24, -69, "bajo", 0.02), (22, 45, "bajo", 0.05), (5, 150, "alto", 0.1), (0, 22, "alto", 0.05)]
_IMERG_DIA = [(5.5, -76.5, "alto", 2.4), (23, 10, "bajo", 1.2), (-0.5, 114, "alto", 2.4), (-3, -60, "alto", 1.2),
              (-24, -69, "bajo", 0.5), (22, 45, "bajo", 1.2), (5, 150, "alto", 2.4), (0, 22, "alto", 1.2)]
_TIERRA = [(-3, -60, "valido", 0), (-25, 135, "valido", 0), (60, 100, "valido", 0), (0, 25, "valido", 0),
           (0, -30, "invalido", 0), (-15, -140, "invalido", 0), (-35, 80, "invalido", 0), (30, -45, "invalido", 0)]
_MOD = [(23, 10, "valido", 0), (22, 78, "valido", 0), (-33, -62, "valido", 0), (-25, 135, "valido", 0),
        (0, -30, "invalido", 0), (-15, -140, "invalido", 0), (-35, 80, "invalido", 0), (30, -45, "invalido", 0)]

PRODUCTOS = {
    "imerg_final": dict(carpeta="imerg_final", grilla="imerg", sub="/Grid/precipitation", relleno=-9999.9004,
                        escala=1.0, controles=_IMERG, unidad="mm/hr"),
    "imerg_late": dict(carpeta="imerg_late", grilla="imerg", sub="precipitation", relleno=-9999.9004,
                       escala=1.0, controles=_IMERG_DIA, unidad="mm/day"),
    "t2m": dict(carpeta="merra2_slv", grilla="merra2", sub="T2M", relleno=9.99999987e14, escala=1.0,
                controles=None, unidad="K"),
    "swgdn": dict(carpeta="merra2_rad", grilla="merra2", sub=None, relleno=9.99999987e14, escala=1.0,
                  controles=None, unidad="W m-2"),
    "humedad_radicular": dict(carpeta="gldas_noah025", grilla="gldas", sub="RootMoist_inst", relleno=-9999.0,
                              escala=1.0, controles=_TIERRA, unidad="kg m-2"),
    "ndvi": dict(carpeta="mod13c2", grilla="mod13c2", relleno=-3000.0, escala=1e-4, controles=_MOD,
                 sub="/MOD_Grid_monthly_CMG_VI/Data_Fields/CMG_0_05_Deg_Monthly_NDVI",
                 rel="/MOD_Grid_monthly_CMG_VI/Data_Fields/CMG_0_05_Deg_Monthly_pixel_reliability",
                 unidad="1"),
}
# pixel_reliability de MOD13C2 que se aceptan: 0 buena y 1 marginal (SUPUESTO; 2 nieve/hielo, 3 nube, 4 estimado y -1 relleno quedan fuera)
FIABLE_ACEPTADA = (0, 1)


def valor_en(a: np.ndarray, g: Grilla, lat: float, lon: float) -> float:
    return a[int((g.y0 - lat) / g.dy), int((lon - g.x0) / g.dx)]


def _cumple(a, g, controles) -> bool:
    for lat, lon, tipo, u in controles:
        v = valor_en(a, g, lat, lon)
        if tipo == "valido" and not np.isfinite(v): return False
        if tipo == "invalido" and np.isfinite(v): return False
        if tipo == "alto" and not (np.isfinite(v) and v > u): return False
        if tipo == "bajo" and not (np.isfinite(v) and v < u): return False
    return True


def _controles_merra(a, g, mes, rad) -> bool:
    # sin máscara de tierra: Tibet frente a su espejo en longitud (T2M) y el contraste de hemisferios de latitudes medias según el mes
    ok = True
    v = lambda la, lo: valor_en(a, g, la, lo)  # noqa: E731
    fn = np.nanmean(a[int((g.y0 - 60) / g.dy):int((g.y0 - 30) / g.dy)])
    fs = np.nanmean(a[int((g.y0 + 30) / g.dy):int((g.y0 + 60) / g.dy)])
    if rad:
        dif = 50  # solo hemisferios: la longitud se hereda de T2M (misma malla y mismo formato), declarado
    else:
        ok &= v(31, 91) < v(31, -91) - 8
        dif = 8
    if mes in (12, 1, 2): ok &= (fs - fn) > dif
    if mes in (6, 7, 8): ok &= (fn - fs) > dif
    return bool(ok)


def _variantes(raw: np.ndarray, g: Grilla):
    for tr, fy, fx in itertools.product((False, True), repeat=3):
        a = raw.T if tr else raw
        if a.shape != (g.alto, g.ancho): continue
        yield (tr, fy, fx), a[::-1 if fy else 1, ::-1 if fx else 1]


def orientar(raw: np.ndarray, producto: str, mes: int, regla: tuple | None = None) -> tuple:
    """Devuelve (arreglo norte arriba, regla). Con `regla` la aplica; sin ella la deduce con los controles."""
    conf = PRODUCTOS[producto]
    g = GRILLAS[conf["grilla"]]
    if regla is not None:  # la regla se deduce en el primer mes y se aplica a los demás (controles estacionales fallarían)
        return dict(_variantes(raw, g))[regla], regla
    buenas = []
    for r, a in _variantes(raw, g):
        ok = _cumple(a, g, conf["controles"]) if conf["controles"] else _controles_merra(a, g, mes, producto == "swgdn")
        if ok: buenas.append((r, a))
    if len(buenas) != 1:
        raise RuntimeError(f"orientación de {producto} ambigua o imposible: {len(buenas)} variantes pasan los controles")
    return buenas[0][1], buenas[0][0]


def _leer_crudo(ruta, sub):
    import rasterio
    ref = f"netcdf:{ruta}:{sub}" if sub else str(ruta)
    with rasterio.open(ref) as d:
        return d.read(1)


def leer_campo(ruta, producto: str, mes: int, regla: tuple | None = None, calidad: bool = True):
    """Campo norte arriba (float64, NaN en relleno y en lo de mala calidad), regla de orientación usada."""
    conf = PRODUCTOS[producto]
    raw = _leer_crudo(ruta, conf["sub"]).astype("float64")
    malo = np.isclose(raw, conf["relleno"], rtol=1e-6) if abs(conf["relleno"]) < 1e6 else raw >= 1e14
    raw = np.where(malo, np.nan, raw)
    if producto == "ndvi":
        rel = _leer_crudo(ruta, conf["rel"]).astype("int16")
        raw = np.where(np.isin(rel, FIABLE_ACEPTADA) | (not calidad), raw, np.nan)
        raw = np.where((raw >= -2000) & (raw <= 10000), raw, np.nan)  # valid_range del producto
    if producto == "swgdn" and regla is None:
        regla = (False, False, False)  # misma malla y formato que T2M, cuya regla se deduce con controles de longitud
    a, regla = orientar(raw, producto, mes, regla)
    return a * conf["escala"], regla


def archivos(base: Path, producto: str) -> dict:
    """{ 'AAAA-MM': ruta } de los mensuales; MOD13C2 usa el mes de inicio del compuesto (día juliano UTC)."""
    import datetime as dt
    out = {}
    for f in sorted(glob.glob(str(Path(base) / PRODUCTOS[producto]["carpeta"] / "*.nc4"))):
        n = Path(f).name
        if producto == "ndvi":
            m = re.search(r"\.A(\d{4})(\d{3})\.", n)
            d = dt.date(int(m[1]), 1, 1) + dt.timedelta(days=int(m[2]) - 1)
            out[f"{d.year}-{d.month:02d}"] = f
        elif producto == "imerg_final":
            m = re.search(r"IMERG\.(\d{4})(\d{2})01-S", n)
            out[f"{m[1]}-{m[2]}"] = f
        elif producto in ("t2m", "swgdn"):
            m = re.search(r"\.(\d{4})(\d{2})\.nc4", n)
            out[f"{m[1]}-{m[2]}"] = f
        elif producto == "humedad_radicular":
            m = re.search(r"\.A(\d{4})(\d{2})\.", n)
            out[f"{m[1]}-{m[2]}"] = f
    return out


def dias_late(base: Path) -> dict:
    """{ 'AAAA-MM': [rutas diarias ordenadas] } de IMERG Late (días en UTC, un granulo por día)."""
    out = {}
    for f in sorted(glob.glob(str(Path(base) / "imerg_late" / "*.nc4"))):
        m = re.search(r"IMERG\.(\d{4})(\d{2})(\d{2})-S", Path(f).name)
        out.setdefault(f"{m[1]}-{m[2]}", []).append(f)
    return out
