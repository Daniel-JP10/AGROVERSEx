# asistido por SI: Claude Code (Anthropic), pruebas del bloque isométrico del lote (reproducible y georreferenciado)
import json
import os
from pathlib import Path

import numpy as np
import pytest

from lotes_demo import bloque_iso as b

RAIZ = Path(__file__).resolve().parents[2]
CRUDOS = Path(os.environ.get("AGROVERSEX_NASADEM", RAIZ / "datos/crudos/nasadem"))
if not (CRUDOS / b.ZIPS["DEMO-COL-01"]).exists():
    CRUDOS = Path("C:/NASA/AGROVERSEx/datos/crudos/nasadem")
EXPOSICION = RAIZ / "datos/lotes/exposicion_erosiva_lotes.json"
LOTES = RAIZ / "src/web/public/datos/lotes_demo.json"
hay_nasadem = pytest.mark.skipif(not (CRUDOS / b.ZIPS["DEMO-COL-01"]).exists(), reason="sin NASADEM local")


def test_utm_ida_y_vuelta():
    # la inversa devuelve el punto de partida a menos de 1e-7 grados (~1 cm)
    lat, lon = np.array([0.842, 41.165]), np.array([-77.661, -96.477])
    for k, zona in enumerate((18, 14)):
        x, y = b.utm_directa(lat[k], lon[k], zona)
        la, lo = b.utm_inversa(x, y, zona)
        assert abs(la - lat[k]) < 1e-7 and abs(lo - lon[k]) < 1e-7


def test_utm_igual_a_pyproj():
    pyproj = pytest.importorskip("pyproj")
    for lat, lon, epsg in ((0.842, -77.661, 32618), (41.165, -96.477, 32614)):
        xr, yr = pyproj.Transformer.from_crs(4326, epsg, always_xy=True).transform(lon, lat)
        x, y = b.utm_directa(lat, lon, epsg % 100)
        assert abs(x - xr) < 0.01 and abs(y - yr) < 0.01


@pytest.mark.datos_reales
@hay_nasadem
def test_dos_corridas_dan_los_mismos_bytes(tmp_path):
    a = b.main(["--crudos", str(CRUDOS), "--salida", str(tmp_path / "a")])
    c = b.main(["--crudos", str(CRUDOS), "--salida", str(tmp_path / "c")])
    assert a == c
    for sub in ("a", "c"):
        assert (tmp_path / sub / "manifiesto_bloques.json").read_bytes() == (tmp_path / "a" / "manifiesto_bloques.json").read_bytes()
    for nombre in sorted(p.name for p in (tmp_path / "a").iterdir()):
        assert (tmp_path / "a" / nombre).read_bytes() == (tmp_path / "c" / nombre).read_bytes(), nombre


@pytest.mark.datos_reales
@hay_nasadem
@pytest.mark.parametrize("lote", ["DEMO-COL-01", "DEMO-USA-01"])
def test_lectura_hgt_igual_a_datos(lote):
    # el píxel HGT más cercano al centro es exactamente el elevacion_centro_m de Datos: lectura y georreferencia bien
    rel = json.loads(EXPOSICION.read_text(encoding="utf-8"))["lotes"][lote]["relieve_nasadem_30m"]
    l = next(x for x in json.loads(LOTES.read_text(encoding="utf-8"))["lotes"] if x["lote_id"] == lote)
    arr, lat_sur, lon_oeste = b.leer_hgt(CRUDOS / b.ZIPS[lote])
    f = int(round((lat_sur + 1 - l["lat"]) * 3600))
    c = int(round((l["lon"] - lon_oeste) * 3600))
    assert arr[f, c] == rel["elevacion_centro_m"]


@pytest.mark.datos_reales
@hay_nasadem
@pytest.mark.parametrize("lote", [
    pytest.param("DEMO-COL-01", marks=pytest.mark.xfail(strict=True, reason=(
        "desfase declarado: el centro del perfil es bilineal (2937,8 m) y Datos tomó el píxel más cercano (2936 m); "
        "con pendiente de 0,08 m/m medio píxel da 1,8 m"))),
    "DEMO-USA-01",
])
def test_centro_del_perfil_igual_a_datos(lote, tmp_path):
    b.main(["--crudos", str(CRUDOS), "--salida", str(tmp_path)])
    perfil = json.loads((tmp_path / f"perfil_{lote}.json").read_text(encoding="utf-8"))
    rel = json.loads(EXPOSICION.read_text(encoding="utf-8"))["lotes"][lote]["relieve_nasadem_30m"]
    assert perfil["distancia_m"][perfil["indice_centro"]] == 0
    assert abs(perfil["elevacion_centro_m"] - rel["elevacion_centro_m"]) <= 1.0


def test_manifiesto_publicado_coincide_con_los_archivos():
    # el SHA-256 del manifiesto vale para los bytes que quedan en public/lotes (fin de línea LF)
    import hashlib
    carpeta = RAIZ / "src/web/public/lotes"
    man = json.loads((carpeta / "manifiesto_bloques.json").read_text(encoding="utf-8"))
    for lote in man["lotes"].values():
        for nombre, sha in lote["archivos"].items():
            assert hashlib.sha256((carpeta / nombre).read_bytes()).hexdigest() == sha, nombre
    assert b"\r\n" not in (carpeta / "manifiesto_bloques.json").read_bytes()
