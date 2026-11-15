// asistido por SI: Claude Code (Anthropic), orden de estrategias por prioridades del agricultor según contratos/gemelo_api.md §4 (v1.2)
import type { EstrategiaGemelo } from './gemelo'

export type Deslizador = 'agua' | 'suelo' | 'insumos' | 'estabilidad_climatica'
export const DESLIZADORES: readonly Deslizador[] = ['agua', 'suelo', 'insumos', 'estabilidad_climatica']
export type Pesos = Record<Deslizador, number>
export const PESO_MAX = 5

// Mapa fijo del contrato (§4); pruebas/rotaciones_prioridades.test.ts lo compara con contratos/prioridades_casos.json
export const OBJETIVOS_DE: Record<Deslizador, readonly string[]> = {
  agua: ['riego', 'deficit'], suelo: ['carbono', 'exposicion_erosiva'], insumos: ['fertilizante'], estabilidad_climatica: ['riesgo_produccion'],
}
export const SENTIDO: Record<string, 'max' | 'min'> = {
  riego: 'min', deficit: 'min', carbono: 'max', exposicion_erosiva: 'min', fertilizante: 'min', riesgo_produccion: 'max',
}
// Alias obsoleto hasta la v2: si falta el objetivo nuevo se lee el viejo (mismo valor)
const ALIAS: Record<string, string> = { exposicion_erosiva: 'lluvia_intensa_suelo_desnudo' }

export const PESOS_IGUALES: Pesos = { agua: 1, suelo: 1, insumos: 1, estabilidad_climatica: 1 }

type Valores = Record<string, number | null | undefined>
const fin = (v: unknown): v is number => typeof v === 'number' && Number.isFinite(v)

/** Valores naturales por objetivo: `metricas` (paquete del gemelo) y, si no, `objetivos` (ejemplo y optimización v1). */
export const valoresDe = (e: Pick<EstrategiaGemelo, 'metricas' | 'objetivos'>): Valores => ({ ...e.objetivos, ...e.metricas })
const leer = (v: Valores, o: string): number | undefined => {
  const x = v[o] ?? (ALIAS[o] ? v[ALIAS[o]] : undefined)
  return fin(x) ? x : undefined
}

/** Objetivos de prioridad que le faltan a cada estrategia incompleta; las completas no aparecen. Nunca se imputa un valor (D-039.4). */
export function faltantes(est: { id: string; valores: Valores }[]): Record<string, string[]> {
  const f: Record<string, string[]> = {}
  for (const e of est) {
    const falta = Object.keys(SENTIDO).filter((o) => leer(e.valores, o) === undefined)
    if (falta.length) f[e.id] = falta
  }
  return f
}

/** Normalizado de cada objetivo entre todas las estrategias del documento que tienen valor en ese objetivo (C-4, D-039). */
function normalizador(est: { valores: Valores }[]) {
  const rango: Record<string, [number, number]> = {}
  for (const o of Object.keys(SENTIDO)) {
    const xs = est.map((e) => leer(e.valores, o)).filter(fin)
    if (xs.length) rango[o] = [Math.min(...xs), Math.max(...xs)]
  }
  return (o: string, x: number) => {
    const [mn, mx] = rango[o]
    return mx === mn ? 0.5 : SENTIDO[o] === 'max' ? (x - mn) / (mx - mn) : (mx - x) / (mx - mn)
  }
}

/**
 * Puntajes S de las estrategias completas: normaliza cada objetivo (normalizador), promedia por deslizador y pondera.
 * Las incompletas no tienen puntaje.
 */
export function puntajes(est: { id: string; valores: Valores }[], pesos: Pesos): Record<string, number> {
  const norm = normalizador(est)
  const suma = DESLIZADORES.reduce((a, k) => a + pesos[k], 0)
  const falta = faltantes(est)
  return Object.fromEntries(est.filter((e) => !falta[e.id]).map((e) => {
    if (suma <= 0) return [e.id, 0]
    const num = DESLIZADORES.reduce((a, k) => a + pesos[k] * (OBJETIVOS_DE[k].reduce((b, o) => b + norm(o, leer(e.valores, o)!), 0) / OBJETIVOS_DE[k].length), 0)
    return [e.id, num / suma]
  }))
}

/**
 * Ids: primero las completas por puntaje descendente (empate: posición original). Después las incompletas (C-4, D-039):
 * menos objetivos faltantes, luego mayor suma de normalizados disponibles, luego id, para que sea determinista.
 */
export function ordenar(est: { id: string; valores: Valores }[], pesos: Pesos): string[] {
  const s = puntajes(est, pesos)
  const con = est.map((e, i) => ({ id: e.id, i })).filter((x) => x.id in s).sort((a, b) => s[b.id] - s[a.id] || a.i - b.i)
  const norm = normalizador(est)
  const falta = faltantes(est)
  const sumaDisponible = (v: Valores) => Object.keys(SENTIDO).reduce((a, o) => { const x = leer(v, o); return x === undefined ? a : a + norm(o, x) }, 0)
  const sin = est.filter((e) => !(e.id in s)).map((e) => ({ id: e.id, n: falta[e.id].length, suma: sumaDisponible(e.valores) }))
    .sort((a, b) => a.n - b.n || b.suma - a.suma || (a.id < b.id ? -1 : a.id > b.id ? 1 : 0))
  return [...con.map((x) => x.id), ...sin.map((x) => x.id)]
}

/** Ids de la línea base y el frente de un documento, en el orden que piden las prioridades. */
const deDocumento = (doc: { linea_base: EstrategiaGemelo; frente: EstrategiaGemelo[] }) => [doc.linea_base, ...doc.frente].map((e) => ({ id: e.id, valores: valoresDe(e) }))

/** Estrategias incompletas de un documento con sus objetivos sin dato. */
export const faltantesDelDocumento = (doc: { linea_base: EstrategiaGemelo; frente: EstrategiaGemelo[] }) => faltantes(deDocumento(doc))

export const ordenDelDocumento = (doc: { linea_base: EstrategiaGemelo; frente: EstrategiaGemelo[] }, pesos: Pesos): string[] =>
  ordenar(deDocumento(doc), pesos)
