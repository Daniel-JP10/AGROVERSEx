# asistido por SI: Cursor (agente), escritura y revisión de código; núcleo del gemelo digital en el hackatón
"""Orquestador: lote + suelo + clima + estrategias -> ensamble simulado -> indicadores con p10/p50/p90.

Miembros del ensamble: M = S estrategias x K miembros climáticos x P muestras de parámetros. Las S estrategias
comparten exactamente los mismos K climas y P vectores de parámetros (números aleatorios comunes), así las
diferencias entre estrategias no se confunden con diferencias de muestreo.
"""
from dataclasses import dataclass, field

import numpy as np

from gemelo import indicadores as ind
from gemelo.clima import ClimaDiario
from gemelo.dinamica import Estado0, THETA_CULTIVO, equilibrio_carbono, simular
from gemelo.escenarios import EscenarioClimatico, series, umbral_lluvia_intensa
from gemelo.incertidumbre import muestrear, resumir
from gemelo.manejo import Programa, apilar, compilar
from gemelo.modelos import EstadoGemelo, Estrategia, Lote
from gemelo.parametros import Cultivo, cargar_catalogo
from gemelo.procedencia import Parametro, TablaParametros, cargar_tabla
from gemelo.suelo import PerfilSuelo, coef_drenaje, grupo_hidrologico, numeros_curva

VERSION_MODELO = "0.1.0"


@dataclass
class Theta:
    """theta muestreado: ts (P,) por clave de suelo/proceso, tc (P, C) por clave de cultivo."""
    ts: dict[str, np.ndarray]
    tc: dict[str, np.ndarray]
    x0: dict[str, np.ndarray]
    parametros: dict[str, Parametro]
    cultivos: list[str]
    avisos: list[str] = field(default_factory=list)


def _calibrar_tabla(tabla: TablaParametros, prefijo: str, calibracion: dict) -> TablaParametros:
    vals = {k.split(".", 1)[1]: v for k, v in calibracion.items() if k.startswith(prefijo + ".") and v is not None}
    for k in vals:
        if k not in tabla:
            raise KeyError(f"calibración {prefijo}.{k}: parámetro desconocido")
    return tabla.con(**vals) if vals else tabla


def construir_theta(suelo: PerfilSuelo, cultivos: list[Cultivo], n: int, semilla: int,
                    calibracion: dict | None = None) -> Theta:
    """Reúne los parámetros con procedencia, aplica la calibración local y muestrea n vectores theta."""
    planos, avisos, suelo = reunir_parametros(suelo, cultivos, calibracion)
    return theta_desde_muestras(planos, muestrear(planos, n, semilla), suelo, cultivos, avisos)


def reunir_parametros(suelo: PerfilSuelo, cultivos: list[Cultivo],
                      calibracion: dict | None = None) -> tuple[dict[str, Parametro], list[str], PerfilSuelo]:
    """Parámetros planos con procedencia (calibración aplicada), avisos y suelo calibrado."""
    calibracion = calibracion or {}
    avisos = list(suelo.avisos)
    sv = {k.split(".", 1)[1]: v for k, v in calibracion.items() if k.startswith("suelo.") and v is not None}
    if sv:
        suelo = suelo.calibrar(**sv)
    t_agua = _calibrar_tabla(cargar_tabla("agua_suelo.yaml"), "agua", calibracion)
    t_cn = _calibrar_tabla(cargar_tabla("carbono_nitrogeno.yaml"), "cn", calibracion)
    planos: dict[str, Parametro] = {}
    for k in ("profundidad_perfil_m", "theta_cc", "theta_pmp", "theta_sat", "ksat_mm_h", "cos_t_ha"):
        planos[f"suelo.{k}"] = suelo[k]
    if "cn_suelo" in suelo.parametros:
        planos["suelo.cn_suelo"] = suelo["cn_suelo"]
    else:
        planos["suelo.cn_suelo"] = t_cn["cn_reservorio_viejo_respaldo"]
        avisos.append("C:N del suelo sin dato de SoilGrids: se usa el respaldo SUPUESTO")
    for k, p in t_agua.items():
        planos[f"agua.{k}"] = p
    for k, p in t_cn.items():
        planos[f"cn.{k}"] = p
    for c in cultivos:
        for k in THETA_CULTIVO:
            clave = f"cultivo.{c.id}.{k}"
            p = c.p(k)
            if clave in calibracion and calibracion[clave] is not None:
                p = p.calibrar(calibracion[clave])
            planos[clave] = p
    for k in calibracion:
        if k.startswith("cultivo.") and k not in planos:
            raise KeyError(f"calibración {k}: cultivo o parámetro fuera de esta simulación")
    if "cn.n_mineral_inicial_kg_ha" not in calibracion:
        avisos.append("N mineral inicial sin análisis de suelo (SUPUESTO 10-60 kg N/ha): el balance de N es "
                      "orientativo")
    if "agua.fraccion_humedad_inicial" not in calibracion:
        avisos.append("Humedad inicial del suelo SUPUESTO (20-80 % del agua disponible); con SMAP L4 o medición "
                      "local se reduce la incertidumbre del primer ciclo")
    return planos, avisos, suelo


def theta_desde_muestras(planos: dict[str, Parametro], m: dict[str, np.ndarray], suelo: PerfilSuelo,
                         cultivos: list[Cultivo], avisos: list[str]) -> Theta:
    """theta a partir de muestras {clave: valores (n,)} ya hechas (LHS o barridos a mano)."""
    n = len(next(iter(m.values())))
    ts = {"zp": m["suelo.profundidad_perfil_m"]}
    ts["th_pmp"] = m["suelo.theta_pmp"]
    ts["th_cc"] = np.maximum(m["suelo.theta_cc"], ts["th_pmp"] + 0.03)
    ts["th_sat"] = np.maximum(m["suelo.theta_sat"], ts["th_cc"] + 0.03)
    ts["tau"] = coef_drenaje(m["suelo.ksat_mm_h"], m["agua.drenaje_a"], m["agua.drenaje_b"])
    cn = numeros_curva(grupo_hidrologico(suelo.valor("ksat_mm_h")))
    ts["cn_cultivo"] = np.full(n, cn["cultivo"])
    ts["cn_desnudo"] = np.full(n, cn["desnudo"])
    ts["cn_residuo_cubierta"] = np.full(n, cn["residuo"])
    for clave, origen in (("rew", "agua.rew_mm"), ("ze", "agua.ze_m"), ("kc_min", "agua.kc_min"),
                          ("kc_max_suelo", "agua.kc_max_suelo"), ("red_mulch", "agua.reduccion_evap_mulch"),
                          ("am", "agua.am_residuo"), ("ajuste_p", "agua.ajuste_p_por_etc"),
                          ("zr_ini", "agua.zr_inicial_m"), ("efic_riego", "agua.eficiencia_riego"),
                          ("k1", "cn.k1_anual"), ("k2", "cn.k2_anual"), ("h", "cn.h_residuo"),
                          ("t_min_dec", "cn.t_min_descomposicion"), ("t_ref_dec", "cn.t_ref_descomposicion"),
                          ("t_norm_dec", "cn.t_normalizacion"), ("cn_suelo", "suelo.cn_suelo"),
                          ("fc_residuo", "cn.fraccion_carbono_residuo"),
                          ("frac_vol", "cn.fraccion_volatilizacion_fertilizante"),
                          ("ndfa_max", "cn.ndfa_max_compensacion")):
        ts[clave] = m[origen]
    tc = {k: np.stack([m[f"cultivo.{c.id}.{k}"] for c in cultivos], axis=1) for k in THETA_CULTIVO}
    x0 = {"frac_agua": m["agua.fraccion_humedad_inicial"], "n_mineral": m["cn.n_mineral_inicial_kg_ha"],
          "cos": m["suelo.cos_t_ha"], "frac_joven": m["cn.fraccion_joven_inicial"]}
    return Theta(ts, tc, x0, planos, [c.id for c in cultivos], avisos)


def _repetir(d: dict, veces_bloque: int, veces_total: int) -> dict:
    """(P, ...) -> (M, ...) con el índice de parámetro m % P (np.tile sobre el primer eje)."""
    return {k: np.tile(v, (veces_total // len(v),) + (1,) * (v.ndim - 1)) for k, v in d.items()}


@dataclass
class Ensamble:
    """Resultado bruto: registros (M, T) y la disposición de miembros (S, K, P)."""
    reg: dict
    prog: dict
    programas: list[Programa]
    S: int
    K: int
    P: int
    H: int
    theta: Theta
    metodo_eto: str
    p_intensa: float
    umbral_cobertura: float
    carbono_inicial: dict | None = None   # y0, yn0, res0, k2 por miembro K x P (equilibrio de la referencia)
    referencia: str | None = None
    equilibrio: str = "completo"

    def bloque(self, s: int) -> slice:
        n = self.K * self.P
        return slice(s * n, (s + 1) * n)


def ejecutar(clima: ClimaDiario, escenario: EscenarioClimatico, suelo: PerfilSuelo, estrategias: list[Estrategia],
             n_parametros: int = 8, semilla: int = 42, calibracion: dict | None = None, n_sub: int = 1,
             catalogo: dict[str, Cultivo] | None = None, theta: Theta | None = None,
             referencia: int | None = 0, carbono_inicial: dict | None = None,
             equilibrio: str = "completo") -> Ensamble:
    """Simula todas las estrategias sobre el mismo ensamble de clima y parámetros.

    referencia: índice de la estrategia (manejo actual) con la que se equilibra el carbono antes de comparar.
    equilibrio: "completo" (joven en equilibrio y k2 efectivo que deja el COS medido estable bajo la referencia),
    "joven" (solo el reservorio joven; k2 de ICBM) o "ninguno" (reparto SUPUESTO fraccion_joven_inicial).
    carbono_inicial reutiliza un equilibrio ya calculado (K x P miembros).
    """
    if equilibrio not in ("completo", "joven", "ninguno"):
        raise ValueError(f"equilibrio {equilibrio!r}")
    if equilibrio == "ninguno":
        referencia, carbono_inicial = None, None
    catalogo = catalogo or cargar_catalogo()
    usados = sorted({t.cultivo for e in estrategias for t in e.temporadas})
    faltan = [c for c in usados if c not in catalogo]
    if faltan:
        raise KeyError(f"cultivos fuera del catálogo: {faltan}")
    if theta is not None:
        fuera = sorted(set(usados) - set(theta.cultivos))
        if fuera:
            raise ValueError(f"theta no incluye los cultivos {fuera}")
        usados = list(theta.cultivos)
    cultivos = [catalogo[c] for c in usados]
    indice = {c: i for i, c in enumerate(usados)}
    H = escenario.anios_horizonte
    T = 365 * H
    programas = [compilar(e, catalogo, indice, T) for e in estrategias]
    if theta is None:
        theta = construir_theta(suelo, cultivos, n_parametros, semilla, calibracion)
    P = len(next(iter(theta.ts.values())))
    clim, metodo = series(clima, escenario, float(theta.parametros["agua.viento_respaldo_ms"].exigir()))
    S, K = len(estrategias), escenario.n_miembros
    M = S * K * P
    # Orden de miembros: m = (s * K + k) * P + p
    clim_kp = {k: np.repeat(v, P, axis=0) for k, v in clim.items()}          # (K P, T)
    ts_kp, tc_kp, x0_kp = (_repetir(d, P, K * P) for d in (theta.ts, theta.tc, theta.x0))
    nombre_ref = None
    if referencia is not None:
        nombre_ref = estrategias[referencia].id
    if carbono_inicial is None and referencia is not None:
        prog_ref = apilar([programas[referencia]], K * P)
        # Dos pasadas: el k2 efectivo cambia la mineralización, el N disponible y con ello la entrada de residuo
        for _ in range(2 if equilibrio == "completo" else 1):
            x0_it = dict(x0_kp, **({k: carbono_inicial[k] for k in ("y0", "yn0", "res0")}
                                   if carbono_inicial else {}))
            ts_it = dict(ts_kp, **({"k2": carbono_inicial["k2"]} if carbono_inicial and equilibrio == "completo"
                                   else {}))
            piloto = simular(clim_kp, prog_ref, ts_it, tc_kp, Estado0(**x0_it), n_sub=n_sub)
            carbono_inicial = equilibrio_carbono(piloto, ts_kp["k1"], ts_kp["h"], x0_kp["cos"])
    clim_m = {k: np.tile(v, (S, 1)) for k, v in clim_kp.items()}
    prog = apilar(programas, K * P)
    ts = _repetir(theta.ts, P, M)
    tc = _repetir(theta.tc, P, M)
    x0 = _repetir(theta.x0, P, M)
    if carbono_inicial is not None:
        for k in ("y0", "yn0", "res0"):
            x0[k] = np.tile(carbono_inicial[k], S)
        if equilibrio == "completo":
            ts["k2"] = np.tile(carbono_inicial["k2"], S)
    reg = simular(clim_m, prog, ts, tc, Estado0(**x0), n_sub=n_sub)
    p_int = umbral_lluvia_intensa(clima, float(theta.parametros["agua.percentil_lluvia_intensa"].exigir()))
    umbral = float(theta.parametros["agua.umbral_cobertura_protectora"].exigir())
    return Ensamble(reg, prog, programas, S, K, P, H, theta, metodo, p_int, umbral, carbono_inicial, nombre_ref,
                    equilibrio)


def resumir_estrategias(ens: Ensamble, costos: dict | None = None) -> list[dict]:
    """Indicadores por estrategia con p10/p50/p90 sobre clima y parámetros, más trayectoria mensual."""
    fijos = None
    avisos_costo = []
    if costos is not None:
        try:
            fijos = np.repeat([ind.costos_fijos_estrategia(p.estrategia, costos) for p in ens.programas],
                              ens.K * ens.P)
        except KeyError as e:
            avisos_costo.append(str(e))
            costos = None
    h = ind.por_miembro(ens.reg, ens.prog, ens.H, ens.p_intensa, ens.umbral_cobertura, fijos, costos)
    men = ind.mensual(ens.reg, ens.H)
    salida = []
    for s, prog in enumerate(ens.programas):
        b = ens.bloque(s)
        e = prog.estrategia
        sub_reg = {k: v[b] for k, v in ens.reg.items() if k != "inicial"}
        sub_prog = {k: v[b] for k, v in ens.prog.items()}
        temp = ind.por_temporada(sub_reg, sub_prog, len(e.temporadas))
        indicadores = {}
        for k, v in h.items():
            unidad, formula, texto = ind.DEFINICIONES[k]
            indicadores[k] = {**resumir(v[b]), "unidad": unidad, "definicion": formula, "explicacion": texto}
            if k in ind.OBSOLETOS:
                indicadores[k].update(obsoleto=True, reemplazado_por=ind.OBSOLETOS[k])
        if "costo_anio" not in h:
            u, f, t = ind.DEFINICIONES["costo_anio"]
            indicadores["costo_anio"] = {"p10": None, "p50": None, "p90": None, "unidad": u, "definicion": f,
                                         "explicacion": t, "etiqueta": "PENDIENTE",
                                         "motivo": avisos_costo[0] if avisos_costo else "sin precios del usuario"}
        temporadas = []
        for k, t in enumerate(e.temporadas):
            dur = sum(prog.duraciones[k])
            fila = t.a_dict(dur)
            fila["etapas_dias"] = list(prog.duraciones[k])
            fila["indicadores"] = {n: {**resumir(arr[:, k]), "unidad": ind.DEFINICIONES_TEMPORADA[n][0],
                                       "definicion": ind.DEFINICIONES_TEMPORADA[n][1]} for n, arr in temp.items()}
            temporadas.append(fila)
        tray = {k: {q: (np.round(val, 4).tolist() if val is not None else None)
                    for q, val in resumir(v[b], eje=0).items()} for k, v in men.items()}
        final = {k: float(np.median(ens.reg[k][b, -1])) for k in ("W", "N", "C", "B", "V")}
        estado_final = EstadoGemelo(365 * ens.H - 1, final["W"], final["N"], final["C"], final["B"], final["V"])
        salida.append({"id": e.id, "nombre": e.nombre, "descripcion": e.descripcion, "etiqueta": e.etiqueta,
                       "secuencia": e.secuencia(), "temporadas": temporadas, "indicadores": indicadores,
                       "trayectoria_mensual": tray, "estado_final_p50": estado_final.vector(),
                       "n_miembros": ens.K * ens.P})
    return salida
