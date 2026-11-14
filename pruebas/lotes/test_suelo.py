# asistido por SI: Claude Code, pruebas de parametros_suelo.json (T-D5 Parte B)
import json
from pathlib import Path

import pytest

from lotes_demo.suelo import media_ponderada, parametros_desde_rest

RAIZ = Path("C:/NASA/AGROVERSEx/datos/procesados/lotes")


def _capa(vals):
    # vals: lista de (tope, fondo, valor)
    return {"depths": [{"range": {"top_depth": t, "bottom_depth": b}, "values": {"mean": v}} for t, b, v in vals]}


def test_media_ponderada_por_espesor():
    c = _capa([(0, 5, 100), (5, 15, 200), (15, 30, 300)])
    # (5*100 + 10*200 + 15*300) / 30
    assert media_ponderada(c, "mean", 30) == pytest.approx(7000 / 30)


def test_media_ponderada_corta_en_el_tope():
    c = _capa([(0, 5, 100), (5, 15, 200)])
    assert media_ponderada(c, "mean", 10) == pytest.approx((500 + 1000) / 10)


@pytest.mark.parametrize("lote", ["DEMO-USA-01", "DEMO-COL-01"])
def test_parametros_reales(lote):
    p = RAIZ / lote / "soilgrids_rest.json"
    if not p.exists():
        pytest.skip("sin descarga")
    r = parametros_desde_rest(json.loads(p.read_text()), lote)
    for k in ("arena", "arcilla", "mo_pct", "cos_t_ha", "densidad_aparente", "agua_disponible_mm_m"):
        v = r["parametros"][k]
        assert v["rango"][0] <= v["valor"] <= v["rango"][1] or k == "agua_disponible_mm_m", k
    assert 0 < r["parametros"]["arena"]["valor"] + r["parametros"]["arcilla"]["valor"] < 1
