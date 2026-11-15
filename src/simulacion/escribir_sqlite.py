# asistido por SI: Claude Code (Anthropic), escritura y revisión de código; base del prototipo migrada en el hackatón
"""Orquesta los módulos del generador y escribe agroversex.sqlite (INICIAR §8.3, §8.4), con hash de contenido."""
import argparse
import hashlib
import json
import os
import sqlite3
import subprocess
import sys
import time
from concurrent.futures import ProcessPoolExecutor
from dataclasses import fields
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

from simulacion import agua as m_agua, clima as m_clima, config, lotes as m_lotes, rotaciones, suelo, variables
from simulacion import vegetacion
from simulacion.condicion import tabla_anual
from simulacion.referencias import cargar as ref
from simulacion.tiempo import dias_del_mes
from simulacion.variables import INT_NULO, VARIABLES, a_entero, de_entero

N = config.N_MESES
TABLAS_COMPARTIDAS = ("unidad", "estatico", "clase_fraccion", "variable", "fuente", "metadatos")
COROPLETA = ("precip", "t2m", "sm_sup")  # SUPUESTO: la fase 3 confirma las variables de coropleta por defecto
EST_COLS = ("silt_0_30", "clay_0_30", "sand_0_30", "phh2o_0_30", "soc_0_30", "bdod_0_30", "elev_max", "elev_min")
DECISIONES = "15.2-C, 15.2-G, 15.2-I, D-007, D-008, D-010"
SUPUESTOS_CLAVE = {**m_agua.METADATOS, "dias_calor": "PENDIENTE (sin umbral con ficha, DEP-F1-9)",
                   "erosion": "PENDIENTE: sin pendiente de NASADEM a 30 m; RUSLE con relieve GMTED2010",
                   "coropleta_por_defecto": "SUPUESTO precip, t2m, sm_sup (la fase 3 confirma)"}


def _uri(ruta, modo):
    return f"file:{Path(ruta).as_posix()}?mode={modo}"


def copiar_geo(con, ruta_geo, ids=None) -> None:
    """ATTACH en solo lectura e INSERT ... SELECT con columnas explícitas. Falla si un id de variable choca."""
    con.execute("CREATE TEMP TABLE sel(id TEXT PRIMARY KEY)")
    con.execute("ATTACH DATABASE ? AS geo", (_uri(ruta_geo, "ro"),))
    if ids is None:
        con.execute("INSERT INTO sel SELECT id FROM geo.unidad")
    else:
        con.executemany("INSERT INTO sel VALUES(?)", [(i,) for i in ids])
    for t in TABLAS_COMPARTIDAS:
        origen = {r[1] for r in con.execute(f"PRAGMA geo.table_info({t})")}
        # Solo columnas explícitas presentes en ambos lados (un geo.sqlite antiguo puede no traer las bbox)
        cols = [r[1] for r in con.execute(f"PRAGMA main.table_info({t})") if r[1] in origen]
        lista = ", ".join(cols)
        filtro = {"unidad": "WHERE id IN (SELECT id FROM sel)",
                  "estatico": "WHERE unidad_id IN (SELECT id FROM sel)",
                  "clase_fraccion": "WHERE unidad_id IN (SELECT id FROM sel)"}.get(t, "")
        con.execute(f"INSERT INTO main.{t}({lista}) SELECT {lista} FROM geo.{t} {filtro}")
    con.commit()
    con.execute("DETACH DATABASE geo")


def _insertar_variables(con) -> None:
    previas = {r[0] for r in con.execute("SELECT id FROM variable")}
    nuevas = list(VARIABLES.values()) + list(suelo.VARIABLES_ANUAL.values())
    choque = previas & {v.id for v in nuevas}
    if choque:
        raise ValueError(f"id de variable repetido entre fase 1 y fase 2: {sorted(choque)}")
    con.executemany(
        "INSERT INTO variable(id, nombre, unidad_medida, escala, desplazamiento, relleno, valido_min, valido_max, "
        "producto, version, inicio, fin, nivel_dato, etiqueta, fuente_id) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
        [(v.id, v.columna, v.unidad_medida, v.escala, v.desplazamiento, v.relleno, v.valido_min, v.valido_max,
          v.producto, v.version, v.inicio, v.fin, v.nivel_dato, v.etiqueta, v.fuente_id) for v in nuevas])
    # Las fuentes de las variables de la fase 2 son fichas EV-* (o la simulación); sin ellas el JOIN quedaría vacío
    for fid in sorted({v.fuente_id for v in nuevas}):
        cita = "simulación de demo (D-010)" if fid == "demo" else f"fichas {fid}-* del catálogo de evidencia"
        con.execute("INSERT OR IGNORE INTO fuente(id, cita, ficha_ev) VALUES(?,?,?)", (fid, cita, fid))


def _horas_mes():
    return np.array([dias_del_mes(m) for m in range(N)]) * 24.0


def a_mm_h(mm_mes, frac=1.0):
    """mm del generador a mm/h del contrato IMERG (INICIAR §5.2): divide por las horas cubiertas (mes parcial: frac<1)."""
    return np.asarray(mm_mes, float) / (_horas_mes() * np.maximum(frac, 1e-9))


def _entero(col, arr, n):
    arr = np.broadcast_to(np.asarray(arr), (n, N))
    if col in VARIABLES:
        return a_entero(arr, VARIABLES[col])
    x = arr.astype(float)
    return np.where(np.isnan(x), INT_NULO, np.rint(x)).astype(np.int32)


def _bloque(ids, g, est, cols_mensual):
    """Todo el cálculo de un bloque de unidades (puro: no toca la base). Devuelve matrices y filas anuales."""
    n = len(ids)
    sl = slice(None)
    est_corto = est.rename(columns=lambda c: c.removesuffix("_0_30"))
    c = m_clima.generar_clima(ids, sl, geo=g)
    nd = vegetacion.generar_ndvi(c, sl, g, est_corto)
    a = m_agua.generar_agua(c, nd, sl, geo=g, estatico=est_corto)
    ev = vegetacion.empaquetar_et_lst(c, a, sl, g, nd)
    dsuelo, metodo = suelo.dias_suelo_mensual(nd["ndvi"], None)
    campos = {f.name: getattr(c, f.name) for f in fields(c)}
    for k in ("ndvi", "ndvi_p10", "ndvi_p90", "ndvi_frac"):
        campos[k] = nd[k]
    for k in ("et", "et_p10", "et_p90", "et_frac", "lst_dia", "lst_err", "lst_frac"):
        campos[k] = ev[k]
    for k in ("sm_sup", "sm_raiz", "sm_err", "sm_frac", "sm_fuente", "sm_qual", "tws", "tws_err", "tws_frac"):
        campos[k] = getattr(a, k)
    campos["dias_suelo_expuesto"], campos["suelo_metodo"] = dsuelo, metodo
    campos["dias_calor"] = suelo.dias_calor(c.t2m_max, None)
    campos["bandera_motivo"] = c.bandera | nd["bandera"] | ev["bandera"] | a.bandera
    for k in ("precip", "precip_err"):
        campos[k] = a_mm_h(campos[k], c.precip_frac)
    mens = np.stack([_entero(col, campos[col], n) for col in cols_mensual], axis=-1).reshape(n * N, -1)

    igbp, _ = suelo.cobertura_igbp(g, g.get("koppen", -1), est)
    serie = suelo.serie_suelo_anual(c, nd, g, est, igbp)
    an = tabla_anual(ids, igbp, serie)
    for q in ("p05", "p50", "p95"):  # erosión a entero escalado (variable.escala); INT_NULO pasa a NULL al escribir
        k = f"erosion_{q}"
        an[k] = a_entero(an[k].to_numpy(), suelo.VARIABLES_ANUAL[k])
    sin_enso = [u for u, s in zip(ids, c.enso_no_documentado) if s]
    return ids, mens, an, sin_enso


def _a_filas(ids, mens, extra_idx=None):
    k = mens.shape[1]
    obj = np.empty((len(ids) * N, k + 2), dtype=object)
    obj[:, 0] = np.repeat(np.asarray(ids, dtype=object), N)
    obj[:, 1] = np.tile(np.arange(N), len(ids))
    cuerpo = mens.astype(object)
    cuerpo[mens == INT_NULO] = None
    obj[:, 2:] = cuerpo
    return obj.tolist()  # .tolist() de un arreglo object ya entrega int de Python


def _escribir_mensual(con, ids, mens, cols):
    q = f"INSERT INTO mensual(unidad_id, mes_id, {', '.join(cols)}) VALUES({', '.join('?' * (len(cols) + 2))})"
    for i in range(0, len(ids), 100):  # sub-bloques: el máximo de filas Python vivas es 100·323
        con.executemany(q, _a_filas(ids[i:i + 100], mens[i * N:(i + 100) * N]))


def _escribir_anual(con, an):
    cols = list(an.columns)
    obj = an.astype(object).where(an.notna(), None)
    obj = obj.replace(INT_NULO, None)
    con.executemany(f"INSERT INTO anual({', '.join(cols)}) VALUES({', '.join('?' * len(cols))})",
                    obj.to_numpy(object).tolist())


def _referencias(con, geo):
    enso = ref.cargar_enso()
    con.executemany("INSERT INTO enso VALUES(?,?,?)",
                    [(int(r.mes_id), None if np.isnan(r.oni) else float(r.oni),
                      None if np.isnan(r.roni) else float(r.roni)) for r in enso.itertuples()])
    ev = ref.cargar_eventos()
    cols = ["id", "tipo", "inicio", "fin", "region_texto", "magnitud_texto", "url", "etiqueta"]
    con.executemany("INSERT INTO evento VALUES(?,?,?,?,?,?,?,?)", [tuple(e[c] for c in cols) for e in ev])
    # Intensidad en desviaciones estándar (INTENSIDAD_EVENTO_SD con el signo del tipo); mismo criterio que el generador
    iso3, adm1 = geo.iso3.to_numpy(), geo["adm1"].to_numpy(object)
    for e in ev:
        paises = m_clima._EV_ISO3.get(e["id"])
        sp, st = m_clima._efecto_evento(e["tipo"])
        if not paises or not (sp or st):
            continue
        if isinstance(paises, dict):
            f = np.zeros(len(iso3), bool)
            for iso, lista in paises.items():
                f |= (iso3 == iso) & np.isin(adm1, lista)
        else:
            f = np.isin(iso3, paises)
        con.executemany("INSERT INTO evento_unidad VALUES(?,?,?)",
                        [(e["id"], u, float(m_clima.INTENSIDAD_EVENTO_SD * (sp or st))) for u in geo.index[f]])
    con.executemany("INSERT INTO sistema_rotacion VALUES(?,?,?,?,?,?,?)", rotaciones.filas_sistema_rotacion())
    con.executemany("INSERT INTO efecto_antecesor VALUES(?,?,?,?,?,?,?,?,?)", rotaciones.filas_efecto_antecesor())
    con.executemany("INSERT INTO cultivo VALUES(" + ",".join("?" * 18) + ")", rotaciones.filas_cultivo())
    con.executemany("INSERT INTO regla_sucesion VALUES(?,?,?,?,?,?)", rotaciones.filas_regla_sucesion())


def _mensual_desde_base(con, ids):
    """Series que usa lotes.serie_diaria, leídas de `mensual` ya escrita (coherentes con la tabla)."""
    out = {}
    for u in ids:
        filas = con.execute("SELECT ndvi, sm_raiz, precip, dias_helada FROM mensual WHERE unidad_id=? ORDER BY mes_id",
                            (u,)).fetchall()
        a = np.array(filas, dtype=float).reshape(-1, 4)
        out[u] = {"ndvi": de_entero(np.where(np.isnan(a[:, 0]), INT_NULO, a[:, 0]), VARIABLES["ndvi"]),
                  "sm_raiz": de_entero(np.where(np.isnan(a[:, 1]), INT_NULO, a[:, 1]), VARIABLES["sm_raiz"]),
                  # la base guarda mm/h; serie_diaria espera mm/mes
                  "precip": de_entero(np.where(np.isnan(a[:, 2]), INT_NULO, a[:, 2]), VARIABLES["precip"]) * _horas_mes(),
                  "dias_helada": a[:, 3]}
    return out


def escribir_lotes(con, geo, n_por_zona: int = 50) -> dict:
    """Cablea lote, lote_diario y lote_ventana con lotes.py. Solo zonas con alguna unidad en `geo`."""
    zonas = m_lotes.cargar_zonas()
    dias = np.arange(m_lotes.N_DIAS)
    cuenta = {"lote": 0, "lote_diario": 0, "lote_ventana": 0}
    esc = {k: VARIABLES[k] for k in ("ndvi", "nbr2", "sm_verdad", "sm_sensor")}
    for zona in sorted(zonas):
        if not any(u in geo.index for u in zonas[zona]["unidades"]):
            continue
        us = zonas[zona]["unidades"]
        con.executemany("INSERT INTO zona_demo VALUES(?,?)", [(u, zona) for (u,) in con.execute(
            f"SELECT id FROM unidad WHERE id IN ({','.join('?' * len(us))}) OR padre_id IN ({','.join('?' * len(us))})",
            us + us)])
        ls = m_lotes.generar_lotes(zona, n_por_zona, geo=geo, zonas=zonas)
        mu = _mensual_desde_base(con, sorted({l["unidad_id"] for l in ls}))
        for l in ls:
            m = dict(mu[l["unidad_id"]], elev_media=float(geo.elev_media.loc[l["unidad_id"]]))
            con.execute("INSERT INTO lote VALUES(?,?,?,?,?)",
                        (l["id"], l["unidad_id"], l["geom_wkt"], l["cultivo_actual"], l["zona_demo"]))
            s = m_lotes.serie_diaria(l, m)
            cols = [np.broadcast_to(a_entero(s[k], esc[k]), dias.shape) for k in esc] + [s["nube"].astype(np.int32)]
            mat = np.stack(cols, axis=-1).astype(object)
            mat[:, :4][np.stack(cols[:4], -1) == INT_NULO] = None
            filas = np.empty((len(dias), 7), dtype=object)
            filas[:, 0], filas[:, 1], filas[:, 2:] = l["id"], dias, mat
            con.executemany("INSERT INTO lote_diario VALUES(?,?,?,?,?,?,?)", filas.tolist())
            ven = m_lotes.detectar_ventana(s["ndvi"], s["nbr2"], dias, s["ndvi_verdad"])
            con.executemany("INSERT INTO lote_ventana VALUES(?,?,?,?,?,?,?)",
                            [(l["id"], str(w["anio"]), w["inicio"], w["fin"], w["error_semanas"],
                              int(w["detectada"]), w["confianza"]) for w in ven])
            cuenta["lote"] += 1
            cuenta["lote_diario"] += len(dias)
            cuenta["lote_ventana"] += len(ven)
    con.commit()
    return cuenta


def crear_indices(con) -> None:
    con.execute("CREATE INDEX mensual_mes ON mensual(mes_id, unidad_id)")
    for v in COROPLETA:
        con.execute(f"CREATE INDEX mensual_mes_{v} ON mensual(mes_id, unidad_id, {v})")
    con.execute("CREATE INDEX lote_unidad ON lote(unidad_id)")
    con.commit()


def hash_contenido(ruta: Path) -> str:
    """SHA-256 de las filas de todas las tablas (menos metadatos) en orden de clave primaria."""
    con = sqlite3.connect(_uri(ruta, "ro"), uri=True)
    h = hashlib.sha256()
    try:
        tablas = [r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table' AND name<>'metadatos' "
                                            "AND name NOT LIKE 'sqlite_%' ORDER BY name")]
        for t in tablas:
            info = list(con.execute(f"PRAGMA table_info({t})"))
            pk = [r[1] for r in sorted((r for r in info if r[5]), key=lambda r: r[5])] or [r[1] for r in info]
            h.update(f"#{t}:{','.join(r[1] for r in info)}\n".encode())
            for fila in con.execute(f"SELECT * FROM {t} ORDER BY {', '.join(pk)}"):
                h.update(repr(fila).encode())
    finally:
        con.close()
    return h.hexdigest()


def _sha256_archivo(ruta) -> str:
    h = hashlib.sha256()
    with open(ruta, "rb") as f:
        for b in iter(lambda: f.read(1 << 22), b""):
            h.update(b)
    return h.hexdigest()


def _commit() -> str:
    try:
        return subprocess.run(["git", "rev-parse", "HEAD"], cwd=Path(__file__).parent, capture_output=True,
                              text=True, check=True).stdout.strip()
    except Exception:
        return "desconocido"


def escribir_metadatos(con, hash: str, versiones: dict) -> None:
    filas = {"hash_contenido": hash, "semilla": str(config.SEMILLA), "fecha_generacion":
             datetime.now(timezone.utc).isoformat(timespec="seconds"), "FECHA_FIN_DIARIA": config.FECHA_FIN_DIARIA.isoformat(),
             "decisiones": DECISIONES, "supuestos_pendientes": json.dumps(SUPUESTOS_CLAVE, ensure_ascii=False),
             "versiones": json.dumps({"python": sys.version.split()[0], "numpy": np.__version__,
                                      "pandas": pd.__version__}), **{k: str(v) for k, v in versiones.items()}}
    con.executemany("INSERT OR REPLACE INTO metadatos VALUES(?,?)", filas.items())
    con.commit()


def construir_agroversex(ruta_geo: Path, ruta_salida: Path, muestra: int | None = None, tam_bloque: int = 2000,
                         iso3: str | None = None, workers: int = 1, con_lotes: bool = True) -> dict:
    t0 = time.time()
    ruta_geo, ruta_salida = Path(ruta_geo), Path(ruta_salida)
    ruta_salida.unlink(missing_ok=True)
    geo = m_clima.cargar_geo(ruta_geo)
    if iso3:
        geo = geo[geo.iso3 == iso3]
    geo = geo.sort_index()
    if muestra:
        geo = geo.iloc[:muestra]
    ids = list(geo.index)

    con = sqlite3.connect(_uri(ruta_salida, "rwc"), uri=True)
    con.execute("PRAGMA journal_mode=OFF")
    con.execute("PRAGMA synchronous=OFF")
    con.execute("PRAGMA cache_size=-1048576")
    variables.crear_esquema(con)
    copiar_geo(con, ruta_geo, ids)
    _insertar_variables(con)
    est = pd.read_sql("SELECT unidad_id, variable_id, media FROM estatico", con).pivot(
        index="unidad_id", columns="variable_id", values="media").reindex(index=ids, columns=list(EST_COLS))
    cols = [r[1] for r in con.execute("PRAGMA table_info(mensual)")][2:]

    # TWS promedia por celda de 3°: un bloque solo se cierra en el borde de una celda, para que el resultado
    # no dependa del tamaño de bloque
    celda = pd.Series(m_agua.celda_3grados(geo.punto_lat, geo.punto_lon), index=ids)
    orden = celda.sort_values(kind="stable").index.tolist()
    bloques, actual = [], []
    for k, u in enumerate(orden):
        actual.append(u)
        if len(actual) >= tam_bloque and (k + 1 == len(orden) or celda[orden[k + 1]] != celda[u]):
            bloques.append(actual)
            actual = []
    if actual:
        bloques.append(actual)
    args = lambda b: (b, geo.loc[b], est.loc[b], cols)
    sin_enso = []
    pool = ProcessPoolExecutor(workers) if workers > 1 else None
    try:
        for i in range(0, len(bloques), max(workers, 1) * 2):
            grupo = bloques[i:i + max(workers, 1) * 2]
            res = (pool.map(_bloque, *zip(*map(args, grupo))) if pool else (_bloque(*args(b)) for b in grupo))
            for b_ids, mens, an, se in res:
                _escribir_mensual(con, b_ids, mens, cols)
                _escribir_anual(con, an)
                sin_enso += se
            con.commit()
    finally:
        if pool:
            pool.shutdown()
    _referencias(con, geo)
    cuenta_lotes = escribir_lotes(con, geo) if con_lotes else {}
    crear_indices(con)
    con.execute("ANALYZE")
    con.commit()
    con.close()

    h = hash_contenido(ruta_salida)
    con = sqlite3.connect(_uri(ruta_salida, "rw"), uri=True)
    escribir_metadatos(con, h, {"commit": _commit(), "geo_sqlite_sha256": _sha256_archivo(ruta_geo),
                                "muestra": muestra or "", "iso3": iso3 or "", "tam_bloque": tam_bloque,
                                "B_ENSO_NO_DOCUMENTADO": f"{len(sin_enso)} de {len(ids)} unidades sin teleconexión "
                                                         "documentada (SUPUESTO: sin forzante ENSO)"})
    filas = {t: con.execute(f"SELECT count(*) FROM {t}").fetchone()[0] for t in
             [r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")]}
    con.close()
    return {"filas_mensual": filas["mensual"], "filas": filas, "bytes": ruta_salida.stat().st_size,
            "segundos": time.time() - t0, "hash": h, "unidades": len(ids), "lotes": cuenta_lotes}


def main():
    p = argparse.ArgumentParser(prog="python -m simulacion.escribir_sqlite")
    p.add_argument("--geo", default=os.environ.get("AGROVERSEX_GEO_SQLITE") or str(config.GEO_SQLITE))
    p.add_argument("--salida", default=str(config.AGROVERSEX_SQLITE))
    p.add_argument("--iso3")
    p.add_argument("--muestra", type=int)
    p.add_argument("--bloque", type=int, default=2000)
    p.add_argument("--workers", type=int, default=1)
    a = p.parse_args()
    r = construir_agroversex(Path(a.geo), Path(a.salida), a.muestra, a.bloque, a.iso3, a.workers)
    print(json.dumps(r, indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()
