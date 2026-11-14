# asistido por SI: Cursor (agente), escritura y revisión de código; núcleo del gemelo digital en el hackatón
"""Línea de comandos: python -m gemelo {simular, optimizar, cultivos, definiciones} ..."""
import argparse
import json
import sys
import time
from pathlib import Path

from gemelo.api import definiciones, optimizar_rotacion, simular
from gemelo.parametros import cargar_catalogo
from gemelo.procedencia import ParametroPendiente
from gemelo.salida import guardar_json, guardar_sqlite

RESUMEN = ("produccion_relativa_anio", "rendimiento_relativo", "riego_mm_anio", "deficit_relativo",
           "lixiviacion_n_kg_ha_anio", "cambio_carbono_t_ha_anio", "exposicion_erosiva_mm_anio")


def _tabla(estrategias: list[dict]) -> str:
    filas = []
    for k in RESUMEN:
        filas.append(f"\n{k} ({estrategias[0]['indicadores'][k]['unidad']})")
        for e in estrategias:
            v = e["indicadores"][k]
            celda = "—" if v["p50"] is None else f"{v['p50']:.3g}  [{v['p10']:.3g}, {v['p90']:.3g}]"
            filas.append(f"  {(e['id'] + ' ' + e['nombre'])[:40]:<42}{celda}")
    return "\n".join(filas)


def _guardar(doc: dict, args) -> None:
    ruta = guardar_json(doc, args.salida)
    print(f"JSON: {ruta}")
    if args.sqlite:
        print(f"SQLite: {args.sqlite} (corrida {guardar_sqlite(doc, args.sqlite)})")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="python -m gemelo", description="Gemelo digital agrícola AGROVERSE (núcleo)")
    sub = ap.add_subparsers(dest="orden", required=True)
    for nombre, ayuda in (("simular", "simula las estrategias del escenario"),
                          ("optimizar", "busca rotaciones con NSGA-II y compara con la línea base")):
        p = sub.add_parser(nombre, help=ayuda)
        p.add_argument("escenario", type=Path, help="archivo YAML de escenario (contratos/gemelo_api.md)")
        p.add_argument("-o", "--salida", type=Path, required=True, help="archivo JSON de salida")
        p.add_argument("--sqlite", type=Path, help="además, añadir la corrida a esta base SQLite")
    p = sub.add_parser("cultivos", help="catálogo de cultivos y qué falta para simularlos")
    p.add_argument("--json", action="store_true")
    sub.add_parser("definiciones", help="indicadores, objetivos y cultivos en JSON")
    args = ap.parse_args(argv)

    try:
        if args.orden in ("simular", "optimizar"):
            t = time.time()
            doc = simular(args.escenario) if args.orden == "simular" else optimizar_rotacion(args.escenario)
            m = doc["metadatos"]["miembros"]
            print(f"{args.orden}: {m['total']} miembros ({m['estrategias']} estrategias x {m['clima']} climas x "
                  f"{m['parametros']} parámetros), {time.time() - t:.1f} s. p50 [p10, p90]:")
            print(_tabla(doc.get("estrategias") or [doc["linea_base"], *doc["frente"]]))
            if args.orden == "optimizar":
                print("\n".join(doc["compromisos"]["explicacion"]))
            _guardar(doc, args)
        elif args.orden == "cultivos":
            cat = cargar_catalogo()
            if args.json:
                print(json.dumps({k: c.a_dict() for k, c in cat.items()}, ensure_ascii=False, indent=2))
            else:
                for k, c in cat.items():
                    estado = ("simulable" if c.apto_rotacion and not c.pendientes()
                              else f"no apto: {c.motivo_no_apto}" if not c.apto_rotacion
                              else f"PENDIENTE: {', '.join(c.pendientes())}")
                    print(f"{k:<18} {c.nombre:<28} {estado}")
        else:
            print(json.dumps(definiciones(), ensure_ascii=False, indent=2, default=str))
    except (ParametroPendiente, ValueError, KeyError, FileNotFoundError, RuntimeError) as e:
        print(f"error: {e}", file=sys.stderr)
        return 2
    return 0
