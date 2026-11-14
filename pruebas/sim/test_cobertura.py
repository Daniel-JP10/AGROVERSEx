# asistido por SI: Claude Code (Anthropic), escritura y revisión de código; base del prototipo migrada en el hackatón
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from simulacion import cobertura as cb
from simulacion.clima import cargar_geo

PRINCIPAL = next((q for q in Path(__file__).resolve().parents if (q / "datos/procesados").exists()), None)
# koppen 1..30: Af=1, Aw=3, BWh=4, Cfb=15, Dfa=25, ET=29, EF=30
FILAS = [("EF1", "ATA", -80.0, 2500.0, 30), ("DES1", "EGY", 25.0, 200.0, 4), ("AF1", "BRA", -3.0, 80.0, 1),
         ("PAR1", "COL", 4.6, 4000.0, 29), ("PAR2", "COL", 4.6, 3700.0, 15), ("AF2", "COL", 1.0, 300.0, 1),
         ("CB1", "USA", 41.0, 250.0, 25), ("SIN1", "FRA", 45.0, 100.0, -1)]
GEO = pd.DataFrame(FILAS, columns=["id", "iso3", "punto_lat", "elev_media", "koppen"]).set_index("id")


def _cob(geo=GEO, est=None):
    return cb.cobertura_simulada(geo, geo.koppen, est)


def test_fracciones_suman_uno():
    c = _cob()
    f = c[cb.COLS]
    assert f.shape[1] == 17 and (f >= 0).all().all()
    assert np.allclose(f.sum(axis=1), 1.0)
    assert (c.igbp_dominante == f.to_numpy().argmax(1) + 1).all()


def test_reglas_de_clima():
    d = _cob().igbp_dominante
    assert d["EF1"] == 15 and d["DES1"] == 16
    assert d["AF1"] == 2 and d["AF2"] == 2
    assert d["CB1"] in (12, 14)
    assert d["PAR1"] != 2 and d["PAR2"] != 2  # sin bosque tropical sobre 3.500 m
    assert d["SIN1"] > 0  # sin Köppen: respaldo


def test_suelo_modula_cultivo():
    bueno = pd.DataFrame({"phh2o": 6.5, "clay": 25.0, "sand": 40.0}, index=GEO.index)
    malo = pd.DataFrame({"phh2o": 3.5, "clay": 80.0, "sand": 5.0}, index=GEO.index)
    assert _cob(est=bueno).loc["CB1", "igbp_12"] > _cob(est=malo).loc["CB1", "igbp_12"]


def test_determinista_por_unidad():
    a = _cob()
    b = _cob(GEO.iloc[::-1])
    assert np.allclose(a.loc[b.index].drop(columns="igbp_dominante").to_numpy(),
                       b.drop(columns="igbp_dominante").to_numpy())


@pytest.mark.datos_reales
def test_cobertura_real_colombia():
    geo = cargar_geo(PRINCIPAL / "datos/procesados/geo.sqlite")
    col = geo[geo.iso3 == "COL"]
    est = cb.cargar_suelo(PRINCIPAL / "datos/procesados/geo.sqlite", col.index)
    c = cb.cobertura_simulada(col, col.koppen, est)
    alto = (col.elev_media > 3500).to_numpy()
    assert alto.any() and not (c.igbp_dominante.to_numpy()[alto] == 2).any()
    assert np.allclose(c[cb.COLS].sum(axis=1), 1.0)
    efs = (col.koppen == 30).to_numpy()
    assert not (c.igbp_dominante.to_numpy()[efs] == 12).any()
