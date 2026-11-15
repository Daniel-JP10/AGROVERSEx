# asistido por SI: Claude Code (Anthropic), climatología mensual de heladas de la estación GHCN como resumen derivado (D-038)
"""Agrega al resumen validacion_temperatura_ipiales.json la climatología mensual de heladas de la estación.

El CSV crudo de GHCN-Daily (fuera de EE. UU., Resolución 40 de la OMM) vive solo en C:/NASA/compartir/ghcn/
y no se versiona. El repo guarda solo estos agregados, con su aviso de uso no comercial.
Uso: python -m lotes_demo.helada_estacion <csv_ghcn> <validacion.json> [umbral_c ...]
"""
import json
import sys
from pathlib import Path

import pandas as pd

CSV_LOCAL = Path("C:/NASA/compartir/ghcn/COM00080370.csv")
AVISO_USO = ("GHCN-Daily: dato de estación fuera de EE. UU. intercambiado bajo la Resolución 40 de la OMM. "
             "Solo agregados derivados, para uso no comercial (investigación y educación). El CSV crudo no se "
             "redistribuye y este resumen queda fuera de la licencia abierta del repositorio (D-038).")


def leer_tmin(ruta: Path, periodo: list[str]) -> tuple[pd.DataFrame, dict, int]:
    """TMIN diaria en °C dentro del periodo; descarta los días con bandera de calidad (segundo campo de TMIN_ATTRIBUTES)."""
    df = pd.read_csv(ruta, usecols=["STATION", "DATE", "LATITUDE", "LONGITUDE", "ELEVATION", "TMIN", "TMIN_ATTRIBUTES"],
                     dtype={"TMIN_ATTRIBUTES": str})
    meta = df.iloc[0]
    df["DATE"] = pd.to_datetime(df["DATE"])
    df = df[(df.DATE >= periodo[0]) & (df.DATE <= periodo[1])]
    q = df.TMIN_ATTRIBUTES.fillna(",,").str.split(",").str[1].str.strip()
    rechazados = int((df.TMIN.notna() & (q != "")).sum())
    df = df[df.TMIN.notna() & (q == "")]
    return df.assign(tmin_c=df.TMIN.to_numpy(float) / 10.0), meta, rechazados


def clave_umbral(u: float) -> str:
    return f"{float(u):.1f}"


def climatologia(ruta: Path, periodo: list[str], umbrales=(0.0,)) -> dict:
    """Por umbral y mes: días del periodo, días con dato y días con TMIN <= umbral."""
    df, meta, rechazados = leer_tmin(ruta, periodo)
    todos = pd.date_range(periodo[0], periodo[1], freq="D")
    meses = df.DATE.dt.month.to_numpy()
    por_umbral = {}
    for u in umbrales:
        por_umbral[clave_umbral(u)] = [
            {"mes": m, "dias_periodo": int((todos.month == m).sum()), "dias_con_dato": int((meses == m).sum()),
             "dias_helada": int(((meses == m) & (df.tmin_c.to_numpy() <= float(u))).sum())}
            for m in range(1, 13)]
    return {"fuente_csv": ruta.name, "estacion": str(meta.STATION), "lat": float(meta.LATITUDE),
            "lon": float(meta.LONGITUDE), "elevacion_m": float(meta.ELEVATION), "periodo": list(periodo),
            "rechazados_bandera_tmin": rechazados, "por_umbral_c": por_umbral}


def ampliar(ruta_csv: Path, ruta_json: Path, umbrales=(0.0,)) -> dict:
    """Escribe el bloque en el resumen sin tocar sus otros campos ni su formato."""
    v = json.loads(ruta_json.read_text(encoding="utf-8"))
    v["climatologia_helada_estacion"] = climatologia(ruta_csv, v["periodo"], umbrales)
    v["aviso_uso"] = AVISO_USO
    ruta_json.write_text(json.dumps(v, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    return v


if __name__ == "__main__":
    us = tuple(float(x) for x in sys.argv[3:]) or (0.0,)
    ampliar(Path(sys.argv[1]), Path(sys.argv[2]), us)
