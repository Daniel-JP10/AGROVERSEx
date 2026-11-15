# asistido por SI: Claude Code (Anthropic), índice de búsqueda sobre unidades CGAZ y nombres de Natural Earth (T-D1)
import gzip
import json
from pathlib import Path

import pandas as pd
import pyogrio

from simulacion.config import CRUDOS, PROCESADOS
from simulacion.geo.normalizar import normalizar_nombre

SALIDA = PROCESADOS / "indice_busqueda.json.gz"
NE_ADMIN0 = CRUDOS / "natural_earth/ne_10m_admin_0_countries.zip"
# Códigos de CGAZ que Natural Earth escribe distinto (ADM0_A3)
ALIAS_NE = {"XKX": "KOS"}


def nombres_paises(ruta: Path | None = None) -> dict[str, tuple[str, str]]:
    """iso3 de CGAZ -> (NAME_ES, NAME_EN) de Natural Earth admin0 (dominio público). El cruce usa ADM0_A3 y,
    si falta, ISO_A3 e ISO_A3_EH (NE pone -99 en Francia, Noruega y otros); además ALIAS_NE (Kosovo).
    Los países de CGAZ sin cruce quedan sin es/en y se buscan por su nombre de CGAZ."""
    import pyogrio
    ruta = Path(ruta or NE_ADMIN0)
    if not ruta.exists():
        return {}
    df = pyogrio.read_dataframe(f"zip://{ruta.as_posix()}", read_geometry=False,
                                columns=["ADM0_A3", "ISO_A3", "ISO_A3_EH", "NAME_ES", "NAME_EN"])
    salida = {}
    for col in ("ISO_A3_EH", "ISO_A3", "ADM0_A3"):  # la última escritura gana: ADM0_A3 manda
        for r in df.itertuples():
            k = getattr(r, col)
            if k and k != "-99" and r.NAME_ES and r.NAME_EN:
                salida[k] = (r.NAME_ES, r.NAME_EN)
    for cgaz, ne in ALIAS_NE.items():
        if ne in salida:
            salida[cgaz] = salida[ne]
    return salida


def leer_atributos(ruta_gpkg: Path) -> pd.DataFrame:
    # solo atributos de las tres capas, sin geometría
    return pd.concat([pyogrio.read_dataframe(ruta_gpkg, layer=f"adm{n}", read_geometry=False,
                                             columns=["unidad_id", "nivel", "iso3", "padre_id", "nombre",
                                                      "nombre_ascii", "es_disputa", "nivel_real"]) for n in (0, 1, 2)],
                     ignore_index=True)


def construir_indice(unidades: pd.DataFrame, nombres_ne: dict | None = None) -> list[dict]:
    """nombres_ne (ver nombres_paises) pone es y en en el nivel 0; el resto de niveles no los trae CGAZ."""
    # no se indexan las filas que repiten un nivel superior (ADM2 sin municipios) ni las disputas de ADM1 y ADM2
    propias = (unidades["nivel_real"] == "ADM" + unidades["nivel"].astype(str)) | ((unidades["nivel"] == 0) & (unidades["es_disputa"] == 1))
    filas = unidades[propias].sort_values(["nivel", "unidad_id"], kind="stable")
    nombres = dict(zip(filas["unidad_id"], filas["nombre"]))
    padres = dict(zip(filas["unidad_id"], filas["padre_id"]))
    pais = {r.iso3: r.nombre for r in filas.itertuples() if r.nivel == 0}
    salida = []
    for r in filas.itertuples():
        # cadena de ancestros, del padre inmediato al país
        cadena, p = [], r.padre_id
        while p in nombres:
            cadena.append(nombres[p])
            p = padres[p]
        # si la cadena no llega al país (padre nulo) se completa por iso3
        if r.nivel in (1, 2) and r.iso3 in pais and (not cadena or cadena[-1] != pais[r.iso3]):
            cadena.append(pais[r.iso3])
        if r.es_disputa:
            cadena = ["Zona en disputa"]
        fila = {"id": r.unidad_id, "nivel": int(r.nivel), "n": r.nombre,
                "a": normalizar_nombre(r.nombre_ascii or r.nombre), "ctx": " · ".join(cadena)}
        if r.es_disputa:
            fila["d"] = 1
        if r.nivel == 0 and nombres_ne and r.iso3 in nombres_ne:
            fila["es"], fila["en"] = nombres_ne[r.iso3]
        salida.append(fila)
    return salida


def escribir_indice(filas: list[dict], ruta: Path) -> int:
    ruta = Path(ruta)
    ruta.parent.mkdir(parents=True, exist_ok=True)
    datos = json.dumps(filas, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    # mtime=0 para que el archivo sea reproducible byte a byte
    ruta.write_bytes(gzip.compress(datos, mtime=0))
    return ruta.stat().st_size


if __name__ == "__main__":
    filas = construir_indice(leer_atributos(PROCESADOS / "unidades.gpkg"), nombres_paises())
    print(f"{len(filas)} filas, {escribir_indice(filas, SALIDA)} bytes -> {SALIDA}")
