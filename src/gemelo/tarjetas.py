# asistido por SI: Cursor (agente), escritura y revisión de código; núcleo del gemelo digital en el hackatón
# asistido por SI: Antigravity (agente), exposición de limitación SoilGrids Andisol en riesgos (D-030)
# asistido por SI: Claude Code (Opus 5.5), vacíos de helada subestimada y de fuente de lluvia alterna (bloque 2)
"""Tarjeta de cinco secciones por estrategia (contrato v1.1): por_que, evidencia, beneficios, vacios y riesgos.

Contenido estructurado: cada entrada es {clave, parametros, valores, referencias}; Web redacta con el catálogo de
textos.py. Un parámetro con forma {"clave": ...} es una clave anidada que se traduce antes de insertar.

vacios sale de `sensibilidad_supuestos`: cada parámetro SUPUESTO con rango se lleva a sus dos extremos (una sola
muestra central de theta, el resto fijo) y se mira si cambia el orden con pesos iguales o el mejor por objetivo.
"""
import re

import numpy as np

from gemelo import indicadores as ind
from gemelo import prioridades as pr
from gemelo.optimizacion import OBJETIVOS, OBJETIVOS_BASE, a_natural, submuestrear, valores_objetivo
from gemelo.parametros import cargar_catalogo
from gemelo.simulador import ejecutar, reunir_parametros, theta_desde_muestras
from gemelo.textos import clave_unidad

TOLERANCIA = 0.02
SECCIONES = ("por_que", "evidencia", "beneficios", "vacios", "riesgos")
# Indicadores de horizonte que entran en beneficios y riesgos, con el sentido en que son mejores
SENTIDO_INDICADOR = {
    "produccion_relativa_anio": "max", "rendimiento_relativo": "max", "riego_mm_anio": "min",
    "deficit_relativo": "min", "lixiviacion_n_kg_ha_anio": "min", "fertilizante_n_kg_ha_anio": "min",
    "cambio_carbono_t_ha_anio": "max", "lluvia_intensa_sobre_suelo_desnudo_mm_anio": "min",
    "dias_suelo_desnudo_anio": "min", "cobertura_media": "max",
}
_FICHA = re.compile(r"EV-[A-Z]+-\d+")
MAX_MIEMBROS = 600

def _e(c: str, parametros: dict | None = None, valores: dict | None = None, referencias: list | None = None) -> dict:
    return {"clave": c, "parametros": parametros or {}, "valores": valores or {}, "referencias": referencias or []}


def _estrategias(doc: dict) -> list[dict]:
    return doc.get("estrategias") or [doc["linea_base"], *doc.get("frente", [])]


def id_referencia(doc: dict) -> str:
    if doc.get("linea_base"):
        return doc["linea_base"]["id"]
    return doc.get("estrategia_referencia") or _estrategias(doc)[0]["id"]


def objetivos_tarjeta(doc: dict) -> list[str]:
    if doc.get("objetivos"):
        return [o["id"] for o in doc["objetivos"] if o["id"] != "costo"]
    return list(OBJETIVOS_BASE)


def _redondeo(x):
    return None if x is None else float(f"{x:.4g}")


def _mejor(sentido: str, d: float, escala: float) -> int:
    """+1 mejora, -1 empeora, 0 similar (tolerancia relativa)."""
    if abs(d) <= TOLERANCIA * max(abs(escala), 1e-6):
        return 0
    return 1 if (d > 0) == (sentido == "max") else -1


def _por_que(e: dict, base: dict, objetivos: list[str], es_base: bool) -> list[dict]:
    if es_base:
        return [_e("card.why.is_baseline", {"id": e["id"]})]
    out = []
    for o in objetivos:
        x, b = e["metricas"][o], base["metricas"][o]
        if _mejor(OBJETIVOS[o]["sentido"], x - b, b) > 0:
            out.append(_e("card.why.improves", {"objetivo": {"clave": f"objective.{o}"}, "base": _redondeo(b),
                                                 "valor": _redondeo(x), "unidad": _unidad_objetivo(o, e)},
                          {"objetivo": o, "base": b, "valor": x}))
    if e.get("no_dominada_en_evaluacion_final"):
        out.append(_e("card.why.front_member"))
    if not out:
        out.append(_e("card.why.no_improvement", {"tolerancia_pct": int(TOLERANCIA * 100)}))
    return out


def _unidad_objetivo(o: str, e: dict) -> dict:
    return clave_unidad(e["indicadores"].get(OBJETIVOS[o]["indicador"], {}).get("unidad", ""))


def _evidencia(e: dict, doc: dict) -> list[dict]:
    cultivos = sorted({t["cultivo"] for t in e["temporadas"]})
    params = [p for p in doc["parametros"] if any(p["clave"].startswith(f"cultivo.{c}.") for c in cultivos)]
    cuenta = {k: sum(p["etiqueta"] == k for p in params) for k in ("FUENTE", "INFERENCIA", "SUPUESTO")}
    fichas = sorted({p["ficha"] for p in params if p.get("ficha")} | set(_FICHA.findall(e.get("etiqueta") or "")))
    out = [_e("card.evidence.label", {"etiqueta": e.get("etiqueta") or ""}, referencias=_FICHA.findall(
              e.get("etiqueta") or "")),
           _e("card.evidence.parameters", {"n_fuente": cuenta["FUENTE"], "n_inferencia": cuenta["INFERENCIA"],
                                           "n_supuesto": cuenta["SUPUESTO"]}, {"cultivos": cultivos}, fichas)]
    if fichas:
        out.append(_e("card.evidence.references", {"fichas": ", ".join(fichas)}, referencias=fichas))
    for r in doc.get("reglas_sucesion", []):
        if set(r.get("cultivos", [])) & set(cultivos):
            out.append(_e("card.evidence.succession", {"familia": r["familia"], "intervalo_anios": r["intervalo_anios"],
                                                       "referencia": r.get("referencia", "")},
                          referencias=[r.get("referencia", "")]))
    out.append(_e("card.evidence.model", {"n_miembros": e.get("n_miembros")}))
    return out


def _beneficios(e: dict, base: dict, es_base: bool) -> list[dict]:
    out = []
    if not es_base:
        for k, sentido in SENTIDO_INDICADOR.items():
            v, b = e["indicadores"].get(k), base["indicadores"].get(k)
            if not v or not b or v["p50"] is None or b["p50"] is None:
                continue
            d = v["p50"] - b["p50"]
            if _mejor(sentido, d, b["p50"]) > 0:
                out.append(_e("card.benefit.delta", {"indicador": {"clave": f"indicator.{k}.name"}, "delta": d,
                                                     "unidad": clave_unidad(v["unidad"]), "p10": v["p10"],
                                                     "p90": v["p90"]},
                              {"indicador": k, "p10": v["p10"], "p50": v["p50"], "p90": v["p90"],
                               "base_p50": b["p50"], "delta_p50": d}))
    return out or [_e("card.benefit.none")]


def _vacios(e: dict, doc: dict, sens: dict | None) -> list[dict]:
    out = []
    if sens is None:
        out.append(_e("card.gap.not_evaluated"))
    else:
        for p in sens["parametros"]:
            pos = p["posiciones"].get(e["id"])
            if pos and len(set(pos.values())) > 1:
                out.append(_e("card.gap.changes_order", {"parametro": p["clave"], "lo": p["rango"][0],
                                                         "hi": p["rango"][1], "unidad": clave_unidad(p["unidad"]),
                                                         "central": pos["central"], "bajo": pos["bajo"],
                                                         "alto": pos["alto"]},
                              {"parametro": p["clave"], "posiciones": pos,
                               "cambia_mejor_por_objetivo": p["cambia_mejor_por_objetivo"]},
                              [p["referencia"]] if p.get("referencia") else []))
        if not out:
            out.append(_e("card.gap.none_changes"))
    hel = (doc.get("alertas") or {}).get("helada_etapa_sensible") or {}
    u = (hel.get("estrategias", {}).get(e["id"]) or {}).get("umbrales", {})
    sup = sorted(c for c, x in u.items() if x["etiqueta"] == "SUPUESTO")
    if sup:
        out.append(_e("card.gap.frost_threshold_assumed", {"cultivos": ", ".join(sup), "umbral": u[sup[0]]["valor"]},
                      {"cultivos": sup}))
    v = hel.get("validacion")
    if v and v["sesgo_c"] > 0:
        out.append(_e("card.gap.frost_underestimated", {"estacion": v["estacion"], "sesgo": v["sesgo_c"],
                                                         "lo": v["sesgo_c_ic95"][0], "hi": v["sesgo_c_ic95"][1]},
                      {"sesgo_c": v["sesgo_c"], "sesgo_c_ic95": v["sesgo_c_ic95"]}, [v["fuente"]]))
    alt = doc.get("sensibilidad_precipitacion_alterna")
    if alt and e["id"] in alt["posiciones"]:
        c = alt["contraste_estacion"]
        pos = alt["posiciones"][e["id"]]
        out.append(_e("card.gap.rain_alt_source", {"central": pos["central"], "alterna": pos["alterna"],
                                                   "estacion": c["estacion"], "sesgo_imerg": c["sesgo_relativo_imerg"],
                                                   "sesgo_power": c["sesgo_relativo_power"]},
                      {"posiciones": pos, "modo": alt["modo"]}, [alt["fuente_contraste"]]))
    if e["indicadores"].get("costo_anio", {}).get("etiqueta") == "PENDIENTE":
        out.append(_e("card.gap.cost_pending"))
    return out


def _riesgos(e: dict, base: dict, objetivos: list[str], doc: dict, es_base: bool) -> list[dict]:
    out = []
    if not es_base:
        for o in objetivos:
            x, b = e["metricas"][o], base["metricas"][o]
            if _mejor(OBJETIVOS[o]["sentido"], x - b, b) < 0:
                out.append(_e("card.risk.gives_up", {"objetivo": {"clave": f"objective.{o}"}, "base": _redondeo(b),
                                                     "valor": _redondeo(x), "unidad": _unidad_objetivo(o, e)},
                              {"objetivo": o, "base": b, "valor": x}))
        for k in ("produccion_relativa_anio", "rendimiento_relativo"):
            v, b = e["indicadores"].get(k), base["indicadores"].get(k)
            if v and b and v["p10"] is not None and b["p10"] is not None and \
                    _mejor("max", v["p10"] - b["p10"], b["p10"]) < 0:
                out.append(_e("card.risk.worse_p10", {"indicador": {"clave": f"indicator.{k}.name"}, "valor": v["p10"],
                                                      "base": b["p10"], "unidad": clave_unidad(v["unidad"])},
                              {"indicador": k, "p10": v["p10"], "base_p10": b["p10"]}))
    for a in doc.get("avisos_claves", []):
        if a["clave"] in ("warning.saxton_rawls_domain", "warning.soilgrids_andisol_mo",
                          "warning.monthly_context_only", "warning.succession_none"):
            out.append(_e(a["clave"], a["parametros"]))
    out.append(_e("card.risk.not_modelled"))
    out.append(_e("card.risk.local_review"))
    return out


def construir(doc: dict, sensibilidad: dict | None = None) -> dict:
    """{estrategia_id: {por_que, evidencia, beneficios, vacios, riesgos}} para todas las estrategias del documento."""
    ests = _estrategias(doc)
    ref = id_referencia(doc)
    base = next(e for e in ests if e["id"] == ref)
    objetivos = objetivos_tarjeta(doc)
    out = {}
    for e in ests:
        es_base = e["id"] == ref
        out[e["id"]] = {"por_que": _por_que(e, base, objetivos, es_base), "evidencia": _evidencia(e, doc),
                        "beneficios": _beneficios(e, base, es_base), "vacios": _vacios(e, doc, sensibilidad),
                        "riesgos": _riesgos(e, base, objetivos, doc, es_base),
                        "referencia": ref, "secciones_claves": {s: f"card.section.{s}" for s in SECCIONES}}
    return out


def _valores_por_muestra(ens, ids: list[str]) -> list[dict[str, dict[str, float]]]:
    """[{estrategia: {objetivo: valor natural}} por muestra p de theta], con las K series climáticas de cada p."""
    h = ind.por_miembro(ens.reg, ens.prog, ens.H, ens.p_intensa, ens.umbral_cobertura)
    out = []
    for p in range(ens.P):
        vals = {}
        for s, i in enumerate(ids):
            sel = np.arange(s * ens.K * ens.P + p, (s + 1) * ens.K * ens.P, ens.P)
            vals[i] = a_natural(list(pr.METRICAS_TODAS), valores_objetivo(h, sel, list(pr.METRICAS_TODAS)))
        out.append(vals)
    return out


def _orden_y_mejores(vals: dict[str, dict[str, float]], objetivos: list[str]) -> tuple[list[str], dict[str, str]]:
    ids = list(vals)
    orden = pr.ordenar(pr.normalizar(vals), pr.PESOS_IGUALES)
    mejores = {o: (max if OBJETIVOS[o]["sentido"] == "max" else min)(ids, key=lambda i: vals[i][o])
               for o in objetivos}
    return orden, mejores


def sensibilidad_supuestos(entrada, estrategias: list, referencia: int = 0, miembros_clima: int = 4,
                           objetivos: list[str] | None = None) -> dict:
    """Barrido uno a uno de los parámetros SUPUESTO con rango, en un solo ensamble: la muestra 0 de theta es la
    central y cada par de muestras siguientes lleva un parámetro a su extremo bajo y alto (K climas submuestreados)."""
    objetivos = objetivos or list(OBJETIVOS_BASE)
    ids = [e.id for e in estrategias]
    esc = submuestrear(entrada.escenario, miembros_clima)
    cat = cargar_catalogo()
    cultivos = [cat[c] for c in sorted({t.cultivo for e in estrategias for t in e.temporadas})]
    planos, avisos, suelo = reunir_parametros(entrada.suelo, cultivos, entrada.calibracion)
    barridos = [(k, p) for k, p in sorted(planos.items()) if p.etiqueta == "SUPUESTO" and p.rango is not None
                and p.rango[1] > p.rango[0] and k not in entrada.calibracion]
    # Tandas de parámetros para no pasar de ~MAX_MIEMBROS miembros por ensamble (memoria)
    tanda = max(1, (MAX_MIEMBROS // (len(estrategias) * esc.n_miembros) - 1) // 2)
    orden_base, mejores_base, extremos = None, None, []
    for t0 in range(0, max(len(barridos), 1), tanda):
        parte = barridos[t0:t0 + tanda]
        n = 1 + 2 * len(parte)
        m = {k: np.full(n, p.exigir()) for k, p in planos.items()}
        for j, (k, p) in enumerate(parte):
            m[k][1 + 2 * j], m[k][2 + 2 * j] = p.rango
        theta = theta_desde_muestras(planos, m, suelo, cultivos, avisos)
        ens = ejecutar(entrada.clima, esc, entrada.suelo, estrategias, theta=theta, catalogo=cat,
                       referencia=referencia, equilibrio=entrada.simulacion["equilibrio"])
        por_muestra = [_orden_y_mejores(v, objetivos) for v in _valores_por_muestra(ens, ids)]
        del ens
        orden_base, mejores_base = por_muestra[0]
        extremos += [(por_muestra[1 + 2 * j], por_muestra[2 + 2 * j]) for j in range(len(parte))]
    filas = []
    for (k, p), (bajo, alto) in zip(barridos, extremos):
        res = {"bajo": bajo, "alto": alto}
        posiciones = {i: {"central": orden_base.index(i) + 1, **{x: r[0].index(i) + 1 for x, r in res.items()}}
                      for i in ids}
        cambia_mejor = sorted({o for r in res.values() for o in objetivos if r[1][o] != mejores_base[o]})
        filas.append({"clave": k, "valor": p.valor, "rango": list(p.rango), "unidad": p.unidad,
                      "referencia": p.referencia, "orden_bajo": res["bajo"][0], "orden_alto": res["alto"][0],
                      "cambia_orden": any(r[0] != orden_base for r in res.values()),
                      "cambia_mejor_por_objetivo": cambia_mejor, "posiciones": posiciones})
    return {"metodo": "uno a uno en los extremos del rango; resto de theta en su valor central; orden con pesos "
                      "iguales en los cuatro deslizadores",
            "escenario": entrada.escenario.tipo, "miembros_clima": esc.n_miembros, "estrategias": ids,
            "orden_central": orden_base, "mejor_por_objetivo_central": mejores_base, "objetivos": objetivos,
            "parametros": [f for f in filas if f["cambia_orden"] or f["cambia_mejor_por_objetivo"]],
            "sin_efecto": [f["clave"] for f in filas if not (f["cambia_orden"] or f["cambia_mejor_por_objetivo"])]}

