# asistido por SI: Claude Code, lectura y validación de forzantes POWER e IMERG por lote (T-D5 Parte B)
import json
import math
from datetime import date, timedelta
from pathlib import Path


def leer_power_csv(ruta: Path) -> dict[str, list[float]]:
    # CSV de POWER con cabecera -BEGIN/-END HEADER-; -999 es faltante y pasa a NaN
    lineas = Path(ruta).read_text(encoding="utf-8").splitlines()
    i = lineas.index("-END HEADER-")
    cols = lineas[i + 1].split(",")
    d = {c: [] for c in cols}
    for l in lineas[i + 2:]:
        for c, v in zip(cols, l.split(",")):
            x = float(v)
            d[c].append(float("nan") if x == -999 else x)
    return d


def validar_power(d):
    for lo, hi in zip(d["T2M_MIN"], d["T2M_MAX"]):
        if lo > hi:
            raise ValueError("T2M_MIN mayor que T2M_MAX")
    if any(p < 0 for p in d["PRECTOTCORR"]):
        raise ValueError("PRECTOTCORR negativa")


def escribir_imerg_csv(jsonl: Path, salida: Path, ini: str, fin: str):
    # una fila por día UTC; sin dato queda vacío (nunca 0)
    reg = {}
    for l in Path(jsonl).read_text().splitlines():
        if l:
            r = json.loads(l)
            reg[r["dia"]] = r
    filas = ["FECHA_UTC,YEAR,DOY,IMERG_PRECIP_MM_DIA,IMERG_N_MUESTRAS"]
    d = date.fromisoformat(ini)
    while d <= date.fromisoformat(fin):
        r = reg.get(d.isoformat(), {})
        p, c = r.get("p"), r.get("cnt")
        filas.append(f"{d.isoformat()},{d.year},{d.timetuple().tm_yday},"
                     f"{'' if p is None else p},{'' if c is None else c}")
        d += timedelta(days=1)
    Path(salida).write_text("\n".join(filas) + "\n", encoding="utf-8")
