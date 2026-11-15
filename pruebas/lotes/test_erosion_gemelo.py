# asistido por SI: Claude Code, la exposición erosiva de Datos y la del Gemelo coinciden con la misma lluvia POWER y la misma fracción desnuda (director, 20:50)
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from lotes_demo.erosion import exposicion_erosiva
from lotes_demo.forzantes import leer_power_csv

clima = pytest.importorskip("gemelo.clima", reason="requiere el paquete gemelo (integracion, entorno del Gemelo)")
RAIZ = Path(__file__).resolve().parents[2]


def _ruta_power(lote):
    # copia temporal del Gemelo (D-034, P-3) o la ruta de Datos
    for r in (RAIZ / f"datos/lotes/power_{lote}_diario.csv", RAIZ / f"datos/procesados/lotes/{lote}/power_diario.csv"):
        if r.exists():
            return r
    pytest.skip(f"sin power_diario.csv de {lote}")


@pytest.mark.parametrize("lote", ["DEMO-USA-01", "DEMO-COL-01"])
def test_misma_lluvia_y_misma_fraccion_dan_el_mismo_indice(lote):
    ruta = _ruta_power(lote)
    d = leer_power_csv(ruta)
    f = pd.to_datetime([f"{int(y)}-{int(j)}" for y, j in zip(d["YEAR"], d["DOY"])], format="%Y-%j")
    p = np.asarray(d["PRECTOTCORR"], dtype=float)
    g = clima.cargar_power(ruta)
    pg = np.asarray(g.datos["precip"], dtype=float).ravel()
    fg = pd.DatetimeIndex([x for a in g.anios for x in pd.date_range(f"{a}-01-01", f"{a}-12-31") if not (x.month == 2 and x.day == 29)])
    # el Gemelo quita el 29 de febrero (calendario nominal): sin esos días las dos series son la misma
    sin29 = ~((f.month == 2) & (f.day == 29))
    assert np.array_equal(p[sin29], pg)
    for frac in (1.0, 0.4):
        a = exposicion_erosiva(p[sin29], f[sin29], desnudo=np.full(sin29.sum(), frac))
        b = exposicion_erosiva(pg, fg, desnudo=np.full(pg.size, frac))
        assert a["indice_exposicion_erosiva"] == b["indice_exposicion_erosiva"]
    # con el calendario completo de Datos la diferencia queda por debajo de 0,1 %
    c = exposicion_erosiva(p, f, desnudo=np.ones(len(p)))["indice_exposicion_erosiva"]
    b1 = exposicion_erosiva(pg, fg, desnudo=np.ones(pg.size))["indice_exposicion_erosiva"]
    assert abs(c / b1 - 1) < 0.001
