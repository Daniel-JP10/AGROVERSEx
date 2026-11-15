# asistido por SI: Claude Code (Anthropic), pruebas del resumen derivado de heladas de la estación GHCN (D-038)
import json
from pathlib import Path

import pytest

from lotes_demo import descargar_ghcn
from lotes_demo.helada_estacion import AVISO_USO, climatologia

RAIZ = Path(__file__).resolve().parents[2]
RESUMEN = RAIZ / "datos" / "lotes" / "validacion_temperatura_ipiales.json"

CABECERA = "STATION,DATE,LATITUDE,LONGITUDE,ELEVATION,TMIN,TMIN_ATTRIBUTES\n"


def test_cuenta_heladas_por_mes_y_descarta_banderas(tmp_path):
    csv = tmp_path / "X.csv"
    filas = [
        ("2001-01-01", "-5", ",,S"),     # helada válida
        ("2001-01-02", "10", ",,S"),     # sin helada
        ("2001-01-03", "-20", ",G,S"),   # bandera de calidad: se descarta
        ("2001-02-01", "0", ",,S"),      # 0,0 °C cuenta como <= 0
        ("2001-02-02", "", ""),          # sin dato
        ("2000-12-31", "-50", ",,S"),    # fuera del periodo
    ]
    csv.write_text(CABECERA + "".join(f'"X","{d}","1.0","2.0","3000.0","{t}","{a}"\n' for d, t, a in filas),
                   encoding="utf-8")
    c = climatologia(csv, ["2001-01-01", "2001-02-28"], (0.0, -1.0))
    ene, feb = c["por_umbral_c"]["0.0"][:2]
    assert (ene["dias_periodo"], ene["dias_con_dato"], ene["dias_helada"]) == (31, 2, 1)
    assert (feb["dias_periodo"], feb["dias_con_dato"], feb["dias_helada"]) == (28, 1, 1)
    assert c["por_umbral_c"]["-1.0"][1]["dias_helada"] == 0
    assert c["rechazados_bandera_tmin"] == 1 and c["fuente_csv"] == "X.csv" and c["elevacion_m"] == 3000.0


def test_resumen_versionado_cruza_con_su_analisis_de_extremos():
    # Dos cálculos independientes del mismo resumen deben coincidir
    v = json.loads(RESUMEN.read_text(encoding="utf-8"))
    b = v["climatologia_helada_estacion"]
    meses = b["por_umbral_c"]["0.0"]
    assert [f["mes"] for f in meses] == list(range(1, 13))
    assert sum(f["dias_helada"] for f in meses) == v["analisis_extremos_frios_tmin"]["ghcn_dias_le_0c"]
    assert sum(f["dias_con_dato"] for f in meses) == v["analisis_extremos_frios_tmin"]["ghcn_tmin_n_validos"]
    assert b["periodo"] == v["periodo"] and v["aviso_uso"] == AVISO_USO and "no comercial" in AVISO_USO


def test_ningun_crudo_de_ghcn_en_el_repo():
    assert not list((RAIZ / "datos").rglob("COM000*.csv")) and not list((RAIZ / "datos").rglob("USC00*.csv"))


def test_descarga_rechaza_carpetas_dentro_del_repo():
    with pytest.raises(ValueError, match="D-038"):
        descargar_ghcn.descargar("COM00080370", RAIZ / "datos" / "crudos")
