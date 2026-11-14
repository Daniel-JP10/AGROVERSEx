# asistido por SI: Claude Code (Anthropic), escritura y revisión de código; base del prototipo migrada en el hackatón
import hashlib
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse

import requests
import yaml

from simulacion.config import CRUDOS, RAIZ

MANIFIESTO = RAIZ / "datos/manifiesto_descargas.yaml"
OBLIGATORIOS = ("id", "url", "archivo", "licencia", "ficha")


@dataclass(frozen=True)
class Recurso:
    id: str
    url: str
    archivo: str
    licencia: str
    ficha: str
    sha256: str | None
    bytes_esperados: int | None


def cargar_manifiesto(ruta: Path) -> list[Recurso]:
    filas = yaml.safe_load(Path(ruta).read_text(encoding="utf-8")) or []
    recursos, vistos = [], set()
    for fila in filas:
        for campo in OBLIGATORIOS:
            if not str(fila.get(campo) or "").strip():
                raise ValueError(f"campo obligatorio vacío: {campo} en {fila}")
        if fila["id"] in vistos:
            raise ValueError(f"id repetido: {fila['id']}")
        vistos.add(fila["id"])
        if urlparse(fila["url"]).scheme != "https":
            raise ValueError(f"URL no https: {fila['url']}")
        recursos.append(Recurso(
            **{c: fila[c] for c in OBLIGATORIOS},
            sha256=fila.get("sha256"),
            bytes_esperados=fila.get("bytes_esperados"),
        ))
    return recursos


def sha256_archivo(ruta: Path) -> str:
    h = hashlib.sha256()
    with open(ruta, "rb") as f:
        for bloque in iter(lambda: f.read(1 << 20), b""):
            h.update(bloque)
    return h.hexdigest()


def _bajar(url: str, parcial: Path, previo: int) -> None:
    cabeceras = {"Range": f"bytes={previo}-"} if previo else {}
    with requests.get(url, stream=True, headers=cabeceras, timeout=60) as r:
        if r.status_code == 416 or (
            r.status_code == 206
            and not r.headers.get("Content-Range", "").startswith(f"bytes {previo}-")
        ):
            # Range inválido o inconsistente: se empieza de cero
            parcial.unlink(missing_ok=True)
            return _bajar(url, parcial, 0)
        r.raise_for_status()
        with open(parcial, "ab" if r.status_code == 206 else "wb") as f:
            for bloque in r.iter_content(1 << 20):
                f.write(bloque)


def _descargar(recurso: Recurso, destino_dir: Path, esquemas=("https",)) -> Path:
    # esquemas solo se amplía en pruebas con servidor local
    if urlparse(recurso.url).scheme not in esquemas:
        raise ValueError(f"esquema no permitido: {recurso.url}")
    destino_dir = Path(destino_dir)
    destino_dir.mkdir(parents=True, exist_ok=True)
    final = destino_dir / recurso.archivo
    parcial = final.with_name(final.name + ".parcial")
    final.parent.mkdir(parents=True, exist_ok=True)  # archivo puede traer subcarpeta (gmted/...)
    if final.exists():
        if recurso.sha256 and sha256_archivo(final) != recurso.sha256:
            raise ValueError(f"hash distinto en archivo existente: {final}")
        return final
    previo = parcial.stat().st_size if parcial.exists() else 0
    esperado = recurso.bytes_esperados
    if esperado is not None and previo > esperado:
        parcial.unlink()  # parcial más grande que lo esperado: basura
        previo = 0
    if previo and previo == esperado:
        pass  # parcial completo; se valida abajo sin pedir nada
    else:
        _bajar(recurso.url, parcial, previo)
    tam = parcial.stat().st_size
    if recurso.bytes_esperados is not None and tam != recurso.bytes_esperados:
        if tam > recurso.bytes_esperados:
            parcial.unlink()
        raise ValueError(f"bytes {tam} distinto de {recurso.bytes_esperados}")
    if recurso.sha256 and sha256_archivo(parcial) != recurso.sha256:
        parcial.unlink()
        raise ValueError(f"hash distinto en {recurso.id}")
    parcial.replace(final)
    return final


def descargar(recurso: Recurso, destino_dir: Path) -> Path:
    return _descargar(recurso, destino_dir)


def registrar_hash(ruta_manifiesto: Path, id: str, sha256: str) -> None:
    # edición de texto para conservar comentarios del manifiesto
    ruta = Path(ruta_manifiesto)
    bloques = re.split(r"(?m)^(?=- id: )", ruta.read_text(encoding="utf-8"))
    for i, b in enumerate(bloques):
        if re.match(rf"- id: {re.escape(id)}\s*$", b.splitlines()[0] if b else ""):
            bloques[i] = re.sub(r"(?m)^  sha256:.*$", f"  sha256: {sha256}", b)
            ruta.write_text("".join(bloques), encoding="utf-8")
            return
    raise ValueError(f"id no encontrado: {id}")


if __name__ == "__main__":
    por_id = {r.id: r for r in cargar_manifiesto(MANIFIESTO)}
    for id_ in sys.argv[1:] or list(por_id):  # sin argumentos, todo el manifiesto
        if id_ not in por_id:
            sys.exit(f"id desconocido: {id_}. Disponibles: {', '.join(por_id)}")
        r = por_id[id_]
        ruta = descargar(r, CRUDOS)
        h = sha256_archivo(ruta)
        if r.sha256 is None:
            registrar_hash(MANIFIESTO, id_, h)
        print(id_, ruta.stat().st_size, h, flush=True)
