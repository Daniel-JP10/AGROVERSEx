# asistido por SI: Claude Code (Anthropic), escritura y revisión de código; base del prototipo migrada en el hackatón
import zipfile
from pathlib import Path

from simulacion.config import CRUDOS, RAIZ

# (zip descargado, carpeta destino): lo que el runbook de docu.md hacía a mano
EXTRACCIONES = [
    (CRUDOS / "gmted/mn30_grd.zip", CRUDOS / "gmted_extraido"),
    (CRUDOS / "koppen/koppen_geiger_tif.zip", CRUDOS / "koppen"),
    (CRUDOS / "go-pmtiles_1.31.2_Windows_x86_64.zip", RAIZ / "herramientas/bin"),
]


def extraer(zip_: Path, destino: Path) -> bool:
    # no vuelve a extraer si la carpeta destino ya tiene contenido; devuelve si extrajo
    destino = Path(destino)
    if destino.exists() and any(destino.iterdir()):
        return False
    destino.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_) as z:
        z.extractall(destino)
    return True


if __name__ == "__main__":
    for z, d in EXTRACCIONES:
        print(z.name, "->", d, "extraido" if extraer(z, d) else "ya estaba")
