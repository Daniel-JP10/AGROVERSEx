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

/**
 * Puntajes S por estrategia: normaliza cada objetivo entre las estrategias del mismo documento, promedia por deslizador y pondera.
 * shortcut: un objetivo sin valor se omite para esa estrategia y un deslizador sin ningún valor sale de la suma; revisar si el gemelo fija otra regla.
 */
export function puntajes(est: { id: string; valores: Valores }[], pesos: Pesos): Record<string, number> {
  const rango: Record<string, [number, number]> = {}
  for (const o of Object.keys(SENTIDO)) {
    const xs = est.map((e) => leer(e.valores, o)).filter(fin)
    if (xs.length) rango[o] = [Math.min(...xs), Math.max(...xs)]
  }
  const norm = (o: string, x: number) => {
    const [mn, mx] = rango[o]
    return mx === mn ? 0.5 : SENTIDO[o] === 'max' ? (x - mn) / (mx - mn) : (mx - x) / (mx - mn)
  }
  const suma = DESLIZADORES.reduce((a, k) => a + pesos[k], 0)
  return Object.fromEntries(est.map((e) => {
    if (suma <= 0) return [e.id, 0]
    let num = 0
    let den = 0
    for (const k of DESLIZADORES) {
      const ns = OBJETIVOS_DE[k].map((o) => { const x = leer(e.valores, o); return x === undefined ? undefined : norm(o, x) }).filter(fin)
      if (!ns.length) continue
      num += pesos[k] * (ns.reduce((a, b) => a + b, 0) / ns.length)
      den += pesos[k]
    }
    return [e.id, den > 0 ? num / den : 0]
  }))
}

/** Ids en orden de puntaje descendente; el empate conserva la posición original del documento. */
export function ordenar(est: { id: string; valores: Valores }[], pesos: Pesos): string[] {
  const s = puntajes(est, pesos)
  return est.map((e, i) => ({ id: e.id, i })).sort((a, b) => s[b.id] - s[a.id] || a.i - b.i).map((x) => x.id)
}

/** Ids de la línea base y el frente de un documento, en el orden que piden las prioridades. */
export const ordenDelDocumento = (doc: { linea_base: EstrategiaGemelo; frente: EstrategiaGemelo[] }, pesos: Pesos): string[] =>
  ordenar([doc.linea_base, ...doc.frente].map((e) => ({ id: e.id, valores: valoresDe(e) })), pesos)
