# asistido por SI: Claude Code y Antigravity, pruebas de los forzantes diarios por lote, corrección de altura y validación GHCN (T-D5 B / D-027)
import math
from pathlib import Path

import pytest

from lotes_demo.forzantes import (
    GRADIENTE_ISA_C_POR_M,
    actualizar_power_csv_altura,
    escribir_imerg_csv,
    leer_power_csv,
    validar_power,
    validar_temperatura_ghcn,
)

RAIZ = Path("C:/NASA/AGROVERSEx/datos/procesados/lotes")
GHCN_CSV = Path("C:/NASA/compartir/ghcn/COM00080370.csv")  # fuera del repo (D-038)


def test_validar_detecta_tmin_mayor_que_tmax():
    malo = {"T2M_MIN": [5.0], "T2M_MAX": [3.0], "PRECTOTCORR": [0.0]}
    with pytest.raises(ValueError, match="T2M_MIN"):
        validar_power(malo)


def test_validar_detecta_precipitacion_negativa():
    with pytest.raises(ValueError, match="PRECTOTCORR"):
        validar_power({"T2M_MIN": [1.0], "T2M_MAX": [2.0], "PRECTOTCORR": [-1.0]})


def test_faltante_no_se_vuelve_cero(tmp_path):
    jl = tmp_path / "i.jsonl"
    jl.write_text('{"dia":"2020-01-01","p":null,"cnt":null}\n{"dia":"2020-01-02","p":0.0,"cnt":48.0}\n')
    out = tmp_path / "o.csv"
    escribir_imerg_csv(jl, out, "2020-01-01", "2020-01-03")
    f = out.read_text().splitlines()
    assert f[1].split(",")[3] == "" and f[2].split(",")[3] == "0.0"
    # el día 3 no se descargó: fila presente y vacía, nunca 0
    assert f[3].split(",")[3] == ""


def test_actualizar_power_csv_agrega_columnas_corregidas_sin_borrar_crudas(tmp_path):
    csv_in = tmp_path / "power_diario.csv"
    csv_in.write_text(
        "-BEGIN HEADER-\n"
        "Location: latitude  0.842   longitude -77.661 \n"
        "elevation from MERRA-2: Average for 0.5 x 0.625 degree lat/lon region = 2553.24 meters\n"
        "-END HEADER-\n"
        "YEAR,DOY,PRECTOTCORR,T2M,T2M_MAX,T2M_MIN,RH2M,ALLSKY_SFC_SW_DWN,WS2M\n"
        "2020,1,1.5,13.0,18.0,9.0,80.0,15.0,2.0\n",
        encoding="utf-8",
    )
    meta = actualizar_power_csv_altura(csv_in, elev_lote_m=2934.0)
    d = leer_power_csv(csv_in)
    validar_power(d)
    # las columnas crudas permanecen intactas
    assert d["T2M"] == [13.0]
    assert d["T2M_MAX"] == [18.0]
    assert d["T2M_MIN"] == [9.0]
    # las corregidas aplican gradiente estándar -0,0065 °C/m sobre delta_z = 2934 - 2553,24 = +380,76 m
    dz = 2934.0 - 2553.24
    assert GRADIENTE_ISA_C_POR_M == pytest.approx(-0.0065)
    assert meta["delta_z_m"] == pytest.approx(dz)
    assert d["T2M_CORR"][0] == pytest.approx(13.0 + GRADIENTE_ISA_C_POR_M * dz, abs=1e-3)
    assert d["T2M_MAX_CORR"][0] == pytest.approx(18.0 + GRADIENTE_ISA_C_POR_M * dz, abs=1e-3)
    assert d["T2M_MIN_CORR"][0] == pytest.approx(9.0 + GRADIENTE_ISA_C_POR_M * dz, abs=1e-3)
    assert d["T2M_MIN_CORR"][0] < d["T2M_MAX_CORR"][0]


@pytest.mark.datos_reales
@pytest.mark.parametrize("lote", ["DEMO-USA-01", "DEMO-COL-01"])
def test_power_real(lote):
    p = RAIZ / lote / "power_diario.csv"
    if not p.exists():
        pytest.skip("sin descarga")
    d = leer_power_csv(p)
    validar_power(d)
    assert len(d["YEAR"]) == 8766 and not any(math.isnan(x) for x in d["PRECTOTCORR"])
    for col in ("T2M", "T2M_MAX", "T2M_MIN", "T2M_CORR", "T2M_MAX_CORR", "T2M_MIN_CORR"):
        assert col in d and len(d[col]) == 8766
    assert all(lo <= hi for lo, hi in zip(d["T2M_MIN_CORR"], d["T2M_MAX_CORR"]))


@pytest.mark.datos_reales
def test_validacion_ghcn_ipiales_real():
    p_pw = RAIZ / "DEMO-COL-01" / "power_diario.csv"
    if not (p_pw.exists() and GHCN_CSV.exists()):
        pytest.skip("sin archivos reales de Ipiales")
    res = validar_temperatura_ghcn(p_pw, GHCN_CSV, elev_lote_m=2934.0, elev_estacion_m=2961.0)
    # T2M_MIN corregida debe reducir sustancialmente el sesgo cálido y el MAE frente a la serie cruda
    tmin_cruda = res["comparaciones"]["T2M_MIN_vs_TMIN"]["cruda_2553m"]
    tmin_lote = res["comparaciones"]["T2M_MIN_vs_TMIN"]["corregida_lote_2934m"]
    tmin_est = res["comparaciones"]["T2M_MIN_vs_TMIN"]["corregida_estacion_2961m"]
    assert abs(tmin_lote["sesgo_c"]) < abs(tmin_cruda["sesgo_c"])
    assert tmin_lote["mae_c"] < tmin_cruda["mae_c"]
    assert tmin_est["mae_c"] < tmin_cruda["mae_c"]
    for metrica in ("sesgo_c", "mae_c", "rmse_c"):
        ic = tmin_lote[f"{metrica}_ic95_bootstrap_anual"]
        assert ic[0] <= tmin_lote[metrica] <= ic[1]
