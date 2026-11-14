# asistido por SI: Claude Code (Anthropic), escritura y revisión de código; base del prototipo migrada en el hackatón
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
import rasterio
import shapely
from exactextract import exact_extract
from exactextract.raster import NumPyRasterSource


def pesos_area_geograficos(transform, alto: int, ancho: int = 1) -> np.ndarray:
    # peso por fila = sin(lat_sup) - sin(lat_inf), normalizado a suma 1 (área de la banda esférica)
    lat_sup = transform.f + transform.e * np.arange(alto)
    lat_inf = lat_sup + transform.e
    w = np.abs(np.sin(np.radians(lat_sup)) - np.sin(np.radians(lat_inf)))
    return w / w.sum()


def _fuente_pesos(d: rasterio.DatasetReader):
    # shortcut: broadcast de una columna (sin memoria extra); si exactextract copia, trocear por bandas
    w = pesos_area_geograficos(d.transform, d.height)
    arr = np.broadcast_to((w / w.max()).astype("float32")[:, None], (d.height, d.width))
    b = d.bounds
    return NumPyRasterSource(arr, b.left, b.bottom, b.right, b.top, srs_wkt=d.crs.to_wkt())


# interrupciones de la Homolosine: norte en -40, sur en -100, -20 y 80; la franja corta unos 22 m
_EPS = 1e-4
_CORTES = shapely.union_all([shapely.box(lon - _EPS, 0, lon + _EPS, 90) for lon in (-40,)]
                            + [shapely.box(lon - _EPS, -90, lon + _EPS, 0) for lon in (-100, -20, 80)])


def proyectar_igh(unidades: gpd.GeoDataFrame, crs) -> gpd.GeoDataFrame:
    # una unidad que cruza una interrupción (Groenlandia, -40) se proyecta con una cuña falsa y el área
    # se multiplica; se corta por los meridianos de interrupción y se densifica antes de proyectar
    g = unidades.geometry.to_crs("EPSG:4326").values.copy()
    cruza = shapely.intersects(g, _CORTES)
    if cruza.any():
        g[cruza] = shapely.segmentize(shapely.difference(g[cruza], _CORTES), 0.1)
    return gpd.GeoDataFrame(unidades.drop(columns="geometry"), geometry=g, crs="EPSG:4326").to_crs(crs)


def _preparar(ruta: Path, unidades: gpd.GeoDataFrame):
    # se reproyecta al CRS del raster; "id" choca con el id de feature de exactextract, se usa "uid"
    with rasterio.open(ruta) as d:
        crs, pesos = d.crs, (_fuente_pesos(d) if d.crs.is_geographic else None)
        b, forma = d.bounds, (d.height, d.width)
    reproy = proyectar_igh(unidades, crs) if crs.to_dict().get("proj") == "igh" else unidades.to_crs(crs)
    u = reproy[["id", "geometry"]].rename(columns={"id": "uid"})
    unos = NumPyRasterSource(np.broadcast_to(np.float32(1), forma), b.left, b.bottom, b.right,
                             b.top, srs_wkt=crs.to_wkt())
    return u, pesos, unos


def _tabla_media(r, total, pref, factor):
    v, n = r[f"{pref}_val"], r[f"{pref}_count"]
    fr = (n / total.where(total > 0)).fillna(0.0).clip(upper=1.0)
    valor = (v / factor).astype(object)
    valor[(fr == 0) | v.isna()] = None
    return pd.DataFrame({"id": r["uid"], "valor": valor, "fraccion_valida": fr})


def medias_ponderadas(rutas: list[Path], unidades: gpd.GeoDataFrame, factores: list[float]) -> dict:
    # varios rasters de una misma grilla en una sola llamada: la cobertura de cada polígono se calcula una vez.
    # continuas: media ponderada por área; CRS geográfico pondera por sin(lat), CRS de área igual pesa 1.
    # shortcut: fraccion_valida se cuenta en celdas (sin peso de latitud), basta para marcar cobertura
    u, pesos, unos = _preparar(rutas[0], unidades)
    op = "weighted_mean" if pesos is not None else "mean"
    kw = {"weights": pesos} if pesos is not None else {}
    r = exact_extract([str(x) for x in rutas], u, [op, "count"], include_cols=["uid"],
                      output="pandas", **kw)
    r.columns = [c.replace("__", "_") for c in r.columns]  # con pesos y varios rasters: "<raster>__weighted_mean"
    if len(rutas) == 1:  # con un solo raster exactextract no antepone el nombre
        pref = Path(rutas[0]).stem
        r = r.rename(columns={op: f"{pref}_{op}", "count": f"{pref}_count"})
    total = exact_extract(unos, u, ["count"], include_cols=["uid"], output="pandas")["count"]
    out = {}
    for ruta, f in zip(rutas, factores):
        pref = Path(ruta).stem
        r2 = r.rename(columns={f"{pref}_{op}": f"{pref}_val"})
        out[ruta] = _tabla_media(r2, total, pref, f)
    return out


def media_ponderada(ruta_raster: Path, unidades: gpd.GeoDataFrame, factor: float) -> pd.DataFrame:
    # el NoData lo declara el propio raster (metadato); exactextract lo respeta
    return medias_ponderadas([ruta_raster], unidades, [factor])[ruta_raster]


def extremos(ruta_raster: Path, unidades: gpd.GeoDataFrame) -> pd.DataFrame:
    # mínimo y máximo de las celdas que tocan la unidad (con dato); NULL si no hay ninguna
    u, _, _ = _preparar(ruta_raster, unidades)
    r = exact_extract(str(ruta_raster), u, ["min", "max"], include_cols=["uid"], output="pandas")
    r.columns = ["id", "minimo", "maximo"]
    return r.astype({"minimo": object, "maximo": object}).where(r.notna(), None)


def fracciones_clase(ruta_raster: Path, unidades: gpd.GeoDataFrame,
                     clases_validas: set[int]) -> pd.DataFrame:
    # clases: fracción de área por clase válida, renormalizada a 1; sin interpolación
    u, pesos, _ = _preparar(ruta_raster, unidades)
    op = "weighted_frac" if pesos is not None else "frac"
    kw = {"weights": pesos} if pesos is not None else {}
    r = exact_extract(str(ruta_raster), u, ["unique", op], include_cols=["uid"], output="pandas", **kw)
    r = r.rename(columns={op: "frac"})
    filas = []
    for fila in r.itertuples(index=False):
        pares = [(int(c), f) for c, f in zip(fila.unique, fila.frac) if int(c) in clases_validas]
        total = sum(f for _, f in pares)
        if total > 0:
            filas += [(fila.uid, c, f / total) for c, f in pares]
    return pd.DataFrame(filas, columns=["id", "clase", "fraccion"])


def moda(fracciones: pd.DataFrame) -> pd.Series:
    idx = fracciones.groupby("id")["fraccion"].idxmax()
    return fracciones.loc[idx].set_index("id")["clase"]


def ponderar_profundidad(v_0_5, v_5_15, v_15_30):
    # espesores 5, 10 y 15 cm sobre 30 cm
    return (5 * v_0_5 + 10 * v_5_15 + 15 * v_15_30) / 30
