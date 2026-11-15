# asistido por SI: Claude Code (Anthropic), escritura y revisión de código; base del prototipo migrada en el hackatón
import re
from datetime import date

import numpy as np
import pandas as pd
import pytest
from shapely import wkt
from shapely.geometry import box

from simulacion import config, lotes
from simulacion.azar import rng_unidad
from simulacion.tiempo import dia_id

ND = dia_id(config.FECHA_FIN_DIARIA) + 1
N = config.N_MESES
# Dos unidades sintéticas con geometría de caja, una por zona ficticia
GEOMS = {"U1": box(-95, 40, -90, 44), "U2": box(-90, 40, -86, 43)}
GEO = pd.DataFrame({"iso3": ["USA", "USA"], "punto_lat": [42.0, 41.5], "punto_lon": [-92.5, -88.0],
                    "adm1": ["a", "b"], "elev_media": [250.0, 200.0], "koppen": [25, 25]}, index=["U1", "U2"])
ZONAS = {"zona_x": {"nombre": "X", "cultivos": ["maiz", "soya"], "unidades": ["U1", "U2"]}}


def _mensual(nmax=0.84):
    m = np.arange(N) % 12
    f = np.clip(np.sin((m - 3) / 12 * 2 * np.pi), 0, 1)
    return {"ndvi": 0.2 + (nmax - 0.2) * f, "sm_raiz": 0.2 + 0.1 * f, "precip": 60 + 40 * f,
            "dias_helada": np.where(m < 2, 10.0, 0.0), "elev_media": 250.0}


def _lotes(n=50):
    return lotes.generar_lotes("zona_x", n, geo=GEO, geometrias=GEOMS, zonas=ZONAS)


def test_10_zonas_50_lotes_sin_procedencia_china():
    z = lotes.cargar_zonas()
    assert len(z) == 10
    assert 490 <= 10 * 50 <= 510
    assert not hasattr(config, "INCLUIR_PROCEDENCIA_CHINA")
    assert "north_china_plain" not in z
    assert not any("procedencia" in v for v in z.values())
    assert not any(u.startswith("CHN.") for v in z.values() for u in v["unidades"])
    assert all(len(v["unidades"]) > 0 for v in z.values())


def test_lote_dentro_de_su_unidad():
    ls = _lotes()
    assert len(ls) == 50
    for l in ls:
        assert GEOMS[l["unidad_id"]].contains(wkt.loads(l["geom_wkt"]))


def test_sin_persona():
    for l in _lotes():
        assert re.fullmatch(r"Lzona_x-\d+", l["id"])
        assert set(l) == {"id", "unidad_id", "geom_wkt", "cultivo_actual", "zona_demo", "pico_ndvi"}
        assert l["zona_demo"] == "zona_x" and l["cultivo_actual"] in ("maiz", "soya")


def test_serie_longitud():
    s = lotes.serie_diaria(_lotes(1)[0], _mensual())
    for k in ("ndvi", "nbr2", "sm_verdad", "sm_sensor", "nube"):
        assert len(s[k]) == ND == dia_id(config.FECHA_FIN_DIARIA) + 1


def test_nube_es_null_no_cero():
    s = lotes.serie_diaria(_lotes(1)[0], _mensual())
    assert (s["nube"] == 1).sum() > 0
    assert np.isnan(s["ndvi"][s["nube"] == 1]).all()
    assert (s["ndvi"][~np.isnan(s["ndvi"])] > 0).all()  # ningún cero de relleno
    assert np.isnan(s["ndvi"]).mean() > 0.5  # días sin pasada: NULL, sin interpolación


def test_antes_de_2013_solo_ndvi():
    l = _lotes(1)[0]
    s = lotes.serie_diaria(l, _mensual())
    corte = dia_id(date(2013, 4, 1))
    assert np.isnan(s["nbr2"][:corte]).all() and not np.isnan(s["nbr2"][corte:]).all()
    v = lotes.detectar_ventana(s["ndvi"], s["nbr2"], np.arange(ND), ndvi_verdad=s["ndvi_verdad"])
    assert all(w["fuente"] == "ndvi" for w in v if w["anio"] < 2013)
    assert any(w["fuente"] == "ndvi+nbr2" for w in v if w["anio"] >= 2014)


def test_slc_off():
    rng = rng_unidad("x", "pasadas")
    m = lotes.mascaras_pasada(rng)["l7_valido"]
    a = lambda y: m[dia_id(date(y, 1, 1)):dia_id(date(y + 1, 1, 1))].sum()
    assert a(2004) < a(2002)
    assert a(2002) > 0


def test_ndvi_pico_cultivo_lotes():
    ls = _lotes(50)
    ok = 0
    for l in ls:
        s = lotes.serie_diaria(l, _mensual())
        lo, hi = lotes.PICO_NDVI[l["cultivo_actual"]]
        ok += lo <= np.nanmax(s["ndvi_verdad"]) <= hi
    assert ok / len(ls) >= 0.95


def test_ventana_error_semanas():
    l = _lotes(1)[0]
    m = _mensual()
    err = {}
    for esc in (0.0, 1.5):
        s = lotes.serie_diaria(l, m, escala_nube=esc)
        v = lotes.detectar_ventana(s["ndvi"], s["nbr2"], np.arange(ND), ndvi_verdad=s["ndvi_verdad"])
        e = [w["error_semanas"] for w in v if w["detectada"] and w["error_semanas"] is not None]
        assert e and all(set(w) >= {"inicio", "fin", "error_semanas", "detectada", "confianza"} for w in v)
        err[esc] = np.mean(e)
    assert err[0.0] < err[1.5]


def test_riesgos_rotulados():
    r = lotes.riesgos_lote(_lotes(1)[0], _mensual())
    assert "9 km" in r["estres_hidrico"]["etiqueta"]
    assert "0,5" in r["helada"]["etiqueta"]
    assert "relieve de unidad" in r["erosion"]["etiqueta"]
    assert r["erosion"]["valor"] is None  # PENDIENTE: sin pendiente de 30 m


@pytest.mark.datos_reales
def test_datos_reales_contencion_y_zonas():
    from simulacion.clima import cargar_geo
    geo = cargar_geo()
    z = lotes.cargar_zonas()
    assert all(u in geo.index for v in z.values() for u in v["unidades"])
    ls = lotes.generar_lotes("llanos", 10, geo=geo)
    g = lotes.geometrias_unidades({l["unidad_id"] for l in ls})
    assert all(g[l["unidad_id"]].contains(wkt.loads(l["geom_wkt"])) for l in ls)
