# asistido por SI: Claude Code, control del desfase de longitud de IMERG en las series de Colombia (T-D2)
"""Recalcula 2000-01 y 2015-01 de IMERG Final con la lectura orientada y con la lectura espejada, y compara
contra los csv.gz de Colombia. Uso (WSL): AGRO_COPIA=... python datos/control_desfase_imerg.py SERIES_COL_DIR"""
import gzip
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd

from simulacion.geo import lectura_nasa as L
from simulacion.geo import serie_mensual as S
from simulacion.geo import zonal_mensual as zm

base = Path(os.environ["AGRO_COPIA"])
serie = pd.read_csv(Path(sys.argv[1]) / "serie_mensual_precipitacion_final_area.csv.gz")
u = S.cargar_unidades(str(base / "proc" / "unidades.gpkg"), "COL")
import pyogrio
geoms = np.concatenate([pyogrio.read_dataframe(str(base / "proc" / "unidades.gpkg"), layer=f"adm{n}", where="iso3='COL'",
                        columns=["unidad_id"]).geometry.values for n in (0, 1, 2)])
g = L.GRILLAS["imerg"]
p = zm.calcular_pesos(g, list(geoms))
arch = L.archivos(base / "crudos", "imerg_final")
for mes in ("2000-01", "2015-01"):
    a, _ = L.leer_campo(arch[mes], "imerg_final", int(mes[5:]))
    ref = serie[serie.mes == mes].set_index("unidad_id")["valor"].reindex(u["unidad_id"]).to_numpy()
    for nombre, campo in (("orientada", a), ("espejada_en_longitud", a[:, ::-1])):
        r = zm.agregar(p, g, campo.ravel(), None, S.UMBRAL_FRAC_VALIDA)["valor"]
        d = np.abs(r - ref)
        print(f"{mes} {nombre}: diferencia maxima contra csv.gz = {np.nanmax(d):.3e}, unidades con diferencia > 1e-6: {int((d > 1e-6).sum())} de {len(d)}")
