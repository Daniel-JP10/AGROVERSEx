# asistido por SI: Claude Code (Anthropic), mapa del mundo en puntos para el fondo de la entrada, desde Natural Earth 1:10m land (dominio público)
"""Rejilla equirectangular de puntos sobre tierra: decoración sin cifras (R1, fondo de la entrada).

Uso: python mapa_puntos.py <ne_10m_land.zip> <salida.svg>
Paso de 2 grados, latitud 76 N a 58 S. Escribe el SVG y su manifiesto con SHA-256 (mismo contenido en dos corridas).
"""
import hashlib
import json
import sys
import zipfile
from pathlib import Path

import pyogrio
import shapely
from shapely.prepared import prep

PASO = 2.0
LAT_N, LAT_S = 76.0, -58.0


def puntos_tierra(zip_ne: Path) -> list[tuple[float, float]]:
    # Lee la capa de tierra dentro del zip sin descomprimir a disco
    with zipfile.ZipFile(zip_ne) as z:
        shp = next(n for n in z.namelist() if n.endswith(".shp"))
    gdf = pyogrio.read_dataframe(f"/vsizip/{zip_ne.as_posix()}/{shp}")
    tierra = prep(shapely.union_all(gdf.geometry.values))
    out = []
    lat = LAT_N
    while lat >= LAT_S:
        lon = -180 + PASO / 2
        while lon < 180:
            if tierra.contains(shapely.Point(lon, lat)):
                out.append((lon, lat))
            lon += PASO
        lat -= PASO
    return out


def svg(puntos: list[tuple[float, float]]) -> str:
    # Coordenadas del lienzo: x = lon + 180, y = 76 - lat; viewBox 360 × 134
    alto = LAT_N - LAT_S
    circulos = "".join(f'<circle cx="{lon + 180:.0f}" cy="{LAT_N - lat:.0f}" r="0.55"/>' for lon, lat in puntos)
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 360 {alto:.0f}" preserveAspectRatio="xMidYMid slice">'
            f'<g fill="#7be0a0">{circulos}</g></svg>\n')


def main(zip_ne: str, salida: str) -> None:
    pts = puntos_tierra(Path(zip_ne))
    texto = svg(pts)
    ruta = Path(salida)
    ruta.write_text(texto, encoding="utf-8", newline="\n")
    sha = hashlib.sha256(texto.encode("utf-8")).hexdigest()
    man = {"archivo": ruta.name, "sha256": sha, "puntos": len(pts), "paso_grados": PASO,
           "fuente": "Natural Earth 1:10m land 5.1.1 (dominio público)", "script": "src/web/herramientas/mapa_puntos.py"}
    ruta.with_suffix(".manifiesto.json").write_text(json.dumps(man, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    print(len(pts), "puntos", sha[:12])


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
