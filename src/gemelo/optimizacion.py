# asistido por SI: Cursor (agente), escritura y revisión de código; núcleo del gemelo digital en el hackatón
"""Búsqueda multiobjetivo de rotaciones con NSGA-II (Deb et al., 2002) sobre el gemelo (pymoo; Blank y Deb, 2020).

Codificación: el horizonte se divide en campañas (p. ej. "principal" el 1 de mayo e "invierno" el 20 de octubre
de cada año). Cada campaña es una ranura con tres genes enteros:
    cultivo   0 = barbecho, 1..n = opción permitida en esa campaña
    desfase   índice en `desfases_dias` (corre la siembra unos días dentro de la ventana)
    riego     0 = secano, 1 = riego automático (solo si el usuario lo permite)
Objetivos (todos se minimizan internamente; los de "max" se cambian de signo) sobre el ensamble clima x theta.
Restricciones g <= 0: solapes y salida del horizonte (días), sucesión entre cultivos susceptibles (días que faltan
al intervalo mínimo), cultivos exigidos ausentes, cosechas mínimas por año y tope anual de riego (mm).

El resultado es un frente de compromisos, no un óptimo: cada solución se explica frente a la línea base.
"""
from dataclasses import dataclass, field, replace
from pathlib import Path

import numpy as np
import yaml
from pymoo.algorithms.moo.nsga2 import NSGA2
from pymoo.core.callback import Callback
from pymoo.core.problem import Problem
from pymoo.core.sampling import Sampling
from pymoo.operators.crossover.sbx import SBX
from pymoo.operators.mutation.pm import PM
from pymoo.operators.repair.rounding import RoundingRepair
from pymoo.optimize import minimize
from pymoo.util.nds.non_dominated_sorting import NonDominatedSorting

from gemelo import indicadores as ind
from gemelo.clima import ClimaDiario
from gemelo.escenarios import EscenarioClimatico
from gemelo.fenologia import duraciones
from gemelo.incertidumbre import cvar
from gemelo.modelos import Estrategia, Fertilizacion, Riego, Temporada, dia_nominal, fecha_legible
from gemelo.parametros import Cultivo, cargar_catalogo
from gemelo.procedencia import REFERENCIAS
from gemelo.simulador import construir_theta, ejecutar, resumir_estrategias
from gemelo.suelo import PerfilSuelo

OBJETIVOS = {
    "produccion": {"indicador": "produccion_relativa_anio", "sentido": "max",
                   "texto": "Producción cosechada (media del ensamble)"},
    "riesgo_produccion": {"indicador": "produccion_relativa_anio", "sentido": "max",
                          "texto": "Producción en el peor 10 % de los casos (CVaR 90 %): robustez ante años malos"},
    "carbono": {"indicador": "cambio_carbono_t_ha_anio", "sentido": "max",
                "texto": "Cambio del carbono del suelo (media del ensamble)"},
    "lluvia_intensa_suelo_desnudo": {"indicador": "lluvia_intensa_sobre_suelo_desnudo_mm_anio", "sentido": "min",
                                     "texto": "Lluvia intensa sobre suelo desprotegido (media del ensamble)"},
    "lixiviacion": {"indicador": "lixiviacion_n_kg_ha_anio", "sentido": "min",
                    "texto": "Nitrógeno lavado (media del ensamble)"},
    "riego": {"indicador": "riego_mm_anio", "sentido": "min", "texto": "Agua de riego (media del ensamble)"},
    "costo": {"indicador": "costo_anio", "sentido": "min", "texto": "Costo directo (media del ensamble)"},
    "deficit": {"indicador": "deficit_relativo", "sentido": "min",
                "texto": "Déficit hídrico relativo (media del ensamble)"},
    "fertilizante": {"indicador": "fertilizante_n_kg_ha_anio", "sentido": "min",
                     "texto": "Nitrógeno de fertilizante aplicado (media del ensamble)"},
}
OBJETIVOS_BASE = ("produccion", "riesgo_produccion", "carbono", "lluvia_intensa_suelo_desnudo", "lixiviacion")
# Ids de objetivo de la v1 que se aceptan en la entrada y se traducen al id vigente
ALIAS_OBJETIVOS = {"exposicion_erosiva": "lluvia_intensa_suelo_desnudo"}
RESTRICCIONES = ("solape_dias", "sucesion_dias", "cultivos_exigidos_faltantes", "cosechas_faltantes",
                 "riego_exceso_mm_anio")
PENALIDAD = 1e6

# Correspondencia familia (tabla regla_sucesion) -> cultivos del catálogo. Las familias sin cultivo simulable
# (guisante, brásicas, colza, remolacha) no afectan a las rotaciones que el gemelo puede construir.
FAMILIAS = {"Papa": ("papa",), "Frijol": ("frijol",), "Trigo y centeno": ("trigo_invierno", "trigo_primavera"),
            "Avena y cebada": ("avena",), "Trébol": ("trebol_berseem",), "Guisante": (), "Brásicas": (),
            "Colza": (), "Remolacha": ()}


@dataclass
class OpcionCultivo:
    """Una forma concreta de sembrar un cultivo que el optimizador puede elegir."""
    id: str
    cultivo: str
    cosechar: bool = True
    residuos: str = "superficie"
    labranza_siembra: bool = False
    fertilizacion: list[Fertilizacion] = field(default_factory=list)
    etapas: tuple[int, int, int, int] | None = None
    etapas_variante: str | None = None


@dataclass
class Campania:
    nombre: str
    fecha: str                    # "MM-DD"
    opciones: list[str]

    @property
    def dia_del_anio(self) -> int:
        return dia_nominal(f"A1-{self.fecha}")


@dataclass
class ReglaSucesion:
    """Intervalo mínimo entre ciclos de una familia susceptible.

    SUPUESTO de interpretación: `intervalo_anios` son años libres entre la cosecha de un ciclo y la siembra del
    siguiente de la misma familia (lectura conservadora de "rotación de n años" en las fuentes).
    """
    familia: str
    cultivos: tuple[str, ...]
    intervalo_anios: float
    referencia: str
    detalle: str = ""


def cargar_reglas(ruta: str | Path | None = None, clima: str = "templado",
                  reglas: list[dict] | None = None) -> tuple[list[ReglaSucesion], list[str]]:
    """Reglas con intervalo numérico y etiqueta FUENTE para el clima del lote, una por familia (la más estricta)."""
    if reglas is None:
        ruta = Path(ruta) if ruta else REFERENCIAS / "sucesion.yaml"
        with open(ruta, encoding="utf-8") as f:
            reglas = yaml.safe_load(f)["reglas"]
    avisos, por_familia = [], {}
    for r in reglas:
        if r.get("clima") != clima:
            continue
        fam = r["cultivo_o_familia"]
        if r.get("etiqueta") != "FUENTE" or r.get("intervalo_min") is None:
            avisos.append(f"Regla de sucesión {fam} / {r.get('enfermedad')} PENDIENTE: no se aplica")
            continue
        if fam not in FAMILIAS:
            avisos.append(f"Familia {fam!r} sin correspondencia en el catálogo: regla no aplicada")
            continue
        if not FAMILIAS[fam]:
            continue
        previo = por_familia.get(fam)
        if previo is None or float(r["intervalo_min"]) > previo.intervalo_anios:
            por_familia[fam] = ReglaSucesion(fam, FAMILIAS[fam], float(r["intervalo_min"]),
                                             r.get("fuente_id") or "", f"{r.get('enfermedad')} ({r.get('fuente_informe')})")
    if clima != "templado" and not por_familia:
        avisos.append("Clima del lote sin reglas de sucesión con intervalo numérico (INV-ROT §5.2): la sucesión "
                      "no restringe la búsqueda; revisar con el agrónomo local")
    return list(por_familia.values()), avisos


@dataclass
class ProblemaRotacion:
    horizonte_anios: int
    campanias: list[Campania]
    opciones: dict[str, OpcionCultivo]
    desfases_dias: tuple[int, ...] = (0,)
    riego_permitido: bool = False
    riego_tope_temporada_mm: float | None = None
    riego_tope_anio_mm: float | None = None
    reglas: list[ReglaSucesion] = field(default_factory=list)
    exigidos: list[str] = field(default_factory=list)
    min_cosechas_por_anio: float = 1.0
    objetivos: list[str] | None = None

    def __post_init__(self):
        if self.objetivos is None:
            self.objetivos = list(OBJETIVOS_BASE) + (["riego"] if self.riego_permitido else [])
        self.objetivos = list(dict.fromkeys(ALIAS_OBJETIVOS.get(o, o) for o in self.objetivos))
        desconocidos = [o for o in self.objetivos if o not in OBJETIVOS]
        if desconocidos:
            raise ValueError(f"objetivos desconocidos {desconocidos}; válidos: {list(OBJETIVOS)}")
        if len(self.objetivos) < 2:
            raise ValueError("se necesitan al menos dos objetivos para un frente de compromisos")
        for c in self.campanias:
            for o in c.opciones:
                if o not in self.opciones:
                    raise KeyError(f"campaña {c.nombre}: opción {o!r} no definida")
        self.campanias = sorted(self.campanias, key=lambda c: c.dia_del_anio)

    @property
    def genes_por_ranura(self) -> int:
        return 3 if self.riego_permitido else 2

    @property
    def ranuras(self) -> list[tuple[int, Campania]]:
        return [(a, c) for a in range(self.horizonte_anios) for c in self.campanias]

    def limites(self) -> tuple[np.ndarray, np.ndarray]:
        xu = []
        for _, c in self.ranuras:
            xu += [len(c.opciones), len(self.desfases_dias) - 1] + ([1] if self.riego_permitido else [])
        xu = np.array(xu, int)
        return np.zeros_like(xu), xu

    def canonico(self, x) -> tuple:
        """Genoma sin genes irrelevantes (desfase y riego de un barbecho): clave de la memoria de evaluaciones."""
        g, x = self.genes_por_ranura, [int(v) for v in x]
        out = []
        for i in range(len(self.ranuras)):
            r = x[i * g:(i + 1) * g]
            out += [0] * g if r[0] == 0 else r
        return tuple(out)

    def decodificar(self, x, catalogo: dict[str, Cultivo], id_: str = "candidata") -> tuple[Estrategia, dict]:
        g, x = self.genes_por_ranura, [int(v) for v in x]
        T = 365 * self.horizonte_anios
        temporadas, nombres, ciclos = [], [], []
        for i, (a, c) in enumerate(self.ranuras):
            gen = x[i * g:(i + 1) * g]
            if gen[0] == 0:
                continue
            op = self.opciones[c.opciones[gen[0] - 1]]
            riego = (Riego("automatico", tope_mm=self.riego_tope_temporada_mm)
                     if self.riego_permitido and gen[2] == 1 else Riego())
            siembra = 365 * a + c.dia_del_anio + self.desfases_dias[gen[1]]
            dur = sum(duraciones(catalogo[op.cultivo], op.etapas, op.etapas_variante))
            temporadas.append(Temporada(op.cultivo, siembra, op.etapas, op.etapas_variante, riego,
                                        list(op.fertilizacion), op.cosechar, op.residuos, op.labranza_siembra))
            nombres.append(f"{op.id}{' (riego)' if riego.modo == 'automatico' else ''} {c.nombre} año {a + 1}")
            ciclos.append((op.cultivo, siembra, siembra + dur - 1, op.cosechar))
        solape = sum(max(0, f0 - s1 + 1) for (_, _, f0, _), (_, s1, _, _) in zip(ciclos, ciclos[1:]))
        solape += sum(max(0, f - (T - 1)) for _, _, f, _ in ciclos)
        sucesion = 0.0
        for r in self.reglas:
            sel = [(s, f) for cu, s, f, _ in ciclos if cu in r.cultivos]
            for (s0, f0), (s1, _) in zip(sel, sel[1:]):
                sucesion += max(0.0, 365.0 * r.intervalo_anios - (s1 - f0))
        presentes = {cu for cu, *_ in ciclos}
        faltan = sum(1 for e in self.exigidos if e not in presentes)
        cosechas = sum(1 for *_, co in ciclos if co)
        viol = {"solape_dias": float(solape), "sucesion_dias": sucesion, "cultivos_exigidos_faltantes": float(faltan),
                "cosechas_faltantes": max(0.0, self.min_cosechas_por_anio * self.horizonte_anios - cosechas)}
        est = Estrategia(id_, " -> ".join(nombres) if nombres else "barbecho", temporadas,
                         descripcion="; ".join(f"{t.cultivo} desde {fecha_legible(t.siembra)}" for t in temporadas),
                         etiqueta="candidata NSGA-II (compromiso, no recomendación única)")
        return est, viol


def valores_objetivo(h: dict, bloque: slice, objetivos: list[str]) -> np.ndarray:
    """Vector a minimizar para el bloque de miembros de una estrategia."""
    out = []
    for o in objetivos:
        meta = OBJETIVOS[o]
        if meta["indicador"] not in h:
            raise ValueError(f"objetivo {o}: indicador {meta['indicador']} no disponible (¿faltan precios?)")
        v = np.nan_to_num(h[meta["indicador"]][bloque], nan=0.0)
        if o == "riesgo_produccion":
            out.append(cvar(-v, 0.9))
        else:
            out.append(-v.mean() if meta["sentido"] == "max" else v.mean())
    return np.array(out)


def a_natural(objetivos: list[str], f: np.ndarray) -> dict[str, float]:
    return {o: float(-v if OBJETIVOS[o]["sentido"] == "max" else v) for o, v in zip(objetivos, f)}


def submuestrear(esc: EscenarioClimatico, k: int | None) -> EscenarioClimatico:
    """k miembros climáticos repartidos a lo largo del registro (para evaluar candidatas rápido)."""
    if not k or esc.n_miembros <= k:
        return esc
    sel = np.linspace(0, esc.n_miembros - 1, k).round().astype(int)
    return replace(esc, miembros=[esc.miembros[i] for i in sel])


class _Evaluador:
    """Simula lotes de candidatas con theta y equilibrio de carbono fijos; guarda cada genoma ya evaluado."""

    def __init__(self, problema, catalogo, clima, escenario, suelo, theta, carbono_inicial, costos, lote=32):
        self.p, self.cat, self.clima, self.esc, self.suelo = problema, catalogo, clima, escenario, suelo
        self.theta, self.ci, self.costos, self.lote = theta, carbono_inicial, costos, lote
        self.memoria: dict[tuple, tuple[np.ndarray, np.ndarray]] = {}
        self.simuladas = 0

    def _simular(self, estrategias: list[Estrategia]) -> list[np.ndarray]:
        ens = ejecutar(self.clima, self.esc, self.suelo, estrategias, theta=self.theta, catalogo=self.cat,
                       referencia=None, carbono_inicial=self.ci)
        fijos = None
        if self.costos is not None:
            fijos = np.repeat([ind.costos_fijos_estrategia(e, self.costos) for e in estrategias], ens.K * ens.P)
        h = ind.por_miembro(ens.reg, ens.prog, ens.H, ens.p_intensa, ens.umbral_cobertura, fijos, self.costos)
        self.simuladas += len(estrategias)
        return [(valores_objetivo(h, ens.bloque(s), self.p.objetivos), float(h["riego_mm_anio"][ens.bloque(s)].mean()))
                for s in range(len(estrategias))]

    def evaluar(self, X: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        claves = [self.p.canonico(x) for x in X]
        pendientes = {}
        for k in claves:
            if k in self.memoria or k in pendientes:
                continue
            est, viol = self.p.decodificar(k, self.cat)
            g = np.array([viol[r] for r in RESTRICCIONES[:-1]] + [0.0])
            if np.any(g > 0):
                self.memoria[k] = (np.full(len(self.p.objetivos), PENALIDAD), g)
            else:
                pendientes[k] = (est, g)
        items = list(pendientes.items())
        for i in range(0, len(items), self.lote):
            parte = items[i:i + self.lote]
            for (k, (_, g)), (f, riego) in zip(parte, self._simular([e for _, (e, _) in parte])):
                if self.p.riego_tope_anio_mm is not None:
                    g = g.copy()
                    g[-1] = max(0.0, riego - self.p.riego_tope_anio_mm)
                self.memoria[k] = (f, g)
        F = np.stack([self.memoria[k][0] for k in claves])
        G = np.stack([self.memoria[k][1] for k in claves])
        return F, G

    def factibles(self) -> tuple[list[tuple], np.ndarray]:
        claves = [k for k, (f, g) in self.memoria.items() if np.all(g <= 0) and f[0] < PENALIDAD]
        F = np.stack([self.memoria[k][0] for k in claves]) if claves else np.zeros((0, len(self.p.objetivos)))
        return claves, F


class _ProblemaPymoo(Problem):
    def __init__(self, problema: ProblemaRotacion, evaluador: _Evaluador):
        xl, xu = problema.limites()
        super().__init__(n_var=len(xl), n_obj=len(problema.objetivos), n_ieq_constr=len(RESTRICCIONES), xl=xl,
                         xu=xu, vtype=int)
        self.evaluador = evaluador

    def _evaluate(self, X, out, *args, **kwargs):
        F, G = self.evaluador.evaluar(np.round(X).astype(int))
        out["F"], out["G"] = F, G


class _MuestreoRanuras(Sampling):
    """Población inicial con barbechos frecuentes (prob. 0,35) para partir de rotaciones sin solapes."""

    def __init__(self, problema: ProblemaRotacion):
        super().__init__()
        self.p = problema

    def _do(self, problem, n_samples, *args, random_state=None, **kwargs):
        rng = random_state if random_state is not None else np.random.default_rng()
        xl, xu = problem.xl.astype(int), problem.xu.astype(int)
        X = rng.integers(xl, xu + 1, size=(n_samples, problem.n_var))
        g = self.p.genes_por_ranura
        barbecho = rng.random((n_samples, len(self.p.ranuras))) < 0.35
        X[:, ::g] = np.where(barbecho, 0, X[:, ::g])
        return X


class _Historial(Callback):
    def __init__(self, objetivos):
        super().__init__()
        self.objetivos, self.filas = objetivos, []

    def notify(self, algorithm):
        F, CV = algorithm.pop.get("F"), algorithm.pop.get("CV")[:, 0]
        fact = CV <= 0
        fila = {"generacion": int(algorithm.n_gen), "factibles_en_poblacion": int(fact.sum()),
                "evaluaciones_simuladas": int(algorithm.problem.evaluador.simuladas)}
        if fact.any():
            fila["mejor_por_objetivo"] = {o: round(v, 4)
                                          for o, v in a_natural(self.objetivos, F[fact].min(0)).items()}
        self.filas.append(fila)


def _seleccionar(F: np.ndarray, n: int) -> list[int]:
    """Hasta n puntos del frente: el mejor en cada objetivo y luego los más alejados (muestreo del punto más lejano)."""
    if len(F) <= n:
        return list(range(len(F)))
    Fn = (F - F.min(0)) / np.maximum(F.max(0) - F.min(0), 1e-12)
    elegidos = list(dict.fromkeys(int(i) for i in Fn.argmin(0)))[:n]
    while len(elegidos) < n:
        d = np.min(np.linalg.norm(Fn[:, None, :] - Fn[None, elegidos, :], axis=2), axis=1)
        d[elegidos] = -1
        elegidos.append(int(d.argmax()))
    return elegidos


def _comparar(objetivos, f, f_base, tolerancia=0.02) -> dict:
    """Ganancias y cesiones de una solución frente a la línea base (en unidades naturales)."""
    nat, base = a_natural(objetivos, f), a_natural(objetivos, f_base)
    gana, cede, igual = [], [], []
    for o in objetivos:
        d = nat[o] - base[o]
        mejor = d > 0 if OBJETIVOS[o]["sentido"] == "max" else d < 0
        escala = max(abs(base[o]), 1e-6)
        texto = f"{OBJETIVOS[o]['texto']}: {base[o]:.3g} -> {nat[o]:.3g}"
        if abs(d) <= tolerancia * escala:
            igual.append(texto)
        elif mejor:
            gana.append(texto)
        else:
            cede.append(texto)
    return {"gana": gana, "cede": cede, "similar": igual}


def optimizar(clima: ClimaDiario, escenario: EscenarioClimatico, suelo: PerfilSuelo, problema: ProblemaRotacion,
              linea_base: Estrategia, poblacion: int = 24, generaciones: int = 15, miembros_clima: int = 4,
              muestras_parametros: int = 3, miembros_final: int | None = 8, muestras_final: int = 8,
              semilla: int = 42, calibracion: dict | None = None, costos: dict | None = None,
              max_soluciones: int = 10, catalogo: dict[str, Cultivo] | None = None) -> dict:
    """Corre NSGA-II y devuelve el frente evaluado con el ensamble completo, comparado con la línea base."""
    catalogo = catalogo or cargar_catalogo()
    if escenario.anios_horizonte != problema.horizonte_anios:
        raise ValueError("el escenario climático y el problema deben tener el mismo horizonte")
    if "costo" in problema.objetivos and costos is None:
        raise ValueError("el objetivo costo necesita precios del usuario (costos)")
    for op in problema.opciones.values():
        if op.cultivo not in catalogo:
            raise KeyError(f"opción {op.id}: cultivo {op.cultivo!r} fuera del catálogo")
        catalogo[op.cultivo].verificar_simulable(op.etapas)
    usados = sorted({op.cultivo for op in problema.opciones.values()} | {t.cultivo for t in linea_base.temporadas})
    theta = construir_theta(suelo, [catalogo[c] for c in usados], muestras_parametros, semilla, calibracion)
    esc_opt = submuestrear(escenario, miembros_clima)
    ens_base = ejecutar(clima, esc_opt, suelo, [linea_base], theta=theta, catalogo=catalogo, referencia=0)
    evaluador = _Evaluador(problema, catalogo, clima, esc_opt, suelo, theta, ens_base.carbono_inicial, costos)
    historial = _Historial(problema.objetivos)
    algoritmo = NSGA2(pop_size=poblacion, sampling=_MuestreoRanuras(problema),
                      crossover=SBX(prob=0.9, eta=3.0, vtype=float, repair=RoundingRepair()),
                      mutation=PM(prob=1.0, eta=3.0, vtype=float, repair=RoundingRepair()),
                      eliminate_duplicates=True)
    minimize(_ProblemaPymoo(problema, evaluador), algoritmo, ("n_gen", generaciones), seed=semilla,
             callback=historial, verbose=False)

    claves, F = evaluador.factibles()
    avisos = list(theta.avisos)
    if not claves:
        return {"frente": [], "avisos": avisos + ["NSGA-II no encontró rotaciones factibles: relajar restricciones "
                                                  "o ampliar opciones y campañas"],
                "historial": historial.filas, "evaluaciones_simuladas": evaluador.simuladas}
    nd = NonDominatedSorting().do(F, only_non_dominated_front=True)
    elegidos = [nd[i] for i in _seleccionar(F[nd], max_soluciones)]
    candidatas = [problema.decodificar(claves[i], catalogo, f"P{j + 1:02d}")[0] for j, i in enumerate(elegidos)]

    # Evaluación final: ensamble más amplio, mismo equilibrio de carbono respecto de la línea base
    esc_fin = submuestrear(escenario, miembros_final)
    ens = ejecutar(clima, esc_fin, suelo, [linea_base] + candidatas, n_parametros=muestras_final, semilla=semilla,
                   calibracion=calibracion, catalogo=catalogo, referencia=0)
    fijos = None
    if costos is not None:
        fijos = np.repeat([ind.costos_fijos_estrategia(e, costos) for e in [linea_base] + candidatas],
                          ens.K * ens.P)
    h = ind.por_miembro(ens.reg, ens.prog, ens.H, ens.p_intensa, ens.umbral_cobertura, fijos, costos)
    F_fin = np.stack([valores_objetivo(h, ens.bloque(s), problema.objetivos) for s in range(ens.S)])
    resumen = resumir_estrategias(ens, costos)
    f_base, F_cand = F_fin[0], F_fin[1:]
    nd_fin = set(NonDominatedSorting().do(F_fin, only_non_dominated_front=True).tolist())

    Fn = (F_cand - F_cand.min(0)) / np.maximum(F_cand.max(0) - F_cand.min(0), 1e-12)
    compromiso = int(np.linalg.norm(Fn, axis=1).argmin())
    mejor_por = {o: candidatas[int(F_cand[:, i].argmin())].id for i, o in enumerate(problema.objetivos)}
    frente = []
    for j, e in enumerate(candidatas):
        frente.append({**resumen[j + 1], "objetivos": a_natural(problema.objetivos, F_cand[j]),
                       "frente_a_linea_base": _comparar(problema.objetivos, F_cand[j], f_base),
                       "no_dominada_en_evaluacion_final": (j + 1) in nd_fin,
                       "domina_a_linea_base": bool(np.all(F_cand[j] <= f_base) and np.any(F_cand[j] < f_base))})
    explicacion = [
        "Ninguna rotación es la mejor en todo: el frente reúne opciones donde mejorar un objetivo obliga a ceder en "
        "otro. La elección depende de las prioridades del productor.",
        *(f"Mejor en {OBJETIVOS[o]['texto'][0].lower()}{OBJETIVOS[o]['texto'][1:]}: {i}"
          for o, i in mejor_por.items()),
        f"Compromiso equilibrado (más cercano al ideal con todos los objetivos normalizados y peso igual, SUPUESTO): "
        f"{candidatas[compromiso].id}",
    ]
    explicacion_claves = [
        {"clave": "tradeoff.no_single_best", "parametros": {}},
        *({"clave": "tradeoff.best_for", "parametros": {"objetivo": {"clave": f"objective.{o}"}, "id": i}}
          for o, i in mejor_por.items()),
        {"clave": "tradeoff.balanced", "parametros": {"id": candidatas[compromiso].id}},
    ]
    if not any(f["domina_a_linea_base"] for f in frente):
        explicacion.append("Ninguna candidata mejora a la línea base en todos los objetivos a la vez.")
        explicacion_claves.append({"clave": "tradeoff.none_dominates", "parametros": {}})
    return {
        "objetivos": [{"id": o, **OBJETIVOS[o], "texto_clave": f"objective.{o}"} for o in problema.objetivos],
        "restricciones": list(RESTRICCIONES),
        "linea_base": {**resumen[0], "objetivos": a_natural(problema.objetivos, f_base)},
        "frente": frente,
        "compromisos": {"mejor_por_objetivo": mejor_por, "compromiso_equilibrado": candidatas[compromiso].id,
                        "explicacion": explicacion, "explicacion_claves": explicacion_claves},
        "busqueda": {"algoritmo": "NSGA-II (pymoo)", "poblacion": poblacion, "generaciones": generaciones,
                     "miembros_clima_busqueda": esc_opt.n_miembros, "muestras_parametros_busqueda": muestras_parametros,
                     "miembros_clima_final": ens.K, "muestras_parametros_final": ens.P,
                     "evaluaciones_simuladas": evaluador.simuladas, "genomas_distintos": len(evaluador.memoria),
                     "factibles": len(claves), "no_dominadas_en_busqueda": len(nd), "historial": historial.filas,
                     "semilla": semilla},
        "reglas_sucesion": [r.__dict__ for r in problema.reglas],
        "ensamble_final": ens,
        "avisos": avisos,
    }


def problema_desde_dict(d: dict, horizonte_anios: int, clima_lote: str = "templado") -> tuple[ProblemaRotacion, list[str]]:
    """Construye el problema desde la sección `optimizacion` de un escenario YAML (ver contratos/gemelo_api.md)."""
    opciones = {}
    for oid, o in d["opciones"].items():
        opciones[oid] = OpcionCultivo(
            oid, o["cultivo"], o.get("cosechar", True), o.get("residuos", "superficie"),
            o.get("labranza_siembra", False), [Fertilizacion(int(f["dia"]), float(f["kg_n"]))
                                               for f in o.get("fertilizacion", [])],
            tuple(o["etapas"]) if o.get("etapas") else None, o.get("etapas_variante"))
    campanias = [Campania(c["nombre"], c["fecha"], list(c["opciones"])) for c in d["campanias"]]
    suc = d.get("sucesion", {})
    avisos = []
    reglas = []
    if suc.get("usar_reglas", True):
        reglas, avisos = cargar_reglas(suc.get("archivo"), suc.get("clima", clima_lote), suc.get("reglas"))
    riego = d.get("riego", {})
    prob = ProblemaRotacion(horizonte_anios, campanias, opciones, tuple(d.get("desfases_dias", [0])),
                            bool(riego.get("permitido", False)), riego.get("tope_mm_temporada"),
                            riego.get("tope_mm_anio"), reglas, list(d.get("exigidos", [])),
                            float(d.get("min_cosechas_por_anio", 1.0)), d.get("objetivos"))
    return prob, avisos
