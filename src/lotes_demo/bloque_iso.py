# asistido por SI: Claude Code (Anthropic), bloque isométrico y perfil del lote DEMO desde NASADEM (plan fase 3 v2 §4)
"""Bloque isométrico del relieve de cada lote DEMO, perfil O-E por el centro y manifiesto con SHA-256.

Entrada: NASADEM_HGT v001 (1 segundo de arco, HGT con píxel como punto), geometría de lotes_demo.json y el CRS métrico
de exposicion_erosiva_lotes.json (relieve_nasadem_30m.crs_metrico).
Transformación espacial: EPSG:4326 (grilla HGT de 1") a la UTM declarada (EPSG:326zz), celda de 30 m alineada a
múltiplos de 30 m. Remuestreo bilineal, porque la elevación es una variable continua y suave (no es clase ni máscara).
La UTM se calcula con las series de Snyder (USGS PP 1395, 1987, págs. 61-64) para no sumar dependencias; la prueba la
compara con pyproj cuando está instalado.
Los laterales de suelo del bloque son ilustrativos: no representan horizontes medidos.
Salidas en src/web/public/lotes/: bloque_<lote>.webp (relieve), bloque_<lote>_pendiente.webp, perfil_<lote>.json y
manifiesto_bloques.json. Sin fechas ni rutas locales en las salidas, para que dos corridas den los mismos bytes.
"""
import argparse
import hashlib
import json
import math
import os
import zipfile
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

RAIZ = Path(__file__).resolve().parents[2]
# WGS84
A_ELIPSE = 6378137.0
F_ELIPSE = 1 / 298.257223563
K0 = 0.9996
E2 = F_ELIPSE * (2 - F_ELIPSE)
EP2 = E2 / (1 - E2)
CELDA_M = 30.0
MARGEN_M = 150.0
EXAGERACION = 3.0  # factor vertical del dibujo; se declara en el perfil y en la interfaz
ESCALA = 2  # se dibuja al doble y se reduce, para suavizar bordes sin antialias de Pillow
VACIO = -32768
# Umbral del factor S de McCool que usa erosion.factor_pendiente_mccool (s < 0.09 o no)
UMBRAL_MCCOOL = 0.09


def _m(phi):
    # arco de meridiano (Snyder ec. 3-21)
    e4, e6 = E2 * E2, E2 ** 3
    return A_ELIPSE * ((1 - E2 / 4 - 3 * e4 / 64 - 5 * e6 / 256) * phi
                       - (3 * E2 / 8 + 3 * e4 / 32 + 45 * e6 / 1024) * np.sin(2 * phi)
                       + (15 * e4 / 256 + 45 * e6 / 1024) * np.sin(4 * phi)
                       - (35 * e6 / 3072) * np.sin(6 * phi))


def utm_directa(lat, lon, zona, norte=True):
    # lat, lon en grados -> x, y en metros (Snyder ec. 8-9 a 8-10)
    phi, lam = np.radians(lat), np.radians(lon)
    lam0 = math.radians((zona - 1) * 6 - 180 + 3)
    n = A_ELIPSE / np.sqrt(1 - E2 * np.sin(phi) ** 2)
    t = np.tan(phi) ** 2
    c = EP2 * np.cos(phi) ** 2
    a = (lam - lam0) * np.cos(phi)
    x = K0 * n * (a + (1 - t + c) * a ** 3 / 6 + (5 - 18 * t + t * t + 72 * c - 58 * EP2) * a ** 5 / 120) + 500000.0
    y = K0 * (_m(phi) + n * np.tan(phi) * (a * a / 2 + (5 - t + 9 * c + 4 * c * c) * a ** 4 / 24
                                           + (61 - 58 * t + t * t + 600 * c - 330 * EP2) * a ** 6 / 720))
    return x, y + (0.0 if norte else 10000000.0)


def utm_inversa(x, y, zona, norte=True):
    # x, y en metros -> lat, lon en grados (Snyder ec. 8-12 a 8-25)
    y = np.asarray(y, float) - (0.0 if norte else 10000000.0)
    lam0 = math.radians((zona - 1) * 6 - 180 + 3)
    mu = (y / K0) / (A_ELIPSE * (1 - E2 / 4 - 3 * E2 ** 2 / 64 - 5 * E2 ** 3 / 256))
    e1 = (1 - math.sqrt(1 - E2)) / (1 + math.sqrt(1 - E2))
    phi1 = (mu + (3 * e1 / 2 - 27 * e1 ** 3 / 32) * np.sin(2 * mu) + (21 * e1 ** 2 / 16 - 55 * e1 ** 4 / 32) * np.sin(4 * mu)
            + (151 * e1 ** 3 / 96) * np.sin(6 * mu) + (1097 * e1 ** 4 / 512) * np.sin(8 * mu))
    c1 = EP2 * np.cos(phi1) ** 2
    t1 = np.tan(phi1) ** 2
    n1 = A_ELIPSE / np.sqrt(1 - E2 * np.sin(phi1) ** 2)
    r1 = A_ELIPSE * (1 - E2) / (1 - E2 * np.sin(phi1) ** 2) ** 1.5
    d = (np.asarray(x, float) - 500000.0) / (n1 * K0)
    phi = phi1 - (n1 * np.tan(phi1) / r1) * (d * d / 2 - (5 + 3 * t1 + 10 * c1 - 4 * c1 * c1 - 9 * EP2) * d ** 4 / 24
                                              + (61 + 90 * t1 + 298 * c1 + 45 * t1 * t1 - 252 * EP2 - 3 * c1 * c1) * d ** 6 / 720)
    lam = lam0 + (d - (1 + 2 * t1 + c1) * d ** 3 / 6
                  + (5 - 2 * c1 + 28 * t1 - 3 * c1 * c1 + 8 * EP2 + 24 * t1 * t1) * d ** 5 / 120) / np.cos(phi1)
    return np.degrees(phi), np.degrees(lam)


def leer_hgt(zip_path: Path):
    # HGT de 3601 x 3601, entero de 16 bits big-endian; la fila 0 es el borde norte (lat_sur + 1)
    nombre = zip_path.stem.lower().split("_")[-1]
    lat_sur = (1 if nombre[0] == "n" else -1) * int(nombre[1:3])
    lon_oeste = (1 if nombre[3] == "e" else -1) * int(nombre[4:7])
    with zipfile.ZipFile(zip_path) as zf:
        hgt = next(n for n in zf.namelist() if n.endswith(".hgt"))
        arr = np.frombuffer(zf.read(hgt), dtype=">i2").reshape(3601, 3601).astype(float)
    arr[arr <= VACIO] = np.nan
    return arr, lat_sur, lon_oeste


def bilineal(arr, lat_sur, lon_oeste, lat, lon):
    # elevación en (lat, lon) por interpolación bilineal entre los 4 puntos HGT vecinos; vacío si falta un vecino
    fil = (lat_sur + 1.0 - np.asarray(lat)) * 3600.0
    col = (np.asarray(lon) - lon_oeste) * 3600.0
    f0, c0 = np.floor(fil).astype(int), np.floor(col).astype(int)
    df, dc = fil - f0, col - c0
    z = (arr[f0, c0] * (1 - df) * (1 - dc) + arr[f0, c0 + 1] * (1 - df) * dc
         + arr[f0 + 1, c0] * df * (1 - dc) + arr[f0 + 1, c0 + 1] * df * dc)
    if np.isnan(z).any():
        raise ValueError("NASADEM tiene vacíos dentro de la caja del lote")
    return z


def _color_relieve(t):
    # rampa verde oscuro a verde claro y ocre, t en [0, 1]
    paradas = np.array([[34, 78, 52], [76, 140, 84], [168, 182, 104], [196, 170, 120]], float)
    t = np.clip(t, 0, 1) * (len(paradas) - 1)
    i = np.minimum(np.floor(t).astype(int), len(paradas) - 2)
    f = (t - i)[..., None]
    return paradas[i] * (1 - f) + paradas[i + 1] * f


# Clases de pendiente: baja, hasta el umbral de McCool, sobre el umbral
COLORES_PENDIENTE = ([86, 160, 110], [214, 190, 92], [196, 96, 64])
LIMITE_PENDIENTE_BAJA = 0.03


def construir(lote_id: str, zip_path: Path, lotes_demo: Path, exposicion: Path, salida: Path) -> dict:
    lote = next(l for l in json.loads(lotes_demo.read_text(encoding="utf-8"))["lotes"] if l["lote_id"] == lote_id)
    relieve = json.loads(exposicion.read_text(encoding="utf-8"))["lotes"][lote_id]["relieve_nasadem_30m"]
    epsg = int(relieve["crs_metrico"].split(":")[1])
    if not (32601 <= epsg <= 32660 or 32701 <= epsg <= 32760):
        raise ValueError(f"crs_metrico {epsg} no es UTM WGS84")
    zona, norte = epsg % 100, epsg < 32700
    arr, lat_sur, lon_oeste = leer_hgt(zip_path)

    # caja del lote en UTM, con margen, alineada a 30 m
    anillo = np.array(lote["geometria"]["coordinates"][0], float)
    ax, ay = utm_directa(anillo[:, 1], anillo[:, 0], zona, norte)
    x0 = math.floor((ax.min() - MARGEN_M) / CELDA_M) * CELDA_M
    x1 = math.ceil((ax.max() + MARGEN_M) / CELDA_M) * CELDA_M
    y0 = math.floor((ay.min() - MARGEN_M) / CELDA_M) * CELDA_M
    y1 = math.ceil((ay.max() + MARGEN_M) / CELDA_M) * CELDA_M
    xs = np.arange(x0 + CELDA_M / 2, x1, CELDA_M)
    ys = np.arange(y1 - CELDA_M / 2, y0, -CELDA_M)  # fila 0 al norte
    gx, gy = np.meshgrid(xs, ys)
    glat, glon = utm_inversa(gx, gy, zona, norte)
    z = bilineal(arr, lat_sur, lon_oeste, glat, glon)

    # perfil O-E por el centro del lote, con una muestra exactamente en el centro
    cx, cy = utm_directa(lote["lat"], lote["lon"], zona, norte)
    k_izq, k_der = int((cx - x0) // CELDA_M), int((x1 - cx) // CELDA_M)
    px = cx + CELDA_M * np.arange(-k_izq, k_der + 1)
    plat, plon = utm_inversa(px, np.full_like(px, cy), zona, norte)
    pz = bilineal(arr, lat_sur, lon_oeste, plat, plon)

    # pendiente en m/m sobre la grilla UTM (diferencias centrales); es solo para la capa visual
    dz_dy, dz_dx = np.gradient(z, CELDA_M, CELDA_M)
    pend = np.hypot(dz_dx, dz_dy)

    zmin, zmax = float(z.min()), float(z.max())
    t_rel = (z - zmin) / max(zmax - zmin, 1e-9)
    # sombreado: luz del noroeste a 45 grados
    az, alt = math.radians(315), math.radians(45)
    pend_ang = np.arctan(pend * EXAGERACION)
    aspecto = np.arctan2(-dz_dx, dz_dy)
    luz = np.clip(np.sin(alt) * np.cos(pend_ang) + np.cos(alt) * np.sin(pend_ang) * np.cos(az - aspecto), 0, 1)
    sombra = (0.55 + 0.45 * luz)[..., None]
    clases = np.where(pend < LIMITE_PENDIENTE_BAJA, 0, np.where(pend < UMBRAL_MCCOOL, 1, 2))
    rel_rgb = _color_relieve(t_rel) * sombra
    pen_rgb = np.array(COLORES_PENDIENTE, float)[clases] * sombra

    salida.mkdir(parents=True, exist_ok=True)
    archivos = {}
    for nombre, rgb in ((f"bloque_{lote_id}.webp", rel_rgb), (f"bloque_{lote_id}_pendiente.webp", pen_rgb)):
        img = _dibujar(z, rgb, anillo, zona, norte, x0, y1)
        ruta = salida / nombre
        img.save(ruta, format="WEBP", lossless=True, quality=100, method=4, exact=True)
        archivos[nombre] = ruta

    perfil = {
        "lote_id": lote_id,
        "fuente": relieve["producto"],
        "archivo_entrada": zip_path.name,
        "crs_origen": "EPSG:4326",
        "crs_destino": relieve["crs_metrico"],
        "celda_m": CELDA_M,
        "remuestreo": "bilineal",
        "motivo_remuestreo": "elevación continua y suave; no es clase ni máscara",
        "transecto": "oeste a este por el centro del lote (lotes_demo.json lat/lon)",
        "distancia_m": [round(float(d), 1) for d in (px - cx)],
        "elevacion_m": [round(float(v), 1) for v in pz],
        "indice_centro": k_izq,
        "elevacion_centro_m": round(float(pz[k_izq]), 1),
        "exageracion_vertical": EXAGERACION,
        "laterales": "ilustrativos, no son horizontes medidos",
        "leyenda_relieve_m": [round(zmin, 1), round(zmax, 1)],
        "leyenda_pendiente_m_m": [LIMITE_PENDIENTE_BAJA, UMBRAL_MCCOOL],
        "nota_pendiente": "capa visual sobre la grilla UTM; la erosión usa relieve_nasadem_30m.pendiente_media_m_m",
    }
    ruta_perfil = salida / f"perfil_{lote_id}.json"
    # LF explícito: con CRLF de Windows git cambiaría los bytes y el SHA-256 del manifiesto dejaría de valer
    ruta_perfil.write_bytes((json.dumps(perfil, ensure_ascii=False, indent=1) + "\n").encode("utf-8"))
    archivos[ruta_perfil.name] = ruta_perfil
    return {"entrada_sha256": _sha(zip_path), "archivos": {n: _sha(r) for n, r in archivos.items()}}


def _dibujar(z, rgb, anillo, zona, norte, x0, y1) -> Image.Image:
    # proyección isométrica: i al este, j al sur; se pinta de atrás (noroeste) hacia adelante (sureste)
    nf, nc = z.shape
    s = 14.0 * ESCALA  # píxeles por celda en el plano
    ez = s / CELDA_M * EXAGERACION  # píxeles por metro en la vertical
    base = float(z.min()) - 0.18 * nc * CELDA_M / EXAGERACION  # fondo del bloque, solo para el dibujo
    cos30, sin30 = math.cos(math.radians(30)), 0.5
    ancho = int((nc + nf) * s * cos30) + 4 * ESCALA * 10
    alto_sup = (float(z.max()) - base) * ez
    alto = int((nc + nf) * s * sin30 + alto_sup) + 4 * ESCALA * 10
    ox, oy = nf * s * cos30 + 20 * ESCALA, (float(z.max()) - base) * ez + 20 * ESCALA

    def pt(i, j, h):
        return (ox + (i - j) * s * cos30, oy + (i + j) * s * sin30 - (h - base) * ez)

    # elevación en los vértices de las celdas (promedio de las celdas vecinas)
    zp = np.pad(z, 1, mode="edge")
    zv = (zp[:-1, :-1] + zp[:-1, 1:] + zp[1:, :-1] + zp[1:, 1:]) / 4
    img = Image.new("RGBA", (ancho, alto), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    # laterales: cara sur (j = nf) y cara este (i = nc), con dos franjas de suelo
    capas = ((0.0, 0.25, (92, 64, 44)), (0.25, 1.0, (66, 46, 32)))
    for a, b, color in capas:
        for i in range(nc):
            h0, h1 = zv[nf, i], zv[nf, i + 1]
            ta = (h0 - (h0 - base) * a, h1 - (h1 - base) * a)
            tb = (h0 - (h0 - base) * b, h1 - (h1 - base) * b)
            d.polygon([pt(i, nf, ta[0]), pt(i + 1, nf, ta[1]), pt(i + 1, nf, tb[1]), pt(i, nf, tb[0])], fill=color + (255,))
        for j in range(nf):
            h0, h1 = zv[j, nc], zv[j + 1, nc]
            ta = (h0 - (h0 - base) * a, h1 - (h1 - base) * a)
            tb = (h0 - (h0 - base) * b, h1 - (h1 - base) * b)
            sombra = tuple(int(c * 0.8) for c in color)
            d.polygon([pt(nc, j, ta[0]), pt(nc, j + 1, ta[1]), pt(nc, j + 1, tb[1]), pt(nc, j, tb[0])], fill=sombra + (255,))
    # superficie, en orden de profundidad
    orden = sorted(((i + j, j, i) for j in range(nf) for i in range(nc)))
    col = np.clip(rgb, 0, 255).astype(np.uint8)
    for _, j, i in orden:
        c = tuple(int(v) for v in col[j, i]) + (255,)
        d.polygon([pt(i, j, zv[j, i]), pt(i + 1, j, zv[j, i + 1]), pt(i + 1, j + 1, zv[j + 1, i + 1]), pt(i, j + 1, zv[j + 1, i])], fill=c)
    # contorno del lote sobre la superficie
    ax, ay = utm_directa(anillo[:, 1], anillo[:, 0], zona, norte)
    fi, fj = (ax - x0) / CELDA_M, (y1 - ay) / CELDA_M
    linea = []
    for k in range(len(fi) - 1):
        for u in np.linspace(0, 1, 24, endpoint=False):
            i, j = fi[k] + (fi[k + 1] - fi[k]) * u, fj[k] + (fj[k + 1] - fj[k]) * u
            ii, jj = min(int(round(i)), nc), min(int(round(j)), nf)
            linea.append(pt(i, j, zv[jj, ii] + 0.5))
    linea.append(linea[0])
    d.line(linea, fill=(240, 248, 236, 255), width=2 * ESCALA)
    img = img.resize((ancho // ESCALA, alto // ESCALA), Image.LANCZOS)
    return img.crop(img.getbbox())


def _sha(ruta: Path) -> str:
    return hashlib.sha256(ruta.read_bytes()).hexdigest()


ZIPS = {"DEMO-COL-01": "NASADEM_HGT_n00w078.zip", "DEMO-USA-01": "NASADEM_HGT_n41w097.zip"}


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--crudos", type=Path, default=Path(os.environ.get("AGROVERSEX_NASADEM", RAIZ / "datos/crudos/nasadem")))
    p.add_argument("--lotes", type=Path, default=RAIZ / "src/web/public/datos/lotes_demo.json")
    p.add_argument("--exposicion", type=Path, default=RAIZ / "datos/lotes/exposicion_erosiva_lotes.json")
    p.add_argument("--salida", type=Path, default=RAIZ / "src/web/public/lotes")
    a = p.parse_args(argv)
    manifiesto = {"generador": "src/lotes_demo/bloque_iso.py", "remuestreo": "bilineal", "celda_m": CELDA_M,
                  "exageracion_vertical": EXAGERACION, "lotes": {}}
    for lote_id, zip_nombre in ZIPS.items():
        manifiesto["lotes"][lote_id] = construir(lote_id, a.crudos / zip_nombre, a.lotes, a.exposicion, a.salida)
    (a.salida / "manifiesto_bloques.json").write_bytes((json.dumps(manifiesto, indent=1) + "\n").encode("utf-8"))
    return manifiesto


if __name__ == "__main__":
    print(json.dumps(main(), indent=1))
