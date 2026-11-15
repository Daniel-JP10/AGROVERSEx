# asistido por SI: Claude Code (Anthropic), descarga el CSV de una estación GHCN-Daily a C:/NASA/compartir/ghcn sin versionarlo (D-038)
"""Baja el CSV por estación de NOAA NCEI fuera del repositorio, para reproducir el resumen derivado sin redistribuirlo.

Uso: python -m lotes_demo.descargar_ghcn [estacion] [carpeta]
NCEI actualiza el archivo cada día: su SHA256 cambia; el resumen se limita al periodo declarado (2001-2024).
"""
import hashlib
import sys
import urllib.request
from pathlib import Path

URL = "https://www.ncei.noaa.gov/data/global-historical-climatology-network-daily/access/{}.csv"
CARPETA = Path("C:/NASA/compartir/ghcn")
# SHA256 de la copia usada en el resumen versionado (ficha datos/fichas/ghcn_daily.md)
SHA_REFERENCIA = {"COM00080370": "b2dca61c6f63748daa21bf876815b402e6c2f60ed9710f302202152db93f94b5"}


def descargar(estacion: str = "COM00080370", carpeta: Path = CARPETA) -> Path:
    destino = carpeta / f"{estacion}.csv"
    if destino.resolve().is_relative_to(Path(__file__).resolve().parents[2]):
        raise ValueError("el CSV de GHCN no se guarda dentro del repositorio (D-038)")
    carpeta.mkdir(parents=True, exist_ok=True)
    with urllib.request.urlopen(URL.format(estacion), timeout=120) as r:
        destino.write_bytes(r.read())
    sha = hashlib.sha256(destino.read_bytes()).hexdigest()
    ref = SHA_REFERENCIA.get(estacion)
    print(f"{destino} sha256={sha}" + ("" if sha == ref else f" (distinto de la referencia {ref}: archivo actualizado por NCEI)"))
    return destino


if __name__ == "__main__":
    descargar(*(sys.argv[1:2] or ["COM00080370"]), *(Path(x) for x in sys.argv[2:3]))
