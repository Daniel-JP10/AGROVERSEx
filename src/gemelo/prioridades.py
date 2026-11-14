# asistido por SI: Cursor (agente), escritura y revisión de código; núcleo del gemelo digital en el hackatón
"""Prioridades del agricultor (contrato v1.1): los cuatro deslizadores de Web sobre los objetivos del gemelo.

    n(o, s) = (x(o, s) - min_o) / (max_o - min_o)        si el objetivo se maximiza
    n(o, s) = (max_o - x(o, s)) / (max_o - min_o)        si se minimiza
    n(o, s) = 0,5                                        si max_o = min_o
    S(s)    = sum_k w_k * media_{o en k} n(o, s) / sum_k w_k      (w_k >= 0; 0 si todos los pesos son 0)

min y max se toman sobre las estrategias del mismo documento (línea base y frente, o las estrategias simuladas).
Orden: S descendente; empate, posición original en el documento. Es el mismo esquema que `ordenar.ts` de Web.
Insumos = fertilizante_n_kg_ha_anio (D-007) mientras el costo siga PENDIENTE.
"""
import numpy as np

from gemelo import indicadores as ind
from gemelo.optimizacion import OBJETIVOS, a_natural, valores_objetivo

DESLIZADORES = {
    "agua": ("riego", "deficit"),
    "suelo": ("carbono", "lluvia_intensa_suelo_desnudo"),
    "insumos": ("fertilizante",),
    "estabilidad_climatica": ("riesgo_produccion",),
}
METRICAS = tuple(dict.fromkeys(o for objs in DESLIZADORES.values() for o in objs))
# Objetivos que se reportan para todas las estrategias (tarjetas y prioridades); costo solo con precios
METRICAS_TODAS = tuple(o for o in OBJETIVOS if o != "costo")

FORMULA = {
    "normalizado_max": "n = (x - min) / (max - min)",
    "normalizado_min": "n = (max - x) / (max - min)",
    "empate_en_objetivo": "n = 0.5 si max = min",
    "puntaje": "S = sum_k w_k * media_{o en k} n_o / sum_k w_k; S = 0 si sum_k w_k = 0",
    "orden": "S descendente; empate: posición original en el documento",
    "pesos": "w_k >= 0 (Web usa 0 a 5)",
    "conjunto": "estrategias del mismo documento (linea_base + frente, o estrategias)",
}


def metricas_ensamble(ens, costos: dict | None = None) -> list[dict[str, float]]:
    """Valores naturales de todos los objetivos (media del ensamble; CVaR 90 % para riesgo) por estrategia."""
    h = ind.por_miembro(ens.reg, ens.prog, ens.H, ens.p_intensa, ens.umbral_cobertura)
    return [a_natural(list(METRICAS_TODAS), valores_objetivo(h, ens.bloque(s), list(METRICAS_TODAS)))
            for s in range(ens.S)]


def normalizar(valores: dict[str, dict[str, float]], objetivos=METRICAS) -> dict[str, dict[str, float]]:
    ids = list(valores)
    out = {i: {} for i in ids}
    for o in objetivos:
        x = np.array([valores[i][o] for i in ids], float)
        lo, hi = float(x.min()), float(x.max())
        for i, v in zip(ids, x):
            if hi - lo <= 1e-12 * max(1.0, abs(hi)):
                n = 0.5
            elif OBJETIVOS[o]["sentido"] == "max":
                n = (v - lo) / (hi - lo)
            else:
                n = (hi - v) / (hi - lo)
            out[i][o] = round(float(n), 6)
    return out


def por_deslizador(normalizados: dict[str, dict[str, float]]) -> dict[str, dict[str, float]]:
    return {i: {k: round(float(np.mean([n[o] for o in objs])), 6) for k, objs in DESLIZADORES.items()}
            for i, n in normalizados.items()}


def puntajes(normalizados: dict[str, dict[str, float]], pesos: dict[str, float]) -> dict[str, float]:
    if any(float(pesos.get(k, 0)) < 0 for k in DESLIZADORES):
        raise ValueError("los pesos deben ser >= 0")
    suma = sum(float(pesos.get(k, 0)) for k in DESLIZADORES)
    d = por_deslizador(normalizados)
    if suma == 0:
        return {i: 0.0 for i in d}
    return {i: sum(float(pesos.get(k, 0)) * v[k] for k in DESLIZADORES) / suma for i, v in d.items()}


def ordenar(normalizados: dict[str, dict[str, float]], pesos: dict[str, float]) -> list[str]:
    s = puntajes(normalizados, pesos)
    pos = {i: n for n, i in enumerate(normalizados)}
    return sorted(s, key=lambda i: (-round(s[i], 12), pos[i]))


PESOS_IGUALES = {k: 1 for k in DESLIZADORES}

# Tabla sintética fija para que Web compruebe su implementación (no son resultados del modelo)
TABLA_PRUEBA = {
    "X": {"riego": 0.0, "deficit": 0.30, "carbono": -0.10, "lluvia_intensa_suelo_desnudo": 30.0,
          "fertilizante": 150.0, "riesgo_produccion": 0.30},
    "Y": {"riego": 0.0, "deficit": 0.20, "carbono": 0.05, "lluvia_intensa_suelo_desnudo": 20.0,
          "fertilizante": 100.0, "riesgo_produccion": 0.25},
    "Z": {"riego": 0.0, "deficit": 0.25, "carbono": -0.30, "lluvia_intensa_suelo_desnudo": 35.0,
          "fertilizante": 50.0, "riesgo_produccion": 0.40},
}
CASOS_PRUEBA = [
    {"nombre": "pesos iguales", "pesos": {"agua": 1, "suelo": 1, "insumos": 1, "estabilidad_climatica": 1},
     "puntajes": {"X": 0.258929, "Y": 0.5625, "Z": 0.625}, "orden": ["Z", "Y", "X"]},
    {"nombre": "solo suelo", "pesos": {"agua": 0, "suelo": 5, "insumos": 0, "estabilidad_climatica": 0},
     "puntajes": {"X": 0.452381, "Y": 1.0, "Z": 0.0}, "orden": ["Y", "X", "Z"]},
    {"nombre": "agua alta y algo de estabilidad", "pesos": {"agua": 5, "suelo": 0, "insumos": 0,
                                                            "estabilidad_climatica": 1},
     "puntajes": {"X": 0.263889, "Y": 0.625, "Z": 0.583333}, "orden": ["Y", "Z", "X"]},
    {"nombre": "todos los pesos en cero", "pesos": {"agua": 0, "suelo": 0, "insumos": 0, "estabilidad_climatica": 0},
     "puntajes": {"X": 0.0, "Y": 0.0, "Z": 0.0}, "orden": ["X", "Y", "Z"]},
]


def bloque(valores: dict[str, dict[str, float]]) -> dict:
    """Bloque `prioridades` del documento: mapeo, fórmula, valores, normalizados y orden con pesos iguales."""
    norm = normalizar(valores)
    return {
        "deslizadores": {k: {"objetivos": [{"id": o, "indicador": OBJETIVOS[o]["indicador"],
                                            "sentido": OBJETIVOS[o]["sentido"]} for o in objs],
                             "rotulo_clave": f"priority.{k}"} for k, objs in DESLIZADORES.items()},
        "nota_insumos": "insumos = fertilizante_n_kg_ha_anio (D-007) mientras costo_anio siga PENDIENTE",
        "formula": FORMULA,
        "formula_clave": "priority.formula",
        "valores": {i: {o: v[o] for o in METRICAS} for i, v in valores.items()},
        "normalizados": norm,
        "por_deslizador": por_deslizador(norm),
        "pesos_iguales": {"pesos": PESOS_IGUALES, "puntajes": {i: round(s, 6) for i, s in
                                                               puntajes(norm, PESOS_IGUALES).items()},
                          "orden": ordenar(norm, PESOS_IGUALES)},
        "casos_prueba": {"tabla": TABLA_PRUEBA, "casos": CASOS_PRUEBA},
    }
