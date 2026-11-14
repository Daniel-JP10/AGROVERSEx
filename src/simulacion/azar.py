# asistido por SI: Claude Code (Anthropic), escritura y revisión de código; base del prototipo migrada en el hackatón
import zlib

import numpy as np

from simulacion.config import SEMILLA


def rng_unidad(unidad_id: str, canal: str) -> np.random.Generator:
    # crc32 y no hash(): el hash de str de Python cambia entre procesos
    ss = np.random.SeedSequence(
        [SEMILLA, zlib.crc32(unidad_id.encode()), zlib.crc32(canal.encode())]
    )
    return np.random.default_rng(ss)
