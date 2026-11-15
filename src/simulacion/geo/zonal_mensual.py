# asistido por SI: Claude Code (Anthropic), motor de agregación zonal mensual con pesos por firma de grilla (T-D2)
"""Motor zonal: la cobertura de cada unidad sobre cada celda se calcula una vez por grilla
(exactextract) y se guarda como matriz dispersa en formato COO (u, c, cov); cada mes es un
producto disperso por vector, hecho con np.bincount (el entorno no trae scipy).

shortcut: solo grillas geográficas WGS84 (todas las de T-D3 lo son); las de igual área (EASE-Grid 2.0)
y Homolosine siguen en zonal.py, súbelas aquí cuando entre SMAP."""
import hashlib
import warnings
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import shapely


def _wkt4326() -> str:
    from pyproj import CRS
    return CRS.from_epsg(4326).to_wkt()


@dataclass(frozen=True)
class Grilla:
    # grilla geográfica WGS84 con norte arriba: x0 borde oeste, y0 borde norte, tamaños positivos
    x0: float
    y0: float
    dx: float
    dy: float
    alto: int
    ancho: int

    def firma(self) -> str:
        # CRS, origen, tamaño de celda y forma; redondeo a 1e-9 para que la firma no dependa del ruido float
        txt = f"EPSG:4326|{self.x0:.9f}|{self.y0:.9f}|{self.dx:.9f}|{self.dy:.9f}|{self.alto}|{self.ancho}"
        return hashlib.sha256(txt.encode()).hexdigest()[:16]

    def areas_fila(self) -> np.ndarray:
        # peso de latitud por fila: sin(lat_sup) - sin(lat_inf); el ancho en longitud es constante y se cancela
        sup = np.clip(self.y0 - self.dy * np.arange(self.alto), -90, 90)
        inf = np.clip(self.y0 - self.dy * (np.arange(self.alto) + 1), -90, 90)
        return np.abs(np.sin(np.radians(sup)) - np.sin(np.radians(inf)))


def grilla_desde_centros(lon: np.ndarray, lat: np.ndarray) -> Grilla:
    # los ejes son centros de celda (Registration=CENTER) y pueden venir crecientes; la grilla sale norte arriba
    lon, lat = np.sort(np.asarray(lon, "float64")), np.sort(np.asarray(lat, "float64"))
    dx, dy = np.diff(lon).mean(), np.diff(lat).mean()
    if not (np.allclose(np.diff(lon), dx, atol=1e-6) and np.allclose(np.diff(lat), dy, atol=1e-6)):
        raise ValueError("ejes no regulares")
    return Grilla(round(lon[0] - dx / 2, 9), round(lat[-1] + dy / 2, 9), round(dx, 9), round(dy, 9),
                  len(lat), len(lon))


@dataclass
class Pesos:
    u: np.ndarray    # índice de unidad (posición en la lista de entrada)
    c: np.ndarray    # celda plana de la grilla completa (fila * ancho + columna), fila 0 al norte
    cov: np.ndarray  # fracción de la celda cubierta por la unidad
    n_unidades: int


def calcular_pesos(g: Grilla, geoms) -> Pesos:
    from exactextract import exact_extract
    from exactextract.raster import NumPyRasterSource
    import geopandas as gpd
    geoms = list(geoms)
    xmin, ymin, xmax, ymax = shapely.total_bounds(np.asarray(geoms, dtype=object))
    # ventana de la grilla que toca las unidades, con una celda de margen: Colombia no recorre la malla mundial
    c0 = max(int(np.floor((xmin - g.x0) / g.dx)) - 1, 0)
    c1 = min(int(np.ceil((xmax - g.x0) / g.dx)) + 1, g.ancho)
    r0 = max(int(np.floor((g.y0 - ymax) / g.dy)) - 1, 0)
    r1 = min(int(np.ceil((g.y0 - ymin) / g.dy)) + 1, g.alto)
    ven_ancho = c1 - c0
    fuente = NumPyRasterSource(np.ones((r1 - r0, ven_ancho), "float32"),
                               g.x0 + c0 * g.dx, g.y0 - r1 * g.dy, g.x0 + c1 * g.dx, g.y0 - r0 * g.dy,
                               srs_wkt=_wkt4326())
    gdf = gpd.GeoDataFrame({"uid": np.arange(len(geoms))}, geometry=geoms, crs="EPSG:4326")
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", RuntimeWarning)  # aviso de WKT equivalente, no de CRS distinto
        r = exact_extract(fuente, gdf, ["cell_id", "coverage"], include_cols=["uid"], output="pandas")
    n = np.array([len(x) for x in r["cell_id"]])
    ids = np.concatenate(list(r["cell_id"])).astype("int64")
    celda = (r0 + ids // ven_ancho) * g.ancho + (c0 + ids % ven_ancho)
    return Pesos(np.repeat(r["uid"].to_numpy().astype("int32"), n), celda,
                 np.concatenate(list(r["coverage"])).astype("float32"), len(geoms))


def hash_unidades(ids, geoms) -> str:
    # hash del contenido de las unidades usadas (id y geometría), no del nombre del archivo
    h = hashlib.sha256()
    for i, gm in zip(ids, geoms):
        h.update(str(i).encode())
        h.update(shapely.to_wkb(gm))
    return h.hexdigest()[:16]


def pesos_con_cache(g: Grilla, ids, geoms, carpeta: Path) -> Pesos:
    # la caché se indexa por firma de grilla y hash de unidades: si cambia cualquiera, es otro archivo
    ruta = Path(carpeta) / f"pesos_{g.firma()}_{hash_unidades(ids, geoms)}.npz"
    if ruta.exists():
        z = np.load(ruta)
        return Pesos(z["u"], z["c"], z["cov"], int(z["n"]))
    p = calcular_pesos(g, geoms)
    Path(carpeta).mkdir(parents=True, exist_ok=True)
    np.savez_compressed(ruta, u=p.u, c=p.c, cov=p.cov, n=p.n_unidades)
    return p


def fraccion_clase(clases: np.ndarray, bloque: int, clases_validas: set) -> np.ndarray:
    # fino a grueso para clases: cada celda fina cuenta como 1 si su clase entra y 0 si no (vecino más
    # cercano, sin interpolar), y luego se promedia por bloques de igual área
    alto, ancho = clases.shape
    if alto % bloque or ancho % bloque:
        raise ValueError("el bloque no divide la malla")
    es = np.isin(clases, list(clases_validas)).astype("float64")
    return es.reshape(alto // bloque, bloque, ancho // bloque, bloque).mean(axis=(1, 3))


def fraccion_cultivo(g: Grilla, clases: np.ndarray, fino: Grilla, clases_cultivo: set, ventana_bbox) -> np.ndarray:
    """Fracción de cultivo por celda de `g` (arreglo plano de la grilla completa, 0 fuera de la ventana).

    `clases` es la malla fina de clases (norte arriba, geográfica) con grilla `fino`. Cada celda fina cuenta 1 si
    su clase es de cultivo y 0 si no; la fracción es el promedio por área de la intersección exacta con la celda
    gruesa (exactextract). No hay remuestreo: nunca se interpola una clase."""
    from exactextract import exact_extract
    from exactextract.raster import NumPyRasterSource
    import geopandas as gpd
    xmin, ymin, xmax, ymax = ventana_bbox
    c0, c1 = max(int(np.floor((xmin - g.x0) / g.dx)) - 1, 0), min(int(np.ceil((xmax - g.x0) / g.dx)) + 1, g.ancho)
    r0, r1 = max(int(np.floor((g.y0 - ymax) / g.dy)) - 1, 0), min(int(np.ceil((g.y0 - ymin) / g.dy)) + 1, g.alto)
    rr, cc = np.meshgrid(np.arange(r0, r1), np.arange(c0, c1), indexing="ij")
    x_o, y_n = g.x0 + cc.ravel() * g.dx, g.y0 - rr.ravel() * g.dy
    celdas = gpd.GeoDataFrame({"k": (rr * g.ancho + cc).ravel()}, crs="EPSG:4326",
                              geometry=shapely.box(x_o, y_n - g.dy, x_o + g.dx, y_n))
    es = np.isin(clases, list(clases_cultivo)).astype("uint8")
    fuente = NumPyRasterSource(es, fino.x0, fino.y0 - fino.alto * fino.dy, fino.x0 + fino.ancho * fino.dx, fino.y0,
                               srs_wkt=_wkt4326())
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", RuntimeWarning)
        r = exact_extract(fuente, celdas, ["mean"], include_cols=["k"], output="pandas")
    out = np.zeros(g.alto * g.ancho, "float32")
    out[r["k"].to_numpy()] = np.nan_to_num(r["mean"].to_numpy(), nan=0.0)
    return out


def _cuantiles(u, x, w, n, ps):
    # cuantil ponderado interpolado: cada celda ocupa la posición (peso acumulado - peso/2) / peso de la unidad y
    # entre posiciones se interpola linealmente; fuera de ellas se acota al mínimo y al máximo. Una celda sola
    # da p10 = p90 = su valor, y con pocas celdas el intervalo no se parte en escalones
    o = np.lexsort((x, u))
    u, x, w = u[o], x[o], w[o]
    if len(x) == 0:
        return [np.full(n, np.nan) for _ in ps]
    cs = np.cumsum(w, dtype="float64")
    ini = np.searchsorted(u, np.arange(n), "left")
    fin = np.searchsorted(u, np.arange(n), "right")
    base = np.where(ini > 0, cs[np.maximum(ini - 1, 0)], 0.0)
    tot = (cs[np.maximum(fin - 1, 0)] - base)
    pos = (cs - w / 2 - base[u]) / tot[u]
    clave = u + pos  # creciente en todo el arreglo: u entero y pos entre 0 y 1
    out = []
    for p in ps:
        i = np.searchsorted(clave, np.arange(n) + p, "left")
        i1 = np.clip(i, ini, np.maximum(fin - 1, 0))      # primera celda con posición >= p
        i0 = np.clip(i - 1, ini, np.maximum(fin - 1, 0))  # celda anterior dentro de la unidad
        i1, i0 = np.minimum(i1, len(x) - 1), np.minimum(i0, len(x) - 1)
        dp = pos[i1] - pos[i0]
        f = np.where(dp > 0, np.clip((p - pos[i0]) / np.where(dp > 0, dp, 1), 0, 1), 1.0)
        out.append(np.where(fin == ini, np.nan, x[i0] + f * (x[i1] - x[i0])))
    return out


def agregar(p: Pesos, g: Grilla, x: np.ndarray, cultivo: np.ndarray | None = None, umbral: float = 0.5) -> dict:
    """Un mes: x es la grilla plana (norte arriba) con NaN en lo malo. Devuelve valor, p10, p90 (espacial),
    frac_valida y motivo. Bajo `umbral` de frac_valida el valor sale NaN con motivo; no se rellena."""
    n = p.n_unidades
    w = p.cov.astype("float64") * g.areas_fila()[p.c // g.ancho]
    if cultivo is not None:
        w = w * np.nan_to_num(cultivo[p.c].astype("float64"), nan=0.0)
    xc = x[p.c].astype("float64")
    ok = np.isfinite(xc) & (w > 0)
    total = np.bincount(p.u, w, n)
    wv = np.bincount(p.u[ok], w[ok], n)
    suma = np.bincount(p.u[ok], (w * xc)[ok], n)
    with np.errstate(invalid="ignore", divide="ignore"):
        frac = np.where(total > 0, wv / total, 0.0)
        valor = suma / wv
    p10, p90 = _cuantiles(p.u[ok], xc[ok], w[ok], n, (0.1, 0.9))
    motivo = np.full(n, None, dtype=object)
    motivo[total <= 0] = "sin_cultivo" if cultivo is not None else "sin_cobertura"
    motivo[(total > 0) & (wv <= 0)] = "sin_celdas_validas"
    motivo[(wv > 0) & (frac < umbral)] = "frac_valida_bajo_umbral"
    malo = np.array([m is not None for m in motivo])
    for a in (valor, p10, p90):
        a[malo] = np.nan
    return {"valor": valor, "p10": p10, "p90": p90, "frac_valida": frac, "motivo": motivo}
