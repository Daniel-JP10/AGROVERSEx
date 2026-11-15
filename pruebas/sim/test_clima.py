# asistido por SI: Claude Code (Anthropic), escritura y revisión de código; base del prototipo migrada en el hackatón
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
import yaml

from simulacion import clima, config
from simulacion.productos import B_PROVISIONAL
from simulacion.referencias.cargar import cargar_enso, cargar_eventos
from simulacion.tiempo import mes_id

AQUI = Path(__file__).resolve().parents[2] / "src/simulacion/referencias"
N = config.N_MESES
# En el worktree no está datos/: se busca también en la raíz del repo principal
PRINCIPAL = next((q for q in Path(__file__).resolve().parents if (q / "datos/procesados").exists()), config.RAIZ)


def _geo_sintetica():
    # Datos sintéticos: ninguna prueba unitaria depende de geo.sqlite
    rng = np.random.default_rng(1)
    filas = [
        ("AND", "COL", 4.7, 2600.0, 15),      # andina de Colombia, Cfb
        ("TROP", "GAB", 0.5, 30.0, 1),        # trópico bajo, Af
        ("POLAR", "NOR", 70.0, 100.0, 27),    # alta latitud, Dfc
        ("PEND", "BRA", -10.0, 300.0, 3),     # región ENSO PENDIENTE
        ("SINK", "FRA", 30.0, 200.0, -1),     # sin Köppen: respaldo
        ("IDN1", "IDN", -6.0, 50.0, 1),
    ]
    for i in range(200):
        filas.append((f"S{i}", "BRA", rng.uniform(-50, 60), rng.uniform(0, 3000), int(rng.integers(1, 31))))
    return pd.DataFrame(filas, columns=["id", "iso3", "punto_lat", "elev_media", "koppen"]).set_index("id")


@pytest.fixture(scope="module")
def geo():
    return _geo_sintetica()


@pytest.fixture(scope="module")
def sim(geo):
    ids = list(geo.index)
    return ids, clima.generar_clima(ids, slice(None), geo=geo)


def _fila(sim, uid):
    ids, c = sim
    return ids.index(uid), c


def test_t2m_ordenada(sim):
    _, c = sim
    ok = ~np.isnan(c.t2m)
    assert (c.t2m_min[ok] <= c.t2m[ok]).all() and (c.t2m[ok] <= c.t2m_max[ok]).all()
    assert (c.t2m_p10[ok] <= c.t2m[ok]).all() and (c.t2m[ok] <= c.t2m_p90[ok]).all()


def test_rangos_fisicos(sim):
    _, c = sim
    assert np.nanmin(c.t2m) >= -60 and np.nanmax(c.t2m) <= 60
    assert np.nanmin(c.rh2m) >= 0 and np.nanmax(c.rh2m) <= 100
    assert np.nanmin(c.rad_sw) >= 0 and np.nanmax(c.rad_sw) <= 35
    assert np.nanmin(c.precip) >= 0
    for a in (c.precip, c.t2m, c.rad_sw, c.dias_helada, c.bandera):
        assert a.shape == (len(sim[0]), N)


def test_helada_cero_en_tropico_bajo(sim):
    i, c = _fila(sim, "TROP")
    assert (c.t2m_min[i] > 8).all() and (c.dias_helada[i] == 0).all()
    j, _ = _fila(sim, "POLAR")
    assert (c.dias_helada[j] > 0).any()


def test_nov_2026_parcial(sim):
    _, c = sim
    assert c.precip_frac[0, mes_id(2026, 11)] == pytest.approx(5 / 30)
    assert c.precip_frac[0, mes_id(2026, 10)] == 1


def test_imerg_provisional_desde_oct_2025(sim):
    _, c = sim
    b = c.bandera[0]
    assert (b[mes_id(2025, 10):] & B_PROVISIONAL).all()
    assert not (b[:mes_id(2025, 10)] & B_PROVISIONAL).any()


def test_enso_signo_colombia(sim):
    roni = cargar_enso().roni.to_numpy()
    ok = ~np.isnan(roni)
    # forzante puro: negativo en El Niño para Colombia (EV-ENS-008)
    lluvia, _ = clima.forzante_enso("Colombia (Caribe y Andina)", roni)
    assert lluvia[roni > 1].max() < 0 and lluvia[roni < -1].min() > 0
    # la serie generada de una unidad andina conserva la señal
    i, c = _fila(sim, "AND")
    assert np.corrcoef(roni[ok], c.precip[i][ok])[0, 1] < -0.15
    # región PENDIENTE: sin teleconexión
    z, zt = clima.forzante_enso("Sahel", roni)
    assert (z == 0).all() and (zt == 0).all()
    j, _ = _fila(sim, "PEND")
    assert abs(np.corrcoef(roni[ok], c.precip[j][ok])[0, 1]) < 0.15


def test_enso_regiones_con_dos_fuentes():
    roni = np.array([2.0, -2.0])
    for reg, signo in (("Indonesia", -1), ("Pacífico occidental", -1), ("Sur de EE. UU.", 1)):
        lluvia, _ = clima.forzante_enso(reg, roni)
        assert np.sign(lluvia[0]) == signo and np.sign(lluvia[1]) == -signo


def test_evento_signo():
    eventos = {e["id"]: e for e in cargar_eventos()}
    ids = ["a", "b"]
    iso3 = np.array(["RUS", "PAK"])
    p, t = np.full((2, N), 100.0), np.full((2, N), 15.0)
    clima.imprimir_eventos(p, t, ids, list(eventos.values()), iso3=iso3)
    # ev02 sequía repentina en Rusia 2010: menos lluvia; ev04 EE. UU. calor no toca estas unidades
    assert (p[0, mes_id(2010, 1):mes_id(2010, 12) + 1] < 100).all()
    # ev08 inundación en Pakistán 2022: más lluvia
    assert (p[1, mes_id(2022, 1):mes_id(2022, 12) + 1] > 100).all()
    # ev04 sequía y calor en EE. UU.: lluvia baja y temperatura sube
    p2, t2 = np.full((1, N), 100.0), np.full((1, N), 15.0)
    clima.imprimir_eventos(p2, t2, ["u"], list(eventos.values()), iso3=np.array(["USA"]))
    assert p2[0, mes_id(2012, 7)] < 100 and t2[0, mes_id(2012, 7)] > 15
    # ev18 helada en Brasil: temperatura baja
    p3, t3 = np.full((1, N), 100.0), np.full((1, N), 15.0)
    clima.imprimir_eventos(p3, t3, ["u"], list(eventos.values()), iso3=np.array(["BRA"]))
    assert t3[0, mes_id(2021, 6)] < 15


def test_ev09_solo_adm1_amazonicos():
    eventos = [e for e in cargar_eventos() if e["id"] == "ev09"]
    iso3 = np.array(["COL", "COL", "COL", "COL", "BRA"])
    adm1 = np.array(["Cundinamarca", "Boyacá", "Caquetá", "Amazonas", "Pará"])
    p, t = np.full((5, N), 100.0), np.full((5, N), 15.0)
    clima.imprimir_eventos(p, t, list("abcde"), eventos, iso3=iso3, adm1=adm1)
    assert (t[:2] == 15).all() and (p[:2] == 100).all()
    assert (t[2:, mes_id(2023, 6)] > 15).all() and (p[2:, mes_id(2023, 6)] < 100).all()


def test_tendencia_colombia(sim):
    assert clima.tendencia_unidad("COL") == pytest.approx(0.24)
    assert clima.tendencia_unidad("XXX") == pytest.approx(0.326)  # respaldo global GISTEMP
    i, c = _fila(sim, "AND")
    anual = c.t2m[i, :312].reshape(26, 12).mean(1)
    pend = np.polyfit(np.arange(26), anual, 1)[0] * 10
    assert 0.24 - 0.10 <= pend <= 0.24 + 0.10


def test_tendencia_media_colombia_sin_inflado_enso():
    rng = np.random.default_rng(5)
    geo = pd.DataFrame({"iso3": "COL", "punto_lat": rng.uniform(0, 11, 60), "elev_media": rng.uniform(0, 3000, 60),
                        "koppen": rng.integers(1, 4, 60)}, index=[f"C{i}" for i in range(60)])
    c = clima.generar_clima(list(geo.index), slice(None), geo=geo)
    anual = c.t2m[:, :312].reshape(60, 26, 12).mean(2).mean(0)
    assert abs(np.polyfit(np.arange(26), anual, 1)[0] * 10 - 0.24) <= 0.06


def test_helada_parcial_con_minima_baja():
    # mínima mensual de 1 °C: ya hay días de helada (Φ(-1/2,5) ~ 34 %)
    geo = pd.DataFrame({"iso3": "FRA", "punto_lat": 45.0, "elev_media": 0.0, "koppen": 15}, index=["F"])
    c = clima.generar_clima(["F"], slice(None), geo=geo)
    m = (c.t2m_min[0] > 0) & (c.t2m_min[0] < 3)
    assert m.any() and (c.dias_helada[0][m] > 0).any()


def test_reproducible_y_bloque_independiente(geo):
    ids = list(geo.index)
    a = clima.generar_clima(ids, slice(0, 10), geo=geo)
    b = clima.generar_clima(ids, slice(0, 10), geo=geo)
    c = clima.generar_clima(ids, slice(5, 10), geo=geo)
    np.testing.assert_array_equal(a.t2m, b.t2m)
    np.testing.assert_array_equal(a.precip[5:], c.precip)


def test_respaldo_sin_koppen(geo):
    c = clima.generar_clima(["SINK"], slice(None), geo=geo)
    assert c.sin_koppen.tolist() == [True]
    cl = clima.climatologia_unidad(30.0, 200.0, None)
    assert cl["respaldo"] and len(cl["t_media"]) == 12 and len(cl["precip"]) == 12
    assert not clima.climatologia_unidad(4.7, 2600.0, 15)["respaldo"]


def test_clases_internas_30_sin_koppen_beck():
    assert len(clima._COD) == 30 and "Af" in clima._COD.values()
    assert not (AQUI / "koppen_leyenda.yaml").exists()


@pytest.mark.skip(reason="depende de geo.sqlite del prototipo, que D-003 no importa")
@pytest.mark.datos_reales
def test_colombia_real():
    import time
    geo = clima.cargar_geo(PRINCIPAL / "datos/procesados/geo.sqlite")
    col = geo[geo.iso3 == "COL"]
    assert len(col) > 1000 and (col.koppen >= 0).mean() > 0.9
    ids = list(col.index)
    t0 = time.perf_counter()
    c = clima.generar_clima(ids, slice(None), geo=geo)
    dt = time.perf_counter() - t0
    print(f"COL {len(ids)} unidades: {dt:.2f} s")
    anual = np.nanmean(c.t2m[:, :312].reshape(len(ids), 26, 12).mean(2), axis=0)
    assert abs(np.polyfit(np.arange(26), anual, 1)[0] * 10 - 0.24) <= 0.06
    assert np.nanmin(c.rh2m) >= 0 and np.nanmax(c.rad_sw) <= 35


def test_sin_dataset_koppen_en_el_producto():
    # D-025: ni el loader ni estaticos leen el mapa de Beck et al. 2023
    import inspect
    assert "clase_fraccion" not in inspect.getsource(clima.cargar_geo)
    assert "koppen" not in (Path(config.RAIZ) / "src/simulacion/geo/estaticos.py").read_text(encoding="utf-8").lower()
