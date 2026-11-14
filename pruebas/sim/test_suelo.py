# asistido por SI: Claude Code (Anthropic), escritura y revisión de código; base del prototipo migrada en el hackatón
import time
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from simulacion import clima, suelo as sl, vegetacion as vg
from simulacion.clima import cargar_geo
from simulacion.cobertura import cargar_suelo

PRINCIPAL = next((q for q in Path(__file__).resolve().parents if (q / "datos/procesados").exists()), None)
FILAS = [("CB%d" % i, "USA", 41.0 + i * 0.2, 250.0, 25) for i in range(6)]
FILAS += [("AF%d" % i, "COL", 1.0 + i * 0.2, 300.0, 1) for i in range(6)]
GEO = pd.DataFrame(FILAS, columns=["id", "iso3", "punto_lat", "elev_media", "koppen"]).set_index("id")
EST = pd.DataFrame({"silt_0_30": 30.0, "clay_0_30": 25.0, "soc_0_30": 20.0, "bdod_0_30": 1.3,
                    "elev_max": 600.0, "elev_min": 100.0}, index=GEO.index)  # q05/q95 no existen (R6)


@pytest.fixture(scope="module")
def sim():
    c = clima.generar_clima(list(GEO.index), slice(None), geo=GEO)
    nd = vg.generar_ndvi(c, slice(None), GEO)
    igbp, _ = sl.cobertura_igbp(GEO, GEO.koppen)
    return sl.serie_suelo_anual(c, nd, GEO, EST, igbp), igbp


def test_soilgrids_constante(sim):
    serie, _ = sim
    assert np.allclose(np.diff(serie["soc_tier1"], axis=1), 0)  # sin cambio de manejo no hay serie temporal
    assert "ph" not in "".join(serie) and "textura" not in "".join(serie)


def test_soc_sin_saltos():
    s = sl.soc_tier1(np.array([78.0, 78.0]), np.array([0.5, -0.5]), sl.ANIOS)
    cambio = np.diff(s, axis=1)
    assert cambio.min() >= sl.CAMBIO_MIN - 1e-9 and cambio.max() <= sl.CAMBIO_MAX + 1e-9
    saltado = s[0].copy()
    saltado[10:] += 3.0  # caso negativo: salto de 3 t/ha
    assert np.diff(saltado).max() > sl.CAMBIO_MAX


def test_soc_constante_sin_cambio():
    s = sl.soc_tier1(np.array([50.0, 80.0]), np.zeros(2), sl.ANIOS)
    assert np.ptp(s, axis=1).max() == 0


def test_soc_stock_formula():
    assert sl.soc_stock(20, 1.3) == pytest.approx(78.0)


def test_erosion_banda_y_orden(sim):
    serie, igbp = sim
    p05, p50, p95 = serie["erosion_p05"], serie["erosion_p50"], serie["erosion_p95"]
    assert (p05 < p50).all() and (p50 < p95).all()
    assert np.allclose(p95 / p05, sl.FACTOR_BANDA ** 2)
    n = 5
    e = lambda ndvi, ig: sl.erosion_rusle(800.0, 0.2, 1.0, sl.factor_c(np.full(n, ndvi), np.full(n, ig)))["erosion_p50"].mean()
    assert 2 <= e(0.5, 12) <= 40  # cultivos, rango §6.3
    assert e(0.85, 2) < e(0.5, 12)  # bosque por debajo


def test_erosion_no_usa_q05_q95_soilgrids(sim):
    assert "q05" not in EST and "q95" not in EST
    assert np.isfinite(sim[0]["erosion_p50"]).all()


def test_dias_suelo_metodo():
    nd = np.full((3, 12), 0.1)
    assert (sl.dias_suelo_expuesto(nd, None, 2012)[1] == 1).all()
    d, m = sl.dias_suelo_expuesto(nd, np.full((3, 12), 0.3), 2013)
    assert (m == 2).all() and (d == 365).all()
    d, _ = sl.dias_suelo_expuesto(np.full((1, 12), np.nan), None, 2015)
    assert np.isnan(d).all()  # sin dato no es 0


def test_igbp_sin_interpolar(sim):
    _, igbp = sim
    assert igbp.dtype.kind == "i" and igbp.min() >= 1 and igbp.max() <= 17
    _, f = sl.cobertura_igbp(GEO, GEO.koppen)
    assert np.allclose(f.sum(1), 1.0, atol=1e-3)


def test_dias_calor_null_sin_umbral():
    d = sl.dias_calor(np.full((2, 5), 30.0), None)
    assert np.isnan(d).all()


def test_relieve_gmted_rotulado():
    assert all("relieve de GMTED2010" in v.etiqueta for v in sl.VARIABLES_ANUAL.values())


@pytest.mark.datos_reales
def test_colombia_real():
    ruta = PRINCIPAL / "datos/procesados/geo.sqlite"
    geo = cargar_geo(ruta)
    col = geo[geo.iso3 == "COL"]
    est = cargar_suelo(ruta, col.index)
    assert len(est) == len(col)


def test_dias_suelo_mensual_forma():
    nd = np.full((4, 323), 0.1)
    d, m = sl.dias_suelo_mensual(nd, np.full((4, 323), 0.3))
    assert d.shape == m.shape == (4, 323)
    assert (m[:, :159] == 1).all() and (m[:, 159:] == 2).all()  # HLS desde 2013-04 (mes 159)
    assert d[0, 0] == 31 and d[0, 1] == 29  # enero y febrero de 2000
    nd[1] = np.nan
    assert np.isnan(sl.dias_suelo_mensual(nd, None)[0][1]).all()


@pytest.mark.datos_reales
def test_erosion_anclas_borrelli_global():
    from simulacion import config, condicion  # noqa: F401
    import sqlite3
    ruta = PRINCIPAL / "datos/procesados/geo.sqlite.bak_prereconstruccion"
    geo = cargar_geo(ruta)
    ids = geo.sample(2000, random_state=config.SEMILLA).index
    g = geo.loc[ids]
    con = sqlite3.connect(f"file:{ruta.as_posix()}?mode=ro", uri=True)
    d = pd.read_sql("SELECT unidad_id, variable_id, media FROM estatico", con)
    est = d.pivot(index="unidad_id", columns="variable_id", values="media").reindex(ids)
    c = clima.generar_clima(list(ids), slice(None), geo=g)
    nd = vg.generar_ndvi(c, slice(None), g)
    igbp, _ = sl.cobertura_igbp(g, g.koppen, est)
    e = sl.serie_suelo_anual(c, nd, g, est, igbp)["erosion_p50"]
    cult = np.isin(igbp, sl.CULTIVOS)
    bosq = np.isin(igbp, (1, 2, 3, 4, 5))
    assert cult.sum() > 1000 and bosq.sum() > 1000
    for media, ancla in ((np.nanmean(e[cult]), sl.ANCLAS["cultivos"]), (np.nanmean(e[bosq]), sl.ANCLAS["bosque"])):
        assert ancla / 1.5 <= media <= ancla * 1.5, (media, ancla)
