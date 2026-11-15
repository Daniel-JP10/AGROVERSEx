# asistido por SI: Claude Code (Anthropic), prueba de las series del mundo con dos ponderaciones (traspaso S1w)
import gzip
import json

import pandas as pd

from mapa_estatico.construir import ESPANOL, N_MESES, PRODUCTO_EN, construir_mundo, indice_mes, traducir_productos

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
    assert "GPM IMERG Final Precipitation L3 1 month 0.1 degree x 0.1 degree (GPM_3IMERGM)" in nombres
    assert meta["variables"]["t2m"]["productos"][0]["producto"] == "MERRA-2 tavgM_2d_slv_Nx: 2d, Monthly mean, Single-Level Diagnostics (M2TMNXSLV, T2M)"
    u = meta["unidades_publicadas"]["precip"]
    assert u["area"]["2"] == {"ids": 3, "con_valor": 3, "sin_cultivo": 0, "archivos": 2}
    assert u["cultivo"]["0"] == {"ids": 2, "con_valor": 1, "sin_cultivo": 1, "archivos": 1}


def test_respaldo_adm2_solo_de_los_paises_pedidos(tmp_path):
    sal = preparar(tmp_path, {"USA"})
    assert not (sal / "KEN").exists() and (sal / "USA/precip_2.json.gz").is_file()
    assert (sal / "MUNDO/precip_1.json.gz").is_file()


def test_nombres_de_producto_sin_espanol():
    # H-F3-1: la prueba distingue los nombres viejos de los nuevos
    for viejo, nuevo in PRODUCTO_EN.items():
        assert ESPANOL.search(viejo), viejo
        assert not ESPANOL.search(nuevo), nuevo


def test_traducir_meta_y_manifiesto(tmp_path):
    import hashlib
    meta = {"variables": {"precip": {"productos": [{"producto": "GPM IMERG Late Run, diario agregado a mes en UTC (GPM_3IMERGDL)", "version": "07B"}]}}}
    (tmp_path / "meta.json").write_text(json.dumps(meta), encoding="utf-8")
    man = {"variables": meta["variables"], "archivos": {"meta.json": {"bytes": 1, "sha256": "x"}, "COL/a.json.gz": {"bytes": 5, "sha256": "y"}}, "total_bytes": 6}
    (tmp_path / "manifiesto.json").write_text(json.dumps(man), encoding="utf-8")
    assert traducir_productos(tmp_path) == ["meta.json", "manifiesto.json"]
    for n in ("meta.json", "manifiesto.json"):
        d = json.loads((tmp_path / n).read_text(encoding="utf-8"))
        assert not ESPANOL.search(d["variables"]["precip"]["productos"][0]["producto"])
    m = json.loads((tmp_path / "manifiesto.json").read_text(encoding="utf-8"))
    b = (tmp_path / "meta.json").read_bytes()
    assert m["archivos"]["meta.json"] == {"bytes": len(b), "sha256": hashlib.sha256(b).hexdigest()} and m["total_bytes"] == len(b) + 5
