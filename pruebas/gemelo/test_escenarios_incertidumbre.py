# asistido por SI: Cursor (agente), escritura y revisión de código; núcleo del gemelo digital en el hackatón
import numpy as np
import pytest

from gemelo.escenarios import AVISO_HIPOTETICO, construir, series
from gemelo.incertidumbre import cvar, muestrear, resumir
from gemelo.procedencia import Parametro


def test_escenarios_ordenados_por_lluvia(clima_ames):
    p = {}
    for tipo in ("seco", "normal", "humedo"):
        esc = construir(clima_ames, tipo, 2, semilla=1)
        assert esc.aviso == AVISO_HIPOTETICO
        sel = clima_ames.precip_anual()[np.array(esc.miembros)]
        p[tipo] = sel.mean()
    assert p["seco"] < p["normal"] < p["humedo"]


def test_historico_ventanas_y_personalizado(clima_ames):
    esc = construir(clima_ames, "historico", 3)
    assert esc.n_miembros == clima_ames.n_anios - 2
    assert all(m[1] == m[0] + 1 for m in esc.miembros)
    base, _ = series(clima_ames, construir(clima_ames, "historico", 1, anio_inicio=2010))
    mas, _ = series(clima_ames, construir(clima_ames, "personalizado", 1, anio_inicio=2010, delta_precip_pct=-20,
                                          delta_temp_c=2.0))
    assert mas["precip"].sum() == pytest.approx(0.8 * base["precip"].sum())
    assert np.all(mas["et0"] >= base["et0"] - 1e-9)
    with pytest.raises(ValueError):
        construir(clima_ames, "historico", 1, delta_temp_c=1.0)
    with pytest.raises(ValueError):
        construir(clima_ames, "historico", 99)


def test_muestreo_lhs():
    params = {"a": Parametro("a", 0.5, "-", "SUPUESTO", rango=(0.0, 1.0)),
              "b": Parametro("b", 10.0, "-", "SUPUESTO", rango=(5.0, 20.0), distribucion="triangular"),
              "c": Parametro("c", 3.0, "-", "FUENTE")}
    m = muestrear(params, 50, semilla=3)
    assert m["a"][0] == 0.5 and m["b"][0] == 10.0
    assert np.all(m["c"] == 3.0)
    assert m["a"].min() >= 0 and m["a"].max() <= 1 and m["b"].min() >= 5 and m["b"].max() <= 20
    # LHS: un punto por estrato (sin contar el central)
    estratos = np.floor(m["a"][1:] * 49).astype(int)
    assert len(np.unique(estratos)) >= 45
    np.testing.assert_array_equal(muestrear(params, 50, 3)["a"], m["a"])


def test_resumen_y_cvar():
    v = np.arange(1, 101, dtype=float)
    r = resumir(v)
    assert r["p10"] < r["p50"] < r["p90"] and r["p50"] == pytest.approx(50.5)
    assert cvar(v, 0.9) == pytest.approx(np.mean(v[v >= np.quantile(v, 0.9)]))
