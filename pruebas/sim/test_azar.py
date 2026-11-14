# asistido por SI: Claude Code (Anthropic), escritura y revisión de código; base del prototipo migrada en el hackatón
import os
import subprocess
import sys
from pathlib import Path

from simulacion.azar import rng_unidad

SRC = Path(__file__).resolve().parents[2] / "src"

CODIGO = (
    "from simulacion.azar import rng_unidad;"
    "print(repr(rng_unidad('COL.1_1', 't2m').normal()))"
)


def _valor_en_proceso():
    # Un proceso nuevo tiene otro hash() de Python; el resultado debe ser idéntico
    entorno = {**os.environ, "PYTHONPATH": str(SRC)}
    salida = subprocess.run(
        [sys.executable, "-c", CODIGO],
        capture_output=True, text=True, check=True, env=entorno,
    )
    return salida.stdout.strip()


def test_rng_estable_entre_procesos():
    assert _valor_en_proceso() == _valor_en_proceso()


def test_rng_independiente_por_canal():
    a = rng_unidad("COL.1_1", "t2m").normal(size=5)
    b = rng_unidad("COL.1_1", "rh2m").normal(size=5)
    assert not (a == b).all()


def test_rng_repetible_mismo_canal():
    a = rng_unidad("COL.1_1", "t2m").normal(size=5)
    b = rng_unidad("COL.1_1", "t2m").normal(size=5)
    assert (a == b).all()
