# asistido por SI: Claude Code (Anthropic), escritura y revisión de código; base del prototipo migrada en el hackatón
import numpy as np
import pandas as pd
import pytest

from simulacion import condicion as cd, suelo as sl
from test_suelo import GEO, sim  # noqa: F401


def test_uno_fuera_todos_fuera():
    # productividad mejora (2), cobertura estable (1), erosión degradada (0)
    assert cd.clasificar_condicion(2, 2, 2, 1, 0, 1) == 0
    assert cd.clasificar_condicion(1, 1, 1, 1, 1, 1) == 1
    assert cd.clasificar_condicion(2, 1, 1, 1, 1, 1) == 2


def test_no_hay_numero_unico():
    c = np.random.default_rng(1).integers(0, 3, (6, 50)).astype(float)
    out = cd.clasificar_condicion(*c)
    assert out.dtype.kind == "i" and set(np.unique(out)) <= {0, 1, 2}


def test_componente_nan_se_ignora():
    assert cd.clasificar_condicion(np.nan, 1, 1, 1, 1, 1) == 1
    assert cd.clasificar_condicion(*[np.nan] * 6) == -1


def test_mann_kendall():
    pend, p = cd.prueba_tendencia(np.arange(20.0))
    assert pend == pytest.approx(1.0) and p < 0.001
    _, p = cd.prueba_tendencia(np.array([1.0, 3, 2, 3, 1, 2, 3, 1, 2, 2]))
    assert p > 0.05


def test_clase_condicion_solo_periodos_2_a_4(sim):  # noqa: F811
    serie, igbp = sim
    df = cd.tabla_anual(list(GEO.index), igbp, serie)
    assert len(df) == len(GEO) * 27
    assert df.loc[df.periodo == 1, "clase_condicion"].isna().all()
    assert df.loc[df.periodo > 1, "clase_condicion"].isin([0, 1, 2]).all()
    assert set(df.periodo.unique()) == {1, 2, 3, 4}


def test_estable_mayoria_y_mejora_minoria():
    # SUPUESTO (INV-SUE no da proporciones): "estable" > 50 % y "mejora" < 30 % en cada periodo
    from simulacion import clima, vegetacion as vg
    filas = [(f"U{i}", "COL", 1.0 + i * 0.15, 200.0 + 40 * i, k) for i, k in enumerate([1, 3, 14, 15, 25] * 12)]
    geo = pd.DataFrame(filas, columns=["id", "iso3", "punto_lat", "elev_media", "koppen"]).set_index("id")
    est = pd.DataFrame({"silt_0_30": 30.0, "clay_0_30": 25.0, "soc_0_30": 20.0, "bdod_0_30": 1.3,
                        "elev_max": 600.0, "elev_min": 100.0}, index=geo.index)
    c = clima.generar_clima(list(geo.index), slice(None), geo=geo)
    igbp, _ = sl.cobertura_igbp(geo, geo.koppen)
    serie = sl.serie_suelo_anual(c, vg.generar_ndvi(c, slice(None), geo), geo, est, igbp)
    df = cd.tabla_anual(list(geo.index), igbp, serie)
    for p in (2, 3, 4):
        f = df[df.periodo == p].clase_condicion.value_counts(normalize=True)
        assert f.get(1, 0) > 0.5 and f.get(2, 0) < 0.3, (p, f.to_dict())
