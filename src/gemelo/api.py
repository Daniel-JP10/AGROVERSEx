# asistido por SI: Cursor (agente), escritura y revisión de código; núcleo del gemelo digital en el hackatón
"""Puntos de entrada de alto nivel: escenario (YAML o dict) -> documento JSON del contrato gemelo_api.md."""
from pathlib import Path

from gemelo import indicadores as ind
from gemelo.entrada import Entrada, leer_entrada
from gemelo.optimizacion import OBJETIVOS, optimizar, problema_desde_dict
from gemelo.parametros import cargar_catalogo
from gemelo.salida import documento_optimizacion, documento_simulacion
from gemelo.simulador import ejecutar, resumir_estrategias


def _indice(entrada: Entrada, id_: str | None) -> int:
    if id_ is None:
        return 0
    ids = [e.id for e in entrada.estrategias]
    if id_ not in ids:
        raise KeyError(f"estrategia de referencia {id_!r} no está entre {ids}")
    return ids.index(id_)


def simular(fuente: str | Path | dict | Entrada) -> dict:
    entrada = fuente if isinstance(fuente, Entrada) else leer_entrada(fuente)
    if not entrada.estrategias:
        raise ValueError("el escenario no define estrategias")
    s = entrada.simulacion
    ens = ejecutar(entrada.clima, entrada.escenario, entrada.suelo, entrada.estrategias,
                   n_parametros=int(s["n_parametros"]), semilla=int(s["semilla"]), calibracion=entrada.calibracion,
                   n_sub=int(s["n_sub"]), referencia=_indice(entrada, s.get("referencia")),
                   equilibrio=s["equilibrio"])
    return documento_simulacion(entrada, ens, resumir_estrategias(ens, entrada.costos))


def optimizar_rotacion(fuente: str | Path | dict | Entrada) -> dict:
    entrada = fuente if isinstance(fuente, Entrada) else leer_entrada(fuente)
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
    return documento_optimizacion(entrada, res)


def definiciones() -> dict:
    """Catálogo de indicadores, objetivos y cultivos con su estado, para que web e integración no lo dupliquen."""
    return {
        "indicadores": {k: {"unidad": u, "definicion": f, "explicacion": t} for k, (u, f, t) in ind.DEFINICIONES.items()},
        "indicadores_temporada": {k: {"unidad": u, "definicion": f} for k, (u, f) in ind.DEFINICIONES_TEMPORADA.items()},
        "objetivos": OBJETIVOS,
        "cultivos": {k: c.a_dict() for k, c in cargar_catalogo().items()},
    }
