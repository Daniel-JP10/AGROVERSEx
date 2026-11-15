# asistido por SI: Claude Code, pruebas de la conversión de series a archivos estáticos (T-D9)
import gzip
import hashlib
import json

import pandas as pd
import pytest

from mapa_estatico import construir as c

COLS = ["unidad_id", "nivel", "variable", "mes", "valor", "p10", "p90", "tipo_rango", "frac_valida", "ponderacion", "producto", "version", "estado", "unidad", "motivo"]


def fila(u, mes, valor, unidad="mm/hr", estado="final", producto="IMERG", frac=1.0, nivel=0, variable="precipitacion"):
    return [u, nivel, variable, mes, valor, valor, valor, "espacial", frac, "area", producto, "07B", estado, unidad, ""]


def escribir(carpeta, nombre, filas):
    pd.DataFrame(filas, columns=COLS).to_csv(carpeta / f"serie_mensual_{nombre}_area.csv.gz", index=False, encoding="utf-8")


def test_unidad_y_estado_van_por_mes_y_el_hueco_queda_nulo(tmp_path):
    escribir(tmp_path, "precipitacion_final", [fila("COL-ADM0", "2025-09", 0.5), fila("COL-ADM0", "2025-08", None, frac=0.2)])
    escribir(tmp_path, "precipitacion_late", [fila("COL-ADM0", "2025-10", 12.0, unidad="mm/day", estado="provisional")])
    d = c._cargar(tmp_path, ["precipitacion_final", "precipitacion_late"])
    m = c.matriz(d, 0, "precip")
    i = c.indice_mes
    assert m["valor"][0][i("2025-09")] == 0.5 and m["valor"][0][i("2025-08")] is None
    assert m["frac"][0][i("2025-08")] == 0.2  # la fracción válida se conserva aunque no haya valor
    pm = m["productos"]
    assert pm[m["producto_mes"][i("2025-09")]]["unidad"] == "mm/hr"
    assert pm[m["producto_mes"][i("2025-10")]]["unidad"] == "mm/day"
    assert pm[m["producto_mes"][i("2025-10")]]["estado"] == "provisional"
    assert m["producto_mes"][i("2001-01")] == -1  # mes sin producto


def test_un_mes_con_dos_unidades_se_rechaza(tmp_path):
    escribir(tmp_path, "precipitacion_final", [fila("A", "2020-01", 1.0), fila("B", "2020-01", 1.0, unidad="mm/day")])
    d = c._cargar(tmp_path, ["precipitacion_final"])
    with pytest.raises(ValueError):
        c.matriz(d, 0, "precip")


def test_final_y_late_no_pueden_traslaparse(tmp_path):
    escribir(tmp_path, "precipitacion_final", [fila("A", "2025-10", 1.0)])
    escribir(tmp_path, "precipitacion_late", [fila("A", "2025-10", 2.0, unidad="mm/day")])
    with pytest.raises(ValueError):
        c._cargar(tmp_path, ["precipitacion_final", "precipitacion_late"])


def test_caracter_de_reemplazo_se_corrige_y_otro_se_rechaza():
    assert c._texto("MERRA-2 rean\ufffdlisis") == "MERRA-2 reanálisis"
    with pytest.raises(ValueError):
        c._texto("otro \ufffd")


def test_mes_fuera_del_eje_se_rechaza(tmp_path):
    escribir(tmp_path, "precipitacion_final", [fila("A", "2026-12", 1.0)])
    with pytest.raises(ValueError):
        c._cargar(tmp_path, ["precipitacion_final"])


def test_salida_reproducible_y_legible(tmp_path):
    r = tmp_path / "x.json.gz"
    c.escribir_gz(r, {"a": [1, None]})
    a = r.read_bytes()
    c.escribir_gz(r, {"a": [1, None]})
    assert r.read_bytes() == a
    assert json.loads(gzip.open(r, "rt", encoding="utf-8").read()) == {"a": [1, None]}


def test_copiar_lotes_y_manifiesto_con_hashes_y_meses(tmp_path):
    series_dir = tmp_path / "series"
    series_dir.mkdir()
    escribir(series_dir, "precipitacion_final", [fila("COL-ADM0", "2025-09", 0.5)])
    escribir(series_dir, "precipitacion_late", [fila("COL-ADM0", "2025-10", 12.0, unidad="mm/day", estado="provisional")])
    escribir(series_dir, "t2m", [fila("COL-ADM0", "2024-06", 295.0, unidad="K", producto="MERRA-2", variable="t2m")])
    escribir(series_dir, "humedad_radicular", [fila("COL-ADM0", "2024-06", 300.0, unidad="kg m-2", producto="GLDAS", variable="humedad_radicular")])
    escribir(series_dir, "ndvi", [fila("COL-ADM0", "2000-02", 0.65, unidad="1", producto="MODIS", variable="ndvi")])

    lotes_orig = tmp_path / "lotes_demo.json"
    lotes_orig.write_text(json.dumps({"version": 1, "lotes": [{"lote_id": "DEMO-COL-01", "unidad_id": "COL-ADM2-1"}]}), encoding="utf-8")

    salida = tmp_path / "public_datos"
    c.construir_series(series_dir, salida, "COL")
    c.copiar_lotes(lotes_orig, salida)
    man = c.construir_manifiesto(salida, generado_utc="2026-11-14T22:00:00Z")

    assert (salida / "lotes_demo.json").exists()
    assert man["version_contrato"] == "web_datos v0"
    assert man["generado_utc"] == "2026-11-14T22:00:00Z"
    assert set(man["variables"].keys()) == {"precip", "t2m", "sm_raiz", "ndvi"}
    assert man["variables"]["precip"]["meses_disponibles"] == {"desde": "2025-09", "hasta": "2025-10", "n_meses_con_producto": 2}
    assert man["variables"]["ndvi"]["productos"][0]["unidad"] == "1"
    assert "lotes_demo.json" in man["archivos"]
    for rel, info in man["archivos"].items():
        b = (salida / rel).read_bytes()
        assert info["bytes"] == len(b)
        assert info["sha256"] == hashlib.sha256(b).hexdigest()
