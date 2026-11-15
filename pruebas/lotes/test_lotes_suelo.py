# asistido por SI: Claude Code y Antigravity, pruebas de parametros_suelo.json con claves en raíz para el Gemelo (T-D5 Parte B / D-027)
import json
from pathlib import Path

import pytest

from lotes_demo.suelo import media_ponderada, parametros_desde_rest

RAIZ = Path("C:/NASA/AGROVERSEx/datos/procesados/lotes")


def _capa(vals):
    # vals: lista de (tope, fondo, valor)
    return {"depths": [{"range": {"top_depth": t, "bottom_depth": b}, "values": {"mean": v, "Q0.05": v * 0.5, "Q0.95": v * 1.5}} for t, b, v in vals]}


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
    # claves escalares en la raíz exigidas por gemelo.suelo.perfil_desde_parametros_datos (D-027)
    for k in ("arena", "arcilla", "mo_pct", "cos_t_ha"):
        assert isinstance(r.get(k), float), f"falta clave escalar {k} en raíz"
        assert r[k] == pytest.approx(r["parametros"][k]["valor"])
    assert r.get("profundidad_m") == pytest.approx(1.0)
    for k in ("arena", "arcilla", "mo_pct", "cos_t_ha", "densidad_aparente", "agua_disponible_mm_m"):
        v = r["parametros"][k]
        assert v["rango"][0] <= v["valor"] <= v["rango"][1] or k == "agua_disponible_mm_m", k
    assert 0 < r["arena"] + r["arcilla"] < 1
