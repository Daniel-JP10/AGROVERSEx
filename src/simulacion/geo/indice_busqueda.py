# asistido por SI: Claude Code (Anthropic), escritura y revisión de código; base del prototipo migrada en el hackatón
import gzip
import json
import sqlite3
from pathlib import Path

from simulacion.config import CRUDOS, GEO_SQLITE, PROCESADOS
from simulacion.geo.normalizar import normalizar_nombre

SALIDA = PROCESADOS / "indice_busqueda.json.gz"
NE_ADMIN0 = CRUDOS / "ne_10m_admin_0_countries.zip"
# Códigos de GADM/gbOpen que Natural Earth escribe distinto (ADM0_A3)
ALIAS_NE = {"XKO": "KOS", "ZNC": "CYN"}


def nombres_paises(ruta: Path | None = None) -> dict[str, tuple[str, str]]:
    """iso3 de `unidad` -> (NAME_ES, NAME_EN) de Natural Earth admin0 (dominio público). El cruce usa ADM0_A3 y,
    si falta, ISO_A3 e ISO_A3_EH (NE pone -99 en Francia, Noruega y otros); además ALIAS_NE (Kosovo, Chipre del
    Norte). Sin cruce (en NE son parte de otro país o no existen): BES, BVT, CCK, CXR, GLP, GUF, MTQ, MYT, REU,
    SJM, TKL, XAD, XCA, XCL, XPI, XSP; quedan sin es/en y se buscan por su nombre."""
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
    for gadm, ne in ALIAS_NE.items():
        if ne in salida:
            salida[gadm] = salida[ne]
    return salida


def construir_indice(ruta_sqlite: Path, nombres_ne: dict | None = None) -> list[dict]:
    """nombres_ne (ver nombres_paises) completa es y en del nivel 0 donde la base no los trae."""
    con = sqlite3.connect(ruta_sqlite)
    # el nivel 9 (zonas en disputa) tiene polígono en adm0, así que se indexa con ctx "Zona en disputa"
    filas = con.execute(
        "SELECT id, nivel, padre_id, nombre, nombre_ascii, nombre_es, nombre_en, iso3"
        " FROM unidad WHERE nivel IN (0, 1, 2, 9) ORDER BY nivel, id").fetchall()
    con.close()
    nombres = {f[0]: f[3] for f in filas}
    padres = {f[0]: f[2] for f in filas}
    salida = []
    for id_, nivel, padre, nombre, ascii_, es, en, iso3 in filas:
        # cadena de ancestros, del padre inmediato al país
        cadena, p = [], padre
        while p in nombres:
            cadena.append(nombres[p])
            p = padres[p]
        # si la cadena no llega al país (padre NULL, p. ej. ADM2 de gbOpen sin ADM1) se completa por iso3
        if nivel in (1, 2) and iso3 in nombres and (not cadena or cadena[-1] != nombres[iso3]):
            cadena.append(nombres[iso3])
        if nivel == 9:
            cadena = ["Zona en disputa"]
        if nivel == 0 and nombres_ne and iso3 in nombres_ne:
            es, en = es or nombres_ne[iso3][0], en or nombres_ne[iso3][1]
        fila = {"id": id_, "nivel": nivel, "n": nombre,
                "a": normalizar_nombre(ascii_ or nombre), "ctx": " · ".join(cadena)}
        if es:
            fila["es"] = es
        if en:
            fila["en"] = en
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
    filas = construir_indice(GEO_SQLITE, nombres_paises())
    print(f"{len(filas)} filas, {escribir_indice(filas, SALIDA)} bytes -> {SALIDA}")
