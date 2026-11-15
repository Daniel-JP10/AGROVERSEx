# asistido por SI: Cursor (agente), escritura y revisión de código; núcleo del gemelo digital en el hackatón
# asistido por SI: Claude Code (Opus 5.5), v1.2: exposicion_erosiva de Datos como objetivo del deslizador suelo
"""Puntos de entrada de alto nivel: escenario (YAML o dict) -> documento JSON del contrato gemelo_api.md."""
from pathlib import Path

import numpy as np

from gemelo import indicadores as ind
from gemelo.enso import FASES, fases_por_anio
from gemelo.entrada import Entrada, leer_entrada
from gemelo.incertidumbre import resumir
from gemelo.optimizacion import OBJETIVOS, optimizar, problema_desde_dict
from gemelo.parametros import cargar_catalogo
from gemelo.salida import documento_optimizacion, documento_simulacion, limpiar
from gemelo.simulador import Ensamble, ejecutar, resumir_estrategias
from gemelo.tarjetas import SENTIDO_INDICADOR


def _indice(entrada: Entrada, id_: str | None) -> int:
    if id_ is None:
        return 0
    ids = [e.id for e in entrada.estrategias]
    if id_ not in ids:
        raise KeyError(f"estrategia de referencia {id_!r} no está entre {ids}")
    return ids.index(id_)


def _entrada(fuente) -> Entrada:
    return fuente if isinstance(fuente, Entrada) else leer_entrada(fuente)


def por_fase_enso(entrada: Entrada, ens: Ensamble, ids: list[str]) -> dict:
    """Indicadores del escenario histórico agrupados por la fase ENSO del primer año de cada ventana."""
    fases, meta = fases_por_anio(entrada.origen.get("enso_archivo"))
    anios = entrada.clima.anios
    fase_k = [fases.get(int(anios[m[0]])) for m in entrada.escenario.miembros]
    h = ind.por_miembro(ens.reg, ens.prog, ens.H, ens.p_intensa, ens.umbral_cobertura, erosion=ens.erosion)
    claves = ["produccion_relativa_anio", *SENTIDO_INDICADOR]
    estrategias = {}
    for s, id_ in enumerate(ids):
        b = ens.bloque(s)
        por_fase = {}
        for f in FASES:
            sel = np.array([fase_k[j // ens.P] == f for j in range(ens.K * ens.P)])
            if not sel.any():
                continue
            por_fase[f] = {"n_miembros": int(sel.sum()),
                           "indicadores": {k: resumir(h[k][b][sel]) for k in dict.fromkeys(claves)}}
        estrategias[id_] = por_fase
    return limpiar({"clasificacion": meta, "criterio": "fase del primer año de cada ventana histórica",
                    "ventanas_por_fase": {f: [int(anios[m[0]]) for m, fk in zip(entrada.escenario.miembros, fase_k)
                                              if fk == f] for f in FASES},
                    "estrategias": estrategias})


def simular_con_ensamble(fuente: str | Path | dict | Entrada) -> tuple[dict, Ensamble]:
    entrada = _entrada(fuente)
    if not entrada.estrategias:
        raise ValueError("el escenario no define estrategias")
    s = entrada.simulacion
    ens = ejecutar(entrada.clima, entrada.escenario, entrada.suelo, entrada.estrategias,
                   n_parametros=int(s["n_parametros"]), semilla=int(s["semilla"]), calibracion=entrada.calibracion,
                   n_sub=int(s["n_sub"]), referencia=_indice(entrada, s.get("referencia")),
                   equilibrio=s["equilibrio"])
    doc = documento_simulacion(entrada, ens, resumir_estrategias(ens, entrada.costos))
    if entrada.escenario.tipo == "historico":
        doc["indicadores_por_fase_enso"] = por_fase_enso(entrada, ens, [e.id for e in entrada.estrategias])
    return doc, ens


def simular(fuente: str | Path | dict | Entrada) -> dict:
    return simular_con_ensamble(fuente)[0]


def optimizar_con_ensamble(fuente: str | Path | dict | Entrada) -> tuple[dict, Ensamble]:
    entrada = _entrada(fuente)
    opt = entrada.optimizacion
    if not opt:
        raise ValueError("el escenario no tiene sección 'optimizacion'")
    problema, avisos = problema_desde_dict(opt, entrada.escenario.anios_horizonte, entrada.clima_lote)
    base = entrada.estrategias[_indice(entrada, opt.get("linea_base"))]
    b = opt.get("busqueda", {})
    res = optimizar(entrada.clima, entrada.escenario, entrada.suelo, problema, base,
                    poblacion=int(b.get("poblacion", 24)), generaciones=int(b.get("generaciones", 15)),
                    miembros_clima=b.get("miembros_clima", 4), muestras_parametros=int(b.get("muestras_parametros", 3)),
                    miembros_final=b.get("miembros_final", 8), muestras_final=int(b.get("muestras_final", 8)),
                    semilla=int(entrada.simulacion["semilla"]), calibracion=entrada.calibracion,
                    costos=entrada.costos, max_soluciones=int(b.get("max_soluciones", 10)))
    res["avisos"] = list(res["avisos"]) + avisos
    if not res["frente"]:
        raise RuntimeError("; ".join(res["avisos"]))
    return documento_optimizacion(entrada, res), res["ensamble_final"]


def optimizar_rotacion(fuente: str | Path | dict | Entrada) -> dict:
    return optimizar_con_ensamble(fuente)[0]


def definiciones() -> dict:
    """Catálogo de indicadores, objetivos y cultivos con su estado, para que web e integración no lo dupliquen."""
    return {
        "indicadores": {k: {"unidad": u, "definicion": f, "explicacion": t,
                            **({"obsoleto": True, "reemplazado_por": ind.OBSOLETOS[k]} if k in ind.OBSOLETOS else {})}
                        for k, (u, f, t) in ind.DEFINICIONES.items()},
        "indicadores_temporada": {k: {"unidad": u, "definicion": f} for k, (u, f) in ind.DEFINICIONES_TEMPORADA.items()},
        "objetivos": OBJETIVOS,
        "cultivos": {k: c.a_dict() for k, c in cargar_catalogo().items()},
    }
