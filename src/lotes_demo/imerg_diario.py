# asistido por SI: Claude Code, lectura puntual de IMERG Final V07 diario por OPeNDAP (T-D5 Parte B)
"""Precipitación diaria IMERG Final V07 (GPM_3IMERGDF.07) en la celda de 0,1 grados de un lote.

Día UTC (producto 3B-DAY: 00:00 a 23:59:59 UTC). Unidad: mm/día. Relleno -9999.9 se vuelve NaN, nunca 0.
"""
import json
import math
import re
import sys
from concurrent.futures import ThreadPoolExecutor
from datetime import date, timedelta
from pathlib import Path

BASE = "https://gpm1.gesdisc.eosdis.nasa.gov/opendap/GPM_L3/GPM_3IMERGDF.07"


def indices_celda(lat: float, lon: float) -> tuple[int, int]:
    # rejilla 0,1 grados con borde en -180 y -90: la celda es el piso, no el redondeo
    if not (-90 <= lat < 90 and -180 <= lon < 180):
        raise ValueError("coordenada fuera de rango")
    return math.floor((lon + 180) / 0.1), math.floor((lat + 90) / 0.1)


def url_dia(dia: str, i_lon: int, j_lat: int) -> str:
    d = dia.replace("-", "")
    f = f"3B-DAY.MS.MRG.3IMERG.{d}-S000000-E235959.V07B.nc4"
    q = (f"precipitation[0:0][{i_lon}:{i_lon}][{j_lat}:{j_lat}],"
         f"precipitation_cnt[0:0][{i_lon}:{i_lon}][{j_lat}:{j_lat}]")
    return f"{BASE}/{dia[:4]}/{dia[5:7]}/{f}.ascii?{q}"


def parsear_ascii(texto: str) -> tuple[float, float]:
    # devuelve (precipitación mm/día, conteo de muestras); relleno a NaN
    vals = {}
    for linea in texto.splitlines():
        m = re.match(r"(precipitation_cnt|precipitation)\.\1\[.*\], (-?[\d.eE+-]+)$", linea.strip())
        if m:
            v = float(m.group(2))
            vals[m.group(1)] = float("nan") if v <= -9999 else v
    if "precipitation" not in vals:
        raise ValueError("respuesta sin precipitation")
    return vals["precipitation"], vals.get("precipitation_cnt", float("nan"))


def _pedir(sesion, dia, i, j, intentos=4):
    for k in range(intentos):
        try:
            r = sesion.get(url_dia(dia, i, j), timeout=90)
            if r.status_code == 200:
                return parsear_ascii(r.text)
        except Exception:
            pass
    return None


def descargar(lote_id, lat, lon, ini, fin, salida: Path, hilos=96):
    # reanuda: salta los días ya escritos en el jsonl
    import earthaccess
    earthaccess.login(strategy="netrc")
    ses = earthaccess.get_requests_https_session()
    i, j = indices_celda(lat, lon)
    salida.parent.mkdir(parents=True, exist_ok=True)
    hechos = set()
    if salida.exists():
        hechos = {json.loads(x)["dia"] for x in salida.read_text().splitlines() if x}
    d, dias = date.fromisoformat(ini), []
    while d <= date.fromisoformat(fin):
        if d.isoformat() not in hechos:
            dias.append(d.isoformat())
        d += timedelta(days=1)
    with ThreadPoolExecutor(hilos) as ex, salida.open("a") as f:
        for dia, res in zip(dias, ex.map(lambda x: _pedir(ses, x, i, j), dias)):
            if res is None:
                continue  # queda sin escribir: se reintenta al reanudar
            f.write(json.dumps({"dia": dia, "p": None if math.isnan(res[0]) else res[0],
                                "cnt": None if math.isnan(res[1]) else res[1]}) + "\n")
            f.flush()
    print(lote_id, "pendientes tras la corrida:", len(dias) - sum(1 for _ in salida.open()) + len(hechos))


if __name__ == "__main__":
    lote, lat, lon, ini, fin, out = sys.argv[1:7]
    descargar(lote, float(lat), float(lon), ini, fin, Path(out))
