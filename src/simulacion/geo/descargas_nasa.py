# asistido por SI: Claude Code (Anthropic), descarga con subconjunto por variable vía OPeNDAP de Earthdata (T-D3)
import json
import os
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from urllib.parse import quote

from simulacion.geo.descargas import sha256_archivo

DATOS = Path(os.environ.get("AGRO_DATOS", "datos"))
FIRMA_HDF5 = b"\x89HDF\r\n\x1a\n"  # netCDF4 es HDF5; un error HTML con código 200 no la trae
OPENDAP = "https://opendap.earthdata.nasa.gov/collections/{cid}/granules/{ur}"

# Producto -> colección CMR y rutas DAP4 de las variables (verificadas en el .dmr del granulo)
PRODUCTOS = {
    "mod13c2": dict(
        cid="C2565788914-LPCLOUD", short_name="MOD13C2", version="061", desde="2000-01-01",
        variables=[
            "/MOD_Grid_monthly_CMG_VI/Data_Fields/CMG_0_05_Deg_Monthly_NDVI",
            "/MOD_Grid_monthly_CMG_VI/Data_Fields/CMG_0_05_Deg_Monthly_pixel_reliability",
        ],
    ),
}


def url_dap4(base: str, variables: list[str]) -> str:
    # los ';' separan variables y las '/' son la ruta del grupo: no se codifican
    return f"{base}.dap.nc4?dap4.ce=" + quote(";".join(variables), safe="/;")


class RegistroHashes:
    """Un solo escritor del registro: el candado evita líneas mezcladas entre hilos."""

    def __init__(self, ruta: Path):
        self.ruta, self._candado = Path(ruta), threading.Lock()
        self.ruta.parent.mkdir(parents=True, exist_ok=True)

    def anotar(self, id: str, bytes_: int, sha256: str) -> None:
        with self._candado, open(self.ruta, "a", encoding="utf-8") as f:
            f.write(json.dumps({"id": id, "bytes": bytes_, "sha256": sha256}) + "\n")


def bajar_subconjunto(sesion, url: str, final: Path, reintentos: int = 12, espera: float = 2.0):
    # shortcut: la respuesta de subconjunto es dinámica y sin Range; reanuda por archivo, no por byte
    final = Path(final)
    if final.exists():
        return final.stat().st_size, sha256_archivo(final)
    final.parent.mkdir(parents=True, exist_ok=True)
    parcial = final.with_name(final.name + ".parcial")
    ultimo = None
    for i in range(reintentos):
        try:
            with sesion.get(url, stream=True, timeout=600) as r:
                r.raise_for_status()
                with open(parcial, "wb") as f:
                    for bloque in r.iter_content(1 << 20):
                        f.write(bloque)
            with open(parcial, "rb") as f:
                if f.read(8) != FIRMA_HDF5:
                    raise RuntimeError("el cuerpo no es netCDF4/HDF5")
            parcial.replace(final)
            return final.stat().st_size, sha256_archivo(final)
        except Exception as e:  # noqa: BLE001 - se reintenta cualquier falla de red o de servicio
            ultimo = e
            parcial.unlink(missing_ok=True)
            time.sleep(min(60, espera * 2**i))
    raise RuntimeError(f"agotados {reintentos} intentos en {url}: {ultimo}")


def granulos(producto: str):
    import earthaccess  # import tardío: las pruebas no lo necesitan
    p = PRODUCTOS[producto]
    earthaccess.login(strategy="netrc")
    gs = earthaccess.search_data(short_name=p["short_name"], version=p["version"],
                                 temporal=(p["desde"], None))
    return sorted(g["umm"]["GranuleUR"] for g in gs), p


def principal(producto: str, hilos: int, limite: int | None):
    import earthaccess
    import yaml
    urs, p = granulos(producto)
    urs = urs[:limite] if limite else urs
    sesion = earthaccess.get_requests_https_session()
    reg = RegistroHashes(DATOS / "crudos/registros" / f"hashes_{producto}.jsonl")
    filas = []
    for ur in urs:
        base = OPENDAP.format(cid=p["cid"], ur=ur)
        filas.append(dict(id=f"{producto}_{ur}", url=url_dap4(base, p["variables"]),
                          archivo=f"{producto}/{ur}.nc4", licencia="PENDIENTE", ficha=f"datos/fichas/{producto}.md"))
    man = DATOS / f"manifiesto_{producto}.yaml"
    man.write_text("# consulta exacta por granulo; hashes en crudos/registros/hashes_*.jsonl\n"
                   + yaml.safe_dump(filas, allow_unicode=True, sort_keys=False), encoding="utf-8")

    def uno(f):
        t = time.time()
        n, h = bajar_subconjunto(sesion, f["url"], DATOS / "crudos" / f["archivo"])
        reg.anotar(f["id"], n, h)
        print(f["id"], n, h, round(time.time() - t, 1), flush=True)

    with ThreadPoolExecutor(hilos) as ex:
        list(ex.map(uno, filas))


if __name__ == "__main__":
    # uso: python -m simulacion.geo.descargas_nasa mod13c2 [hilos] [limite]
    if sys.argv[1] not in PRODUCTOS:
        sys.exit(f"producto desconocido. Disponibles: {', '.join(PRODUCTOS)}")
    principal(sys.argv[1], int(sys.argv[2]) if len(sys.argv) > 2 else 1,
              int(sys.argv[3]) if len(sys.argv) > 3 else None)
