# asistido por SI: Claude Code, sensibilidades de Colombia: clases de cultivo 1-3 frente a 1-5 y NDVI con pixel_reliability solo 0 (T-D2)
"""AGRO_COPIA=... python datos/sensibilidad_col.py SALIDA clases(ej 1,2,3) fiable(ej 0,1) variable[,variable]
Corre area y cultivo de Colombia a una carpeta aparte (no toca procesados/series)."""
import os
import sys
from pathlib import Path

import pyogrio

from simulacion.geo import lectura_nasa as L
from simulacion.geo import serie_mensual as S

salida, clases, fiable, variables = Path(sys.argv[1]), {int(x) for x in sys.argv[2].split(",")}, tuple(int(x) for x in sys.argv[3].split(",")), sys.argv[4].split(",")
base = Path(os.environ["AGRO_COPIA"])
gpkg = str(base / "proc" / "unidades.gpkg")
L.FIABLE_ACEPTADA = fiable
b = pyogrio.read_info(gpkg, layer="adm0")  # caja de la capa; se recorta a Colombia abajo
u0 = pyogrio.read_dataframe(gpkg, layer="adm0", where="iso3='COL'", columns=["unidad_id"])
x0, y0, x1, y1 = u0.total_bounds
bbox = (x0 - 1, y0 - 1, x1 + 1, y1 + 1)  # un grado de margen para cubrir las celdas gruesas de borde
cultivo = S.cultivo_desde_gfsad(str(base / "crudos" / "gfsad1kcm" / "GFSAD1KCM.2010.001.2016348142550.tif"), bbox, clases)
S.correr(base / "crudos", gpkg, "COL", salida, ("area", "cultivo"), variables, cultivo)
