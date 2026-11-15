# asistido por SI: Cursor (agente), escritura y revisión de código; núcleo del gemelo digital en el hackatón
# asistido por SI: Claude Code (Opus 5.5), v1.2: exposicion_erosiva de Datos como objetivo del deslizador suelo
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
           "lixiviacion_n_kg_ha_anio", "cambio_carbono_t_ha_anio", "indice_exposicion_erosiva")


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
    p = sub.add_parser("paquete", help="paquete estático por lote para la app pública (contrato v1.1)")
    p.add_argument("escenario", type=Path, nargs="?", help="archivo YAML de escenario del lote")
    p.add_argument("--lote-id", help="id DEMO-{iso3}-{nn} del lote")
    p.add_argument("--salida", type=Path, default=Path("datos/publicos/gemelo"), help="carpeta del paquete")
    p.add_argument("--definitivo", action="store_true", help="el id ya es el del lote DEMO elegido (no provisional)")
    p.add_argument("--solo-indice", action="store_true", help="solo regenerar indice.json y textos")
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
        elif args.orden == "paquete":
            from gemelo import paquete
            if not args.solo_indice:
                if not args.escenario or not args.lote_id:
                    raise ValueError("paquete: se necesitan el escenario y --lote-id (o --solo-indice)")
                t = time.time()
                paquete.construir_lote(args.escenario, args.lote_id, args.salida, not args.definitivo)
                print(f"lote {args.lote_id}: {time.time() - t:.0f} s")
            print(f"índice: {paquete.actualizar_indice(args.salida)}")
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
