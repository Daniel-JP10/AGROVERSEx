# asistido por SI: Claude Code (Anthropic), prueba de las series del mundo con dos ponderaciones (traspaso S1w)
import gzip
import json

import pandas as pd

from mapa_estatico.construir import N_MESES, construir_mundo, indice_mes

COLS = ["unidad_id", "nivel", "variable", "mes", "valor", "p10", "p90", "tipo_rango", "frac_valida", "ponderacion", "producto", "version", "estado", "unidad", "motivo"]
FINAL = "GPM IMERG Final Run, mensual 0,1 grados (GPM_3IMERGM)"
ARCHIVOS = {"precipitacion_final": ("mm/hr", "final", "2025-09"), "precipitacion_late": ("mm/day", "provisional", "2025-10"),
            "t2m": ("K", "final", "2024-06"), "humedad_radicular": ("kg m-2", "final", "2024-06"), "ndvi": ("1", "final", "2024-06")}
UNIDADES = [("KEN-ADM0", 0), ("KEN-ADM1-a", 1), ("KEN-ADM2-a", 2), ("KEN-ADM2-b", 2), ("ATA-ADM0", 0), ("USA-ADM2-x", 2)]


def escribir(carpeta, pond):
    for nombre, (unidad, estado, mes) in ARCHIVOS.items():
        filas = []
        for u, n in UNIDADES:
            sin = pond == "cultivo" and u in ("ATA-ADM0", "KEN-ADM2-b")
            v = None if sin else 1.234567
            prod = FINAL if nombre == "precipitacion_final" else "MERRA-2 rean�lisis, M2TMNXSLV (T2M)" if nombre == "t2m" else nombre
            filas.append([u, n, nombre, mes, v, v, v, "espacial", 0 if sin else 0.9876, pond, prod, "07B", estado, unidad, "sin_cultivo" if sin else ""])
        pd.DataFrame(filas, columns=COLS).to_csv(carpeta / f"serie_mensual_{nombre}_{pond}.csv.gz", index=False, encoding="utf-8")


def leer(ruta):
    return json.loads(gzip.decompress(ruta.read_bytes()))


def preparar(tmp_path, adm2=None):
    src = tmp_path / "consolidados"
    src.mkdir()
    for pond in ("area", "cultivo"):
        escribir(src, pond)
    sal = tmp_path / "datos"
    construir_mundo(src, sal, adm2, procesos=1)
    return sal


def test_archivos_por_ponderacion_y_sin_cultivo(tmp_path):
    sal = preparar(tmp_path)
    a, c = leer(sal / "MUNDO/precip_0.json.gz"), leer(sal / "MUNDO/precip_0_cultivo.json.gz")
    assert a["ids"] == c["ids"] == ["ATA-ADM0", "KEN-ADM0"]
    assert a["ponderacion"] == "area" and c["ponderacion"] == "cultivo"
    i = indice_mes("2025-09")
    assert len(a["valor"][0]) == N_MESES and a["valor"][0][i] == 1.23457 and a["p10"][0][i] == 1.2346 and a["frac"][0][i] == 0.988
    # sin cultivo: null y listado, nunca 0
    assert c["valor"][0][i] is None and c["sin_cultivo"] == ["ATA-ADM0"] and a["sin_cultivo"] == []
    # adm2 por país; Final y Late en el mismo archivo, con su unidad y estado por mes
    k = leer(sal / "KEN/precip_2_cultivo.json.gz")
    assert k["ids"] == ["KEN-ADM2-a", "KEN-ADM2-b"] and k["sin_cultivo"] == ["KEN-ADM2-b"]
    pm = k["productos"]
    assert pm[k["producto_mes"][indice_mes("2025-10")]] == {"producto": "precipitacion_late", "version": "07B", "unidad": "mm/day", "estado": "provisional"}
    assert pm[k["producto_mes"][i]]["unidad"] == "mm/hr"
    assert (sal / "USA/t2m_2.json.gz").is_file() and (sal / "MUNDO/ndvi_1_cultivo.json.gz").is_file()


def test_meta_paises_productos_en_ingles_y_conteo(tmp_path):
    sal = preparar(tmp_path)
    meta = json.loads((sal / "meta.json").read_text(encoding="utf-8"))
    assert meta["paises"] == ["ATA", "KEN"] and meta["paises_adm2"] == ["KEN", "USA"] and meta["ponderacion_defecto"] == "cultivo"
    nombres = [p["producto"] for p in meta["variables"]["precip"]["productos"]]
    assert "GPM IMERG Final Run, monthly 0.1° (GPM_3IMERGM)" in nombres
    assert meta["variables"]["t2m"]["productos"][0]["producto"] == "MERRA-2 reanalysis, M2TMNXSLV (T2M)"
    u = meta["unidades_publicadas"]["precip"]
    assert u["area"]["2"] == {"ids": 3, "con_valor": 3, "sin_cultivo": 0, "archivos": 2}
    assert u["cultivo"]["0"] == {"ids": 2, "con_valor": 1, "sin_cultivo": 1, "archivos": 1}


def test_respaldo_adm2_solo_de_los_paises_pedidos(tmp_path):
    sal = preparar(tmp_path, {"USA"})
    assert not (sal / "KEN").exists() and (sal / "USA/precip_2.json.gz").is_file()
    assert (sal / "MUNDO/precip_1.json.gz").is_file()
