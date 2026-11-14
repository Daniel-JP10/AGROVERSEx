# asistido por SI: Cursor (agente), escritura y revisión de código; núcleo del gemelo digital en el hackatón
"""Documento de salida del gemelo (JSON y, opcionalmente, SQLite) según contratos/gemelo_api.md."""
import dataclasses
import hashlib
import json
import math
import sqlite3
import subprocess
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

from gemelo.entrada import VERSION_CONTRATO, Entrada
from gemelo.simulador import VERSION_MODELO, Ensamble

AVISO_SIMULADO = ("Todos los resultados son simulados (naturaleza 'simulado'): estiman tendencias y compromisos "
                  "entre estrategias, no son mediciones ni garantías de cosecha.")
AVISO_EQUILIBRIO = ("Carbono: se supone que el suelo está en equilibrio con la estrategia de referencia (SUPUESTO); "
                    "los cambios de carbono se leen como diferencias frente a ese manejo, no como tendencia absoluta.")


def limpiar(obj):
    """Convierte a tipos JSON: numpy -> Python, NaN/inf -> None, dataclasses -> dict."""
    if isinstance(obj, dict):
        return {str(k): limpiar(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [limpiar(v) for v in obj]
    if isinstance(obj, np.ndarray):
        return limpiar(obj.tolist())
    if isinstance(obj, (np.bool_, bool)):
        return bool(obj)
    if isinstance(obj, (np.integer,)):
        return int(obj)
    if isinstance(obj, (float, np.floating)):
        v = float(obj)
        return v if math.isfinite(v) else None
    if dataclasses.is_dataclass(obj) and not isinstance(obj, type):
        return limpiar(dataclasses.asdict(obj))
    if isinstance(obj, Path):
        return str(obj)
    return obj


def commit_git() -> str | None:
    try:
        r = subprocess.run(["git", "rev-parse", "--short", "HEAD"], capture_output=True, text=True, timeout=5,
                           cwd=Path(__file__).resolve().parent)
        return r.stdout.strip() or None
    except (OSError, subprocess.SubprocessError):
        return None


def huella_parametros(parametros: dict) -> str:
    texto = json.dumps({k: p.a_dict() for k, p in sorted(parametros.items())}, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(texto.encode("utf-8")).hexdigest()[:16]


def diagnostico_carbono(ens: Ensamble) -> dict:
    d = {"equilibrio": ens.equilibrio, "estrategia_referencia": ens.referencia,
         "k2_icbm_anual": float(ens.theta.parametros["cn.k2_anual"].exigir())}
    if ens.carbono_inicial is not None:
        k2 = np.asarray(ens.carbono_inicial["k2"])
        y0 = np.asarray(ens.carbono_inicial["y0"])
        d.update({"k2_efectivo_anual_p10_p50_p90": np.percentile(k2, [10, 50, 90]).round(6).tolist(),
                  "reservorio_joven_inicial_t_ha_p50": float(np.median(y0)),
                  "explicacion": "k2 efectivo = h i / (r O): el valor que deja estable el COS medido bajo la "
                                 "referencia. Si difiere mucho del de ICBM, el suelo (p. ej. un Andisol) estabiliza "
                                 "carbono distinto de los suelos con que se calibró ICBM."})
    return d


def metadatos(entrada: Entrada, ens: Ensamble, semilla: int, tipo: str) -> dict:
    return {
        "version_contrato": VERSION_CONTRATO, "version_modelo": VERSION_MODELO, "tipo": tipo,
        "generado_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"), "commit": commit_git(),
        "semilla": semilla, "huella_parametros": huella_parametros(ens.theta.parametros), "naturaleza": "simulado",
        "paso_tiempo": "diario (calendario nominal de 365 días)", "horizonte_anios": ens.H,
        "miembros": {"estrategias": ens.S, "clima": ens.K, "parametros": ens.P, "total": ens.S * ens.K * ens.P},
        "metodo_eto": ens.metodo_eto, "umbral_lluvia_intensa_mm_dia": ens.p_intensa,
        "umbral_cobertura_protectora": ens.umbral_cobertura, "carbono": diagnostico_carbono(ens),
        "archivo_entrada": entrada.origen.get("archivo"),
    }


def _comparacion(estrategias: list[dict]) -> dict:
    """{indicador: {estrategia: p50}} para tablas y gráficos rápidos."""
    if not estrategias:
        return {}
    return {k: {e["id"]: e["indicadores"][k]["p50"] for e in estrategias}
            for k in estrategias[0]["indicadores"]}


def _avisos(entrada: Entrada, ens: Ensamble, extra: list[str] | None = None) -> list[str]:
    avisos = [AVISO_SIMULADO, entrada.escenario.aviso, *ens.theta.avisos]
    if ens.equilibrio != "ninguno":
        avisos.append(AVISO_EQUILIBRIO)
    if entrada.clima.huecos_rellenos:
        avisos.append(f"Clima: huecos cortos rellenados por interpolación {entrada.clima.huecos_rellenos}")
    if entrada.clima.naturaleza != "observado":
        avisos.append(f"Clima de naturaleza '{entrada.clima.naturaleza}' ({entrada.clima.fuente})")
    return list(dict.fromkeys(a for a in avisos + (extra or []) if a))


def _comun(entrada: Entrada, ens: Ensamble, semilla: int, tipo: str) -> dict:
    return {
        "metadatos": metadatos(entrada, ens, semilla, tipo),
        "lote": dataclasses.asdict(entrada.lote) | {"clima_tipo": entrada.clima_lote},
        "clima": entrada.clima.resumen(),
        "escenario": entrada.escenario.a_dict(entrada.clima),
        "suelo": entrada.suelo.a_dict(),
        "parametros": [{"clave": k, **p.a_dict()} for k, p in sorted(ens.theta.parametros.items())],
    }


def documento_simulacion(entrada: Entrada, ens: Ensamble, estrategias: list[dict]) -> dict:
    return limpiar({**_comun(entrada, ens, int(entrada.simulacion["semilla"]), "simulacion"),
                    "estrategias": estrategias, "comparacion_p50": _comparacion(estrategias),
                    "avisos": _avisos(entrada, ens)})


def documento_optimizacion(entrada: Entrada, resultado: dict) -> dict:
    ens = resultado["ensamble_final"]
    cuerpo = {k: v for k, v in resultado.items() if k not in ("ensamble_final", "avisos")}
    todas = [resultado["linea_base"], *resultado["frente"]]
    return limpiar({**_comun(entrada, ens, int(resultado["busqueda"]["semilla"]), "optimizacion"), **cuerpo,
                    "comparacion_p50": _comparacion(todas), "avisos": _avisos(entrada, ens, resultado["avisos"])})


def guardar_json(doc: dict, ruta: str | Path) -> Path:
    ruta = Path(ruta)
    ruta.parent.mkdir(parents=True, exist_ok=True)
    ruta.write_text(json.dumps(doc, ensure_ascii=False, indent=2, allow_nan=False), encoding="utf-8")
    return ruta


ESQUEMA_SQLITE = """
CREATE TABLE IF NOT EXISTS corrida (
    id INTEGER PRIMARY KEY, tipo TEXT NOT NULL, generado_utc TEXT NOT NULL, version_modelo TEXT NOT NULL,
    semilla INTEGER, huella_parametros TEXT, lote_id TEXT, documento TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS indicador (
    corrida_id INTEGER NOT NULL REFERENCES corrida(id), estrategia_id TEXT NOT NULL, indicador TEXT NOT NULL,
    unidad TEXT, p10 REAL, p50 REAL, p90 REAL, PRIMARY KEY (corrida_id, estrategia_id, indicador));
CREATE TABLE IF NOT EXISTS trayectoria_mensual (
    corrida_id INTEGER NOT NULL REFERENCES corrida(id), estrategia_id TEXT NOT NULL, variable TEXT NOT NULL,
    mes INTEGER NOT NULL, p10 REAL, p50 REAL, p90 REAL,
    PRIMARY KEY (corrida_id, estrategia_id, variable, mes));
"""


def guardar_sqlite(doc: dict, ruta: str | Path) -> int:
    """Añade la corrida a una base SQLite (documento completo + tablas planas para consultas). Devuelve el id."""
    ruta = Path(ruta)
    ruta.parent.mkdir(parents=True, exist_ok=True)
    m = doc["metadatos"]
    estrategias = doc.get("estrategias") or [doc["linea_base"], *doc.get("frente", [])]
    con = sqlite3.connect(str(ruta))
    try:
        con.executescript(ESQUEMA_SQLITE)
        cur = con.execute("INSERT INTO corrida (tipo, generado_utc, version_modelo, semilla, huella_parametros, "
                          "lote_id, documento) VALUES (?, ?, ?, ?, ?, ?, ?)",
                          (m["tipo"], m["generado_utc"], m["version_modelo"], m["semilla"], m["huella_parametros"],
                           doc["lote"]["id"], json.dumps(doc, ensure_ascii=False)))
        cid = cur.lastrowid
        for e in estrategias:
            con.executemany("INSERT INTO indicador VALUES (?, ?, ?, ?, ?, ?, ?)",
                            [(cid, e["id"], k, v.get("unidad"), v["p10"], v["p50"], v["p90"])
                             for k, v in e["indicadores"].items()])
            filas = []
            for var, q in e["trayectoria_mensual"].items():
                for mes in range(len(q["p50"])):
                    filas.append((cid, e["id"], var, mes, q["p10"][mes], q["p50"][mes], q["p90"][mes]))
            con.executemany("INSERT INTO trayectoria_mensual VALUES (?, ?, ?, ?, ?, ?, ?)", filas)
        con.commit()
    finally:
        con.close()
    return cid
