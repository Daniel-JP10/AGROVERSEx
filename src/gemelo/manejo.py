# asistido por SI: Cursor (agente), escritura y revisión de código; núcleo del gemelo digital en el hackatón
"""Compila una Estrategia (decisiones u) a series diarias que consume la dinámica.

Todo lo que depende solo del calendario se calcula aquí una vez; lo que depende de parámetros muestreados
(Kc, Zr, RUE, ...) se resuelve en la dinámica con los pesos de fenologia.pesos_kc.
"""
from dataclasses import dataclass

import numpy as np

from gemelo.fenologia import duraciones, fraccion_raiz, pesos_kc
from gemelo.modelos import Estrategia, fecha_legible
from gemelo.parametros import Cultivo


@dataclass
class Programa:
    """Series diarias (T,) de una estrategia. cult = -1 en barbecho."""
    estrategia: Estrategia
    cult: np.ndarray            # índice del cultivo en la lista `cultivos` del lote de simulación
    temporada: np.ndarray       # índice de temporada, -1 en barbecho
    dds: np.ndarray             # días desde la siembra
    w_ini: np.ndarray
    w_mid: np.ndarray
    w_end: np.ndarray
    f_raiz: np.ndarray
    siembra: np.ndarray         # bool, día de siembra
    cosecha: np.ndarray         # bool, último día de la temporada
    cosechar: np.ndarray        # bool, la cosecha exporta producto (False: cobertura incorporada)
    incorporar: np.ndarray      # bool, en la cosecha el residuo se incorpora
    labranza: np.ndarray        # bool, labranza al sembrar
    fert: np.ndarray            # kg N/ha aplicados ese día
    riego_auto: np.ndarray      # bool
    riego_umbral: np.ndarray
    riego_tope: np.ndarray      # mm brutos por temporada (inf sin tope)
    duraciones: list[tuple[int, int, int, int]]

    @property
    def T(self) -> int:
        return len(self.cult)


def compilar(estrategia: Estrategia, catalogo: dict[str, Cultivo], indice: dict[str, int], T: int) -> Programa:
    cult = np.full(T, -1, np.int32)
    temp = np.full(T, -1, np.int32)
    dds = np.zeros(T)
    w = [np.zeros(T) for _ in range(3)]
    f_raiz = np.zeros(T)
    siembra, cosecha, cosechar, incorporar, labranza, riego_auto = (np.zeros(T, bool) for _ in range(6))
    fert = np.zeros(T)
    umbral = np.ones(T)
    tope = np.full(T, np.inf)
    durs = []
    fin_anterior = -1
    for k, t in enumerate(estrategia.temporadas):
        if t.cultivo not in catalogo:
            raise KeyError(f"cultivo {t.cultivo!r} no está en el catálogo")
        c = catalogo[t.cultivo]
        c.verificar_simulable(t.etapas)
        e = duraciones(c, t.etapas, t.etapas_variante)
        dur = sum(e)
        ini, fin = t.siembra, t.siembra + dur - 1
        if ini <= fin_anterior:
            raise ValueError(f"{estrategia.id}: la temporada {k + 1} ({t.cultivo}) se siembra el "
                             f"{fecha_legible(ini)}, antes de terminar la anterior")
        if fin >= T:
            raise ValueError(f"{estrategia.id}: la temporada {k + 1} ({t.cultivo}) termina después del horizonte")
        sl = slice(ini, fin + 1)
        d = np.arange(dur)
        cult[sl], temp[sl], dds[sl] = indice[t.cultivo], k, d
        for arr, val in zip(w, pesos_kc(d, e)):
            arr[sl] = val
        f_raiz[sl] = fraccion_raiz(d, e)
        siembra[ini] = True
        labranza[ini] = t.labranza_siembra
        cosecha[fin] = True
        cosechar[fin] = t.cosechar
        incorporar[fin] = t.residuos == "incorporar"
        riego_auto[sl] = t.riego.modo == "automatico"
        umbral[sl] = t.riego.umbral
        tope[sl] = np.inf if t.riego.tope_mm is None else t.riego.tope_mm
        for f in t.fertilizacion:
            if f.dia >= dur:
                raise ValueError(f"{estrategia.id}: fertilización el día {f.dia} después de la cosecha ({dur} días)")
            fert[ini + f.dia] += f.kg_n
        durs.append(e)
        fin_anterior = fin
    return Programa(estrategia, cult, temp, dds, *w, f_raiz, siembra, cosecha, cosechar, incorporar, labranza,
                    fert, riego_auto, umbral, tope, durs)


def apilar(programas: list[Programa], repeticiones: int) -> dict[str, np.ndarray]:
    """Series (M, T) con M = len(programas) * repeticiones; el miembro m usa el programa m // repeticiones."""
    claves = ("cult", "temporada", "dds", "w_ini", "w_mid", "w_end", "f_raiz", "siembra", "cosecha", "cosechar",
              "incorporar", "labranza", "fert", "riego_auto", "riego_umbral", "riego_tope")
    return {k: np.repeat(np.stack([getattr(p, k) for p in programas]), repeticiones, axis=0) for k in claves}
