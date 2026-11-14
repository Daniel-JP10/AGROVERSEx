# asistido por SI: Claude Code, fracción de observaciones HLS v2.0 válidas por píxel y mes (T-D5 Parte B)
"""Fmask de HLS v2.0: bit1 nube, bit2 adyacente a nube/sombra, bit3 sombra, bit4 nieve/hielo, bit5 agua, bits 6-7
aerosol, 255 sin dato. Válida = observada y sin bits 1-4. El agua no invalida. Denominador: escenas con dato (!=255)
en ese píxel, cada escena es una observación."""
import json
import sys
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np

MALOS = 0b00011110  # bits 1 a 4


def clasificar(fmask):
    f = np.asarray(fmask, dtype=np.uint8)
    obs = f != 255
    return obs, obs & ((f & MALOS) == 0)


def tabla_mensual(escenas):
    # escenas: [(fecha_iso, obs_bool[npix], valido_bool[npix])] -> por mes fracción válida por píxel
    por = defaultdict(list)
    for fecha, o, v in escenas:
        por[fecha[:7]].append((o, v))
    out = {}
    for mes, lst in sorted(por.items()):
        no = np.sum([o for o, _ in lst], axis=0).astype(float)
        nv = np.sum([v for _, v in lst], axis=0).astype(float)
        with np.errstate(invalid="ignore", divide="ignore"):
            fr = np.where(no > 0, nv / no, np.nan)
        out[mes] = {"fraccion_pixel": fr, "n_escenas": len(lst), "n_obs_pixel": no}
    return out


def _buscar(bbox, ini, fin, zona_tile):
    import requests
    res = []
    for sn in ("HLSL30", "HLSS30"):
        p = 1
        while True:
            r = requests.get("https://cmr.earthdata.nasa.gov/search/granules.json", timeout=120, params={
                "short_name": sn, "version": "2.0", "bounding_box": bbox, "temporal": f"{ini}T00:00:00Z,{fin}T23:59:59Z",
                "page_size": 500, "page_num": p})
            e = r.json()["feed"]["entry"]
            if not e:
                break
            for g in e:
                t = g["title"].split(".")
                if t[2].startswith(zona_tile):
                    u = [x["href"] for x in g["links"] if x["href"].endswith("Fmask.tif") and x["href"].startswith("https")]
                    res.append((g["title"], u[0], g["time_start"]))
            p += 1
    return res


def _leer(url, geom_utm_cache):
    import rasterio
    from rasterio.mask import mask
    import threading
    # un archivo de cookies por hilo: con uno compartido GDAL recibe 303 al azar
    ck = f"/tmp/hls_ck_{threading.get_ident()}"
    with rasterio.Env(GDAL_HTTP_COOKIEFILE=ck, GDAL_HTTP_COOKIEJAR=ck), rasterio.open(url) as ds:
        key = str(ds.crs)
        if key not in geom_utm_cache:
            from pyproj import Transformer
            from shapely.geometry import shape
            from shapely.ops import transform
            tr = Transformer.from_crs(4326, ds.crs, always_xy=True).transform
            geom_utm_cache[key] = transform(tr, shape(geom_utm_cache["geo"]))
        a, _ = mask(ds, [geom_utm_cache[key]], crop=True, all_touched=False, filled=True, nodata=255)
    return a[0]


def correr(lote, ini, fin, zona_tile, salida: Path, hilos=12):
    import os
    os.environ.setdefault("GDAL_HTTP_NETRC", "YES")
    os.environ.setdefault("GDAL_HTTP_COOKIEFILE", "/tmp/hls_cookies")
    os.environ.setdefault("GDAL_HTTP_COOKIEJAR", "/tmp/hls_cookies")
    os.environ.setdefault("GDAL_DISABLE_READDIR_ON_OPEN", "EMPTY_DIR")
    os.environ.setdefault("CPL_VSIL_CURL_ALLOWED_EXTENSIONS", ".tif")
    lotes = json.loads(Path(sys.argv[0]).resolve().parents[2].joinpath("datos/lotes/lotes_demo.json").read_text())["lotes"]
    L = next(x for x in lotes if x["lote_id"] == lote)
    xs = [p[0] for p in L["geometria"]["coordinates"][0]]
    ys = [p[1] for p in L["geometria"]["coordinates"][0]]
    gr = _buscar(f"{min(xs)},{min(ys)},{max(xs)},{max(ys)}", ini, fin, zona_tile)
    cache = {"geo": L["geometria"]}
    print(lote, "granulos", len(gr), flush=True)

    def una(g):
        for _ in range(3):
            try:
                return g, _leer("/vsicurl/" + g[1], cache)
            except Exception as e:
                err = str(e)[:100]
        return g, err

    escenas, fallos = [], []
    with ThreadPoolExecutor(hilos) as ex:
        for g, a in ex.map(una, gr):
            if isinstance(a, str):
                fallos.append((g[0], a))
                continue
            o, v = clasificar(a.ravel())
            escenas.append((g[2][:10], g[0], o, v))
    escenas.sort(key=lambda x: x[0])
    # los píxeles del recorte son los mismos en todas las escenas de una misma tesela
    n = max(len(e[2]) for e in escenas)
    escenas = [e for e in escenas if len(e[2]) == n]
    t = tabla_mensual([(f, o, v) for f, _, o, v in escenas])
    res = {"lote_id": lote, "periodo": [ini, fin], "tesela": zona_tile, "n_pixeles": n, "n_granulos": len(gr),
           "n_fallos": len(fallos), "fallos": fallos[:10], "meses": {}}
    for m, d in t.items():
        fr = d["fraccion_pixel"]
        res["meses"][m] = {"n_escenas": d["n_escenas"], "media": float(np.nanmean(fr)),
                           "q05": float(np.nanquantile(fr, .05)), "q50": float(np.nanquantile(fr, .5)),
                           "q95": float(np.nanquantile(fr, .95))}
    salida.write_text(json.dumps(res, indent=1), encoding="utf-8")
    print("ok", len(t), "meses", len(fallos), "fallos")


if __name__ == "__main__":
    correr(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4], Path(sys.argv[5]))
