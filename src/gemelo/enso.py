# asistido por SI: Cursor (agente), escritura y revisión de código; núcleo del gemelo digital en el hackatón
"""Fase ENSO de cada año del registro: El Niño, La Niña o neutra (contrato v1.1).

La clasificación la entrega Datos (archivo `{anio: fase}` en YAML o JSON). Mientras no exista, se deriva del ONI
de NOAA CPC copiado de la rama datos: media de las 12 temporadas del año >= +0,5 °C es El Niño, <= -0,5 °C es
La Niña y el resto neutra. Esa derivación es INFERENCIA (el umbral es el de NOAA, la media anual es nuestra).
"""
import json
from pathlib import Path

import numpy as np
import yaml

from gemelo.procedencia import REFERENCIAS

FASES = ("nino", "nina", "neutra")
UMBRAL_ONI_C = 0.5
AVISO_INTERINO = ("Fase ENSO derivada del ONI de NOAA (±0,5 °C, media del año) como INFERENCIA mientras Datos no "
                  "entrega su clasificación.")


def _leer_archivo(ruta: Path) -> dict[int, str]:
    texto = ruta.read_text(encoding="utf-8")
    datos = json.loads(texto) if ruta.suffix == ".json" else yaml.safe_load(texto)
    if isinstance(datos, dict) and "fases" in datos:
        datos = datos["fases"]
    if isinstance(datos, list):
        datos = {d["anio"]: d["fase"] for d in datos}
    fases = {int(a): str(f) for a, f in datos.items()}
    malas = sorted({f for f in fases.values() if f not in FASES})
    if malas:
        raise ValueError(f"clasificación ENSO {ruta.name}: fases {malas} fuera de {FASES}")
    return fases


def clasificar_oni(archivo: Path | None = None) -> dict[int, str]:
    datos = yaml.safe_load((archivo or REFERENCIAS / "enso.yaml").read_text(encoding="utf-8"))
    fases = {}
    for fila in datos["oni"]:
        v = [x for x in fila["valores"] if x is not None]
        if len(v) < 12:
            continue
        m = float(np.mean(v))
        fases[int(fila["anio"])] = "nino" if m >= UMBRAL_ONI_C else "nina" if m <= -UMBRAL_ONI_C else "neutra"
    return fases


def fases_por_anio(archivo: str | Path | None = None) -> tuple[dict[int, str], dict]:
    """({anio: fase}, metadatos de la clasificación)."""
    if archivo:
        ruta = Path(archivo)
        return _leer_archivo(ruta), {"fuente": f"Datos: {ruta.name}", "etiqueta": "FUENTE", "interina": False}
    return clasificar_oni(), {"fuente": "ONI NOAA CPC (copia de la rama datos, INV-CLI §1.3)",
                              "etiqueta": "INFERENCIA", "interina": True,
                              "regla": f"media anual del ONI >= +{UMBRAL_ONI_C} El Niño, <= -{UMBRAL_ONI_C} La Niña"}
