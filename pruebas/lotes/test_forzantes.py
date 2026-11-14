# asistido por SI: Claude Code, pruebas de los forzantes diarios por lote (T-D5 Parte B)
import math
from pathlib import Path

import pytest

from lotes_demo.forzantes import escribir_imerg_csv, leer_power_csv, validar_power

RAIZ = Path("C:/NASA/AGROVERSEx/datos/procesados/lotes")


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


@pytest.mark.datos_reales
@pytest.mark.parametrize("lote", ["DEMO-USA-01", "DEMO-COL-01"])
def test_power_real(lote):
    p = RAIZ / lote / "power_diario.csv"
    if not p.exists():
        pytest.skip("sin descarga")
    d = leer_power_csv(p)
    validar_power(d)
    assert len(d["YEAR"]) == 8766 and not any(math.isnan(x) for x in d["PRECTOTCORR"])
