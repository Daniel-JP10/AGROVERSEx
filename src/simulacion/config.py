# asistido por SI: Claude Code (Anthropic), variable AGRO_DATOS para la ruta de datos (T-D1)
import os
from datetime import date
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
# AGRO_DATOS apunta los datos pesados fuera del repo (sin ella, datos/ junto al repo)
DATOS = Path(os.environ.get("AGRO_DATOS", RAIZ / "datos"))
CRUDOS = DATOS / "crudos"
PROCESADOS = DATOS / "procesados"
FICHAS = RAIZ / "datos/fichas"

# Mollweide para áreas, WGS84 para coordenadas de salida
CRS_AREA = "ESRI:54009"
CRS_SALIDA = "EPSG:4326"

SEMILLA = 20261108
GEO_SQLITE = PROCESADOS / "geo.sqlite"
# Respaldo mientras geo.sqlite se reconstruye (Köppen y latitudes no cambian)
GEO_SQLITE_RESPALDO = PROCESADOS / "geo.sqlite.bak_prereconstruccion"
AGROVERSEX_SQLITE = PROCESADOS / "agroversex.sqlite"

# Periodo de 323 meses en UTC, de ene-2000 a nov-2026 (INICIAR §5.1)
N_MESES = 323
FECHA_INICIO = date(2000, 1, 1)
# PENDIENTE: se fija con la consulta real de POWER en la tarea 13; 2026-11-05 es aproximado (INICIAR, tabla de POWER)
FECHA_FIN_DIARIA = date(2026, 11, 5)

