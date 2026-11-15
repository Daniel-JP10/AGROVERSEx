# asistido por SI: Antigravity (Google DeepMind), pruebas TDD de exposicion_erosiva y umbrales P90 (T-D6 Idea 2)
import numpy as np
import pandas as pd
import pytest

from lotes_demo import exposicion_erosiva
from lotes_demo.erosion import (
    factor_erodabilidad_williams,
    factor_pendiente_mccool,
    pendiente_nasadem_lote,
    umbral_p90_semanal,
)


def _serie_sintetica():
    # tres años de fechas diarias (2020-2022) con tormentas concentradas en la semana 1
    fechas = pd.date_range("2020-01-01", "2022-12-31", freq="D")
    p = np.zeros(len(fechas), dtype=float)
    # en los primeros 7 días de cada año ponemos 9 días normales (2 mm) y 3 tormentas fuertes (30 mm)
    for i, f in enumerate(fechas):
        if f.month == 1 and f.day <= 7:
            p[i] = 30.0 if f.day in (1, 2) else 2.0
    return p, fechas


def test_exposicion_erosiva_cero_sin_dias_desnudos():
    p, fechas = _serie_sintetica()
    desnudo = np.zeros(len(fechas), dtype=float)
    res = exposicion_erosiva(p, fechas, desnudo=desnudo, pendiente_m_m=0.08, k_erodabilidad=0.035)
    assert res["indice_exposicion_erosiva"] == 0.0
    assert res["n_tormentas_suelo_desnudo"] == 0.0
    assert res["lluvia_tormentas_suelo_desnudo_mm"] == 0.0
    assert res["rango_indice"] == [0.0, 0.0]


def test_exposicion_erosiva_cero_sin_tormentas():
    _, fechas = _serie_sintetica()
    p_cero = np.zeros(len(fechas), dtype=float)
    desnudo = np.ones(len(fechas), dtype=float)
    res = exposicion_erosiva(p_cero, fechas, desnudo=desnudo, pendiente_m_m=0.08, k_erodabilidad=0.035)
    assert res["indice_exposicion_erosiva"] == 0.0
    assert res["n_tormentas_suelo_desnudo"] == 0.0
    assert res["lluvia_tormentas_suelo_desnudo_mm"] == 0.0


def test_umbral_p90_semanal_sin_fuga_temporal():
    # antes de 2022-01-01 las lluvias en semana 1 no superan 10 mm; en 2022 metemos eventos extremos de 500 mm
    fechas = pd.date_range("2018-01-01", "2022-12-31", freq="D")
    p = np.zeros(len(fechas), dtype=float)
    for i, f in enumerate(fechas):
        if f.month == 1 and f.day <= 7:
            if f.year < 2022:
                p[i] = float(f.day)  # 1..7 mm/día
            else:
                p[i] = 500.0  # evento futuro extremo
    u_corte = umbral_p90_semanal(p, fechas, fecha_corte="2021-12-31")
    u_total = umbral_p90_semanal(p, fechas, fecha_corte=None)
    assert u_corte[1] <= 7.0
    assert u_total[1] > 100.0
    # al evaluar exposicion_erosiva con fecha_corte no se contamina el umbral con 2022
    mask_pre = fechas <= pd.Timestamp("2021-12-31")
    r_corte = exposicion_erosiva(
        p[mask_pre],
        fechas[mask_pre],
        desnudo=np.ones(mask_pre.sum()),
        fecha_corte="2021-12-31",
    )
    assert r_corte["umbrales_p90_semanal_mm_dia"][1] == pytest.approx(u_corte[1])


def test_cota_baja_menor_o_igual_que_cota_alta():
    p, fechas = _serie_sintetica()
    cota_baja = np.full(len(fechas), 0.2)
    desnudo = np.full(len(fechas), 0.5)
    cota_alta = np.full(len(fechas), 0.8)
    res = exposicion_erosiva(
        p,
        fechas,
        desnudo=desnudo,
        desnudo_cota_baja=cota_baja,
        desnudo_cota_alta=cota_alta,
        pendiente_m_m=0.06,
        k_erodabilidad=0.03,
    )
    assert res["dias_desnudos_totales"]["cota_baja"] <= res["dias_desnudos_totales"]["valor"] <= res["dias_desnudos_totales"]["cota_alta"]
    assert res["dias_desnudos_anio"]["cota_baja"] <= res["dias_desnudos_anio"]["valor"] <= res["dias_desnudos_anio"]["cota_alta"]
    assert res["rango_n_tormentas_suelo_desnudo"][0] <= res["n_tormentas_suelo_desnudo"] <= res["rango_n_tormentas_suelo_desnudo"][1]
    assert res["rango_lluvia_tormentas_mm_anio"][0] <= res["lluvia_tormentas_suelo_desnudo_mm_anio"] <= res["rango_lluvia_tormentas_mm_anio"][1]
    assert res["rango_indice"][0] <= res["indice_exposicion_erosiva"] <= res["rango_indice"][1]
    # si cota_baja > cota_alta debe fallar con ValueError
    with pytest.raises(ValueError, match="cota_baja"):
        exposicion_erosiva(p, fechas, desnudo=desnudo, desnudo_cota_baja=cota_alta, desnudo_cota_alta=cota_baja)


def test_monotonia_con_pendiente_y_erodabilidad():
    p, fechas = _serie_sintetica()
    desnudo = np.ones(len(fechas), dtype=float)
    r_baja_pend = exposicion_erosiva(p, fechas, desnudo=desnudo, pendiente_m_m=0.02, k_erodabilidad=0.03)
    r_alta_pend = exposicion_erosiva(p, fechas, desnudo=desnudo, pendiente_m_m=0.15, k_erodabilidad=0.03)
    r_alto_k = exposicion_erosiva(p, fechas, desnudo=desnudo, pendiente_m_m=0.15, k_erodabilidad=0.05)
    assert 0.0 < r_baja_pend["indice_exposicion_erosiva"] < r_alta_pend["indice_exposicion_erosiva"]
    assert r_alta_pend["indice_exposicion_erosiva"] < r_alto_k["indice_exposicion_erosiva"]


def test_componentes_explicables_y_compatibilidad_con_v_gemelo():
    p, fechas = _serie_sintetica()
    cobertura_v = np.full(len(fechas), 0.25)  # 75 % suelo descubierto
    res = exposicion_erosiva(p, fechas, cobertura_v=cobertura_v, pendiente_m_m=0.05, k_erodabilidad=0.032)
    claves_esperadas = {
        "indice_exposicion_erosiva",
        "rango_indice",
        "rotulo",
        "etiqueta",
        "n_tormentas_suelo_desnudo",
        "n_tormentas_suelo_desnudo_anio",
        "rango_n_tormentas_suelo_desnudo",
        "lluvia_tormentas_suelo_desnudo_mm",
        "lluvia_tormentas_suelo_desnudo_mm_anio",
        "rango_lluvia_tormentas_mm_anio",
        "dias_desnudos_totales",
        "dias_desnudos_anio",
        "pendiente_m_m",
        "factor_pendiente_s",
        "k_erodabilidad",
        "umbrales_p90_semanal_mm_dia",
        "anios_evaluados",
    }
    assert claves_esperadas <= set(res.keys())
    assert res["rotulo"] == "combinacion_propia"
    assert len(res["umbrales_p90_semanal_mm_dia"]) == 52
    # comprobación manual de McCool 1987 para pendiente 0,05 (< 0,09): 10,8 * sin(arctan(0,05)) + 0,03
    s_manual = 10.8 * (0.05 / np.sqrt(1.0 + 0.05**2)) + 0.03
    assert res["factor_pendiente_s"] == pytest.approx(s_manual)
    # K de Williams 1995 en rango físico SI (0,005 a 0,08 t·ha·h/(ha·MJ·mm))
    k_usa = factor_erodabilidad_williams(0.11, 0.48, 0.41, 14.5)
    k_col = factor_erodabilidad_williams(0.38, 0.33, 0.29, 55.6)
    assert 0.005 < k_col < k_usa < 0.08
    assert factor_pendiente_mccool(0.05) < factor_pendiente_mccool(0.12)


def test_pendiente_nasadem_comprobada_contra_calculo_manual():
    from pathlib import Path
    import zipfile

    z_col = Path("C:/NASA/AGROVERSEx/datos/crudos/nasadem/NASADEM_HGT_n00w078.zip")
    if not z_col.exists():
        pytest.skip("sin NASADEM descargado")
    anillo = [[-77.665, 0.838], [-77.657, 0.838], [-77.657, 0.846], [-77.665, 0.846], [-77.665, 0.838]]
    rel = pendiente_nasadem_lote(z_col, anillo, 0.842, -77.661)
    assert rel["crs_metrico"] == "EPSG:32618"
    assert 0.01 < rel["pendiente_media_m_m"] < 0.25
    # comprobación manual por diferencias centrales en el píxel central
    with zipfile.ZipFile(z_col) as zf:
        hgt = np.frombuffer(zf.read("n00w078.hgt"), dtype=">i2").reshape(3601, 3601).astype(float)
    r_c = int(round((1.0 - 0.842) * 3600))
    c_c = int(round((-77.661 - (-78.0)) * 3600))
    dz_dy = (hgt[r_c + 1, c_c] - hgt[r_c - 1, c_c]) / (2.0 * rel["dy_m"])
    dz_dx = (hgt[r_c, c_c + 1] - hgt[r_c, c_c - 1]) / (2.0 * rel["dx_m"])
    assert rel["pendiente_centro_m_m"] == pytest.approx(np.sqrt(dz_dx**2 + dz_dy**2))

