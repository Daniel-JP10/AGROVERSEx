# asistido por SI: Claude Code (Anthropic), escritura y revisión de código; base del prototipo migrada en el hackatón
import re
import subprocess
import sys
import time
from pathlib import Path

from simulacion.config import PROCESADOS, RAIZ

HERRAMIENTAS = RAIZ / "herramientas"
CRUDOS_GEOJSON = PROCESADOS / "limites_crudos"
SIMPLIFICADOS = PROCESADOS / "limites_simplificados"
TESELAS = PROCESADOS / "teselas"
# SUPUESTO: medidos en la tarea 3, paso 8
PORCENTAJE = 10
ZOOMS = {0: (0, 6), 1: (2, 9), 2: (5, 12)}
WSL_TMP = "~/tmp"
# por encima de este tamaño mapshaper necesita ~5x en RAM (medido con ADM0): se parte por país
MAX_ENTRADA = 1_400_000_000
MAX_PARTE = 1_000_000_000
_ISO = re.compile(rb'"iso3"\s*:\s*"([^"]+)"')
_ID = re.compile(rb'"id"\s*:\s*"([^"]+)"')


def comando_mapshaper(entradas: list[Path], dir_salida: Path, porcentaje: float) -> list[str]:
    bin_ = f"{HERRAMIENTAS.as_posix()}/node_modules/mapshaper/bin/mapshaper-xl"
    return ["node", bin_, "16gb", "-i", "combine-files", *map(str, entradas), "snap",
            "-simplify", f"{porcentaje}%", "keep-shapes", "-clean",
            "-o", f"{dir_salida}/", "format=geojson"]


def comando_tippecanoe(entrada_wsl: str, salida_wsl: str, capa: str, zmin: int, zmax: int) -> list[str]:
    return ["wsl", "-d", "Ubuntu-24.04", "--", "tippecanoe", "-o", salida_wsl, "--force",
            "-l", capa, "-Z", str(zmin), "-z", str(zmax),
            "--no-simplification-of-shared-nodes", "--no-tiny-polygon-reduction",
            "--no-feature-limit", "--no-tile-size-limit", entrada_wsl]


def ruta_wsl(p: Path) -> str:
    p = Path(p)
    return f"/mnt/{p.drive[0].lower()}/" + "/".join(p.parts[1:])


def contar_ids(ruta_geojson: Path) -> set[str]:
    # lectura por bloques: los GeoJSON pesan GB y no caben cargados como JSON
    ids, resto = set(), b""
    with open(ruta_geojson, "rb") as f:
        while bloque := f.read(1 << 24):
            datos = resto + bloque
            # la cola sin procesar cubre un id partido entre bloques
            corte = max(len(datos) - 200, 0)
            for m in _ID.finditer(datos[:corte]):
                ids.add(m.group(1).decode())
            resto = datos[corte:]
    ids.update(m.group(1).decode() for m in _ID.finditer(resto))
    return ids


def partir_por_pais(ruta: Path, dir_salida: Path, max_bytes: int = MAX_PARTE) -> list[Path]:
    # los GeoJSON de la tarea 2 traen un feature por línea; los países no se parten
    dir_salida.mkdir(parents=True, exist_ok=True)
    partes, f_out, tam, iso_prev = [], None, 0, None
    with open(ruta, "rb") as f:
        for linea in f:
            if not linea.startswith(b'{ "type": "Feature"'):
                continue
            iso = _ISO.search(linea).group(1)
            if f_out is None or (iso != iso_prev and tam >= max_bytes):
                if f_out:
                    f_out.write(b"\n]}\n")
                    f_out.close()
                partes.append(dir_salida / f"{ruta.stem}_p{len(partes) + 1:02d}.geojson")
                f_out, tam = open(partes[-1], "wb"), 0
                f_out.write(b'{"type":"FeatureCollection","features":[\n')
            else:
                f_out.write(b",\n")
            f_out.write(linea.rstrip().rstrip(b","))
            tam += len(linea)
            iso_prev = iso
    f_out.write(b"\n]}\n")
    f_out.close()
    return partes


def unir_geojson(partes: list[Path], destino: Path) -> None:
    with open(destino, "wb") as out:
        out.write(b'{"type":"FeatureCollection","features":[\n')
        primero = True
        for p in partes:
            with open(p, "rb") as f:
                for linea in f:
                    if linea.startswith(b'{"type":"Feature"'):
                        out.write(b"" if primero else b",\n")
                        out.write(linea.rstrip().rstrip(b","))
                        primero = False
        out.write(b"\n]}\n")


def completar_perdidos(crudo: Path, simple: Path) -> int:
    # -clean de mapshaper borra unidades diminutas; se reponen del crudo (sin simplificar)
    faltan = contar_ids(crudo) - contar_ids(simple)
    if not faltan:
        return 0
    lineas = []
    with open(crudo, "rb") as f:
        for linea in f:
            m = _ID.search(linea) if linea.startswith(b'{ "type": "Feature"') else None
            if m and m.group(1).decode() in faltan:
                lineas.append(linea.rstrip().rstrip(b","))
    with open(simple, "r+b") as f:
        f.seek(-4, 2)
        assert f.read(4) == b"\n]}\n"
        f.seek(-4, 2)
        f.write(b",\n" + b",\n".join(lineas) + b"\n]}\n")
    return len(lineas)


def _correr(cmd: list[str], log) -> None:
    t = time.time()
    log.write(f"$ {' '.join(cmd)}\n")
    log.flush()
    subprocess.run(cmd, check=True, stdout=log, stderr=subprocess.STDOUT)
    log.write(f"# {time.time() - t:.0f} s\n")
    log.flush()


def simplificado_vigente(crudo: Path, final: Path) -> bool:
    # un simplificado más viejo que el crudo viene de otra reconstrucción de unidades: se rehace
    return final.exists() and final.stat().st_mtime > crudo.stat().st_mtime


def _simplificar(capa: str, log) -> Path:
    crudo = CRUDOS_GEOJSON / f"{capa}.geojson"
    final = SIMPLIFICADOS / f"{capa}.geojson"
    if simplificado_vigente(crudo, final):
        completar_perdidos(crudo, final)
        return final
    final.unlink(missing_ok=True)
    if crudo.stat().st_size <= MAX_ENTRADA:
        entradas = [crudo]
    else:
        # shortcut: partir por país deja las fronteras internacionales sin simplificar en común
        entradas = partir_por_pais(crudo, SIMPLIFICADOS / f"{capa}_partes", MAX_PARTE)
    salidas = []
    for e in entradas:
        _correr(comando_mapshaper([e], SIMPLIFICADOS, PORCENTAJE), log)
        # mapshaper escribe .json aunque la entrada sea .geojson
        salidas.append((SIMPLIFICADOS / f"{e.stem}.json").replace(SIMPLIFICADOS / f"{e.stem}.geojson"))
    if entradas != [crudo]:
        unir_geojson(salidas, final)
        for e, s in zip(entradas, salidas):
            e.unlink()
            s.unlink()
        (SIMPLIFICADOS / f"{capa}_partes").rmdir()
    else:
        salidas[0].replace(final)
    completar_perdidos(crudo, final)
    return final


def _wsl(script: str, log) -> None:
    _correr(["wsl", "-d", "Ubuntu-24.04", "--", "bash", "-c", script], log)


def construir_teselas(niveles=(0, 1, 2)) -> dict[str, Path]:
    SIMPLIFICADOS.mkdir(parents=True, exist_ok=True)
    TESELAS.mkdir(parents=True, exist_ok=True)
    salida = {}
    with open(TESELAS / "construccion.log", "a", encoding="utf-8") as log:
        for n in niveles:
            capa = f"adm{n}"
            simple = _simplificar(capa, log)
            # tippecanoe lee lento desde /mnt/c: se trabaja en el disco de WSL
            wsl_in, wsl_out = f"{WSL_TMP}/{capa}.geojson", f"{WSL_TMP}/{capa}.pmtiles"
            destino = TESELAS / f"{capa}.pmtiles"
            _wsl(f"mkdir -p {WSL_TMP} && cp '{ruta_wsl(simple)}' {wsl_in}", log)
            _correr(comando_tippecanoe(wsl_in, wsl_out, capa, *ZOOMS[n]), log)
            _wsl(f"cp {wsl_out} '{ruta_wsl(destino)}' && rm {wsl_in} {wsl_out}", log)
            salida[capa] = destino
    return salida


if __name__ == "__main__":
    print(construir_teselas(tuple(int(a) for a in sys.argv[1:]) or (0, 1, 2)))
