# asistido por SI: Claude Code (Anthropic), arma la carpeta del release del dataset abierto y verifica sha256 (D-044)
"""Arma la carpeta plana del release a partir de herramientas/dataset_lista.json.

Uso:
  python herramientas/armar_release_dataset.py --datos C:/NASA/AGROVERSEx/datos/procesados/series_mundo --salida C:/NASA/release_dataset
Solo biblioteca estándar. Sale con código 1 si falta un archivo o no coincide su tamaño o su sha256.
"""
import argparse
import hashlib
import json
import shutil
import sys
from pathlib import Path

RAIZ_REPO = Path(__file__).resolve().parent.parent
LISTA = RAIZ_REPO / "herramientas" / "dataset_lista.json"
# Documentos que acompañan al release, sin huella porque cambian con cada edición
DOCUMENTOS = ["DATASET.md", "LICENSE-DATA.md"]


def sha256(ruta):
    # Lectura por bloques: las series pesan cientos de MB
    h = hashlib.sha256()
    with open(ruta, "rb") as f:
        for bloque in iter(lambda: f.read(1 << 20), b""):
            h.update(bloque)
    return h.hexdigest()


def armar(lista, datos, salida, repo=RAIZ_REPO):
    """Copia cada archivo a salida con su nombre plano; devuelve la lista de errores."""
    raices = {"datos": Path(datos), "repo": Path(repo)}
    salida = Path(salida)
    salida.mkdir(parents=True, exist_ok=True)
    errores = []
    nombres = set()
    for a in lista["archivos"]:
        # Los assets de un release de GitHub son planos: un nombre repetido pisaría otro archivo
        if a["nombre"] in nombres:
            errores.append(f"nombre repetido: {a['nombre']}")
            continue
        nombres.add(a["nombre"])
        origen = raices[a["raiz"]] / a["ruta"]
        if not origen.is_file():
            errores.append(f"falta: {origen}")
            continue
        if origen.stat().st_size != a["bytes"]:
            errores.append(f"tamaño distinto: {origen}")
            continue
        destino = salida / a["nombre"]
        shutil.copy2(origen, destino)
        # Se verifica la copia, no el origen, para detectar fallas de escritura
        if sha256(destino) != a["sha256"]:
            destino.unlink()
            errores.append(f"sha256 distinto: {origen}")
    for doc in DOCUMENTOS:
        if (Path(repo) / doc).is_file():
            shutil.copy2(Path(repo) / doc, salida / doc)
    # SHA256SUMS para que cualquiera compruebe la descarga con sha256sum -c
    if not errores:
        lineas = [f"{a['sha256']}  {a['nombre']}\n" for a in lista["archivos"]]
        (salida / "SHA256SUMS.txt").write_text("".join(lineas), encoding="utf-8", newline="\n")
    return errores


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--datos", required=True, help="carpeta series_mundo (AGROVERSEX_DATOS/series_mundo)")
    p.add_argument("--salida", required=True, help="carpeta nueva del release")
    p.add_argument("--lista", default=str(LISTA))
    args = p.parse_args(argv)
    lista = json.loads(Path(args.lista).read_text(encoding="utf-8"))
    errores = armar(lista, args.datos, args.salida)
    for e in errores:
        print("ERROR", e, file=sys.stderr)
    print(f"{len(lista['archivos']) - len(errores)} de {len(lista['archivos'])} archivos verificados")
    return 1 if errores else 0


if __name__ == "__main__":
    sys.exit(main())
