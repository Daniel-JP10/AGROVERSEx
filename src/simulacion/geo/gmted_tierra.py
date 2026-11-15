# asistido por SI: Claude Code (Anthropic), escritura y revisión de código; base del prototipo migrada en el hackatón
from pathlib import Path

import rasterio

from simulacion.config import CRUDOS

ORIGEN = CRUDOS / "gmted_extraido/mn30_grd"
DESTINO = CRUDOS / "gmted_extraido/mn30_tierra.tif"


def crear_tierra(origen: Path = ORIGEN, destino: Path = DESTINO) -> Path:
    # GMTED trae el mar como 0 y no declara NoData (el -32768 declarado no aparece nunca);
    # se copia a GeoTIFF teselado declarando 0 como NoData. Una celda de tierra a 0 m exacto se pierde.
    with rasterio.open(origen) as s:
        perfil = s.profile | {"driver": "GTiff", "nodata": 0, "tiled": True, "blockxsize": 256,
                              "blockysize": 256, "compress": "deflate", "predictor": 2}
        with rasterio.open(destino, "w", **perfil) as d:
            for _, ventana in d.block_windows(1):
                d.write(s.read(1, window=ventana), 1, window=ventana)
    return destino


if __name__ == "__main__":
    print(crear_tierra())
