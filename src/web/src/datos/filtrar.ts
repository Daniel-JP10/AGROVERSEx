// asistido por SI: Claude Code (Anthropic), escritura y revisión de código; base del prototipo migrada en el hackatón
// Filtros globales: se traducen a FiltroUnidad (motor de la Task 6), no a filtros de capa.
export interface AtributosUnidad {
  id: string
  lat?: number; elevMin?: number; elevMax?: number; ph?: number; pendiente?: number
  koppen?: string; igbp?: number; macro?: string; condicion?: string; zona?: string
  eventos?: boolean; heladas?: boolean; riego?: number; grace?: boolean; unimodal?: boolean; cultivo?: boolean
  valor?: number; fraccion?: number // del mes en curso; undefined = sin dato (nunca 0)
}

export interface FiltrosGlobales {
  rango?: [number, number]; fraccionMin?: number
  koppen?: string[]; igbp?: number[]; macro?: string[]; zona?: string[] // zona: tabla zona_demo, opcional
  enso?: 'nino' | 'nina' | 'neutro'; soloEventos?: boolean; clase?: string[]
}

// SUPUESTO: |RONI| >= 0,5 °C (convención de NOAA para el ONI, aplicada al RONI sin respaldo propio).
export const UMBRAL_RONI: number | undefined = 0.5

export interface ContextoEnso { roni: number[]; umbral?: number }

export function mesCumpleEnso(e: NonNullable<FiltrosGlobales['enso']>, mes: number, c?: ContextoEnso): boolean {
  const u = c?.umbral
  if (u === undefined || !c) return true // PENDIENTE: no se filtra
  const r = c.roni[mes]
  if (!Number.isFinite(r)) return false
  return e === 'nina' ? r <= -u : e === 'nino' ? r >= u : Math.abs(r) < u
}

const en = <T>(lista: T[] | undefined, v: T | undefined) => !lista?.length || (v !== undefined && lista.includes(v))

export function aplicarFiltros(unidades: AtributosUnidad[], f: FiltrosGlobales, mes: number, enso?: ContextoEnso): Set<string> {
  if (f.enso && !mesCumpleEnso(f.enso, mes, enso)) return new Set()
  const ok = (u: AtributosUnidad) =>
    en(f.koppen, u.koppen) && en(f.igbp, u.igbp) && en(f.macro, u.macro) && en(f.zona, u.zona) && en(f.clase, u.condicion) &&
    (!f.soloEventos || u.eventos === true) &&
    (!f.rango || (u.valor !== undefined && u.valor >= f.rango[0] && u.valor <= f.rango[1])) &&
    (f.fraccionMin === undefined || (u.fraccion !== undefined && u.fraccion >= f.fraccionMin))
  return new Set(unidades.filter(ok).map((u) => u.id))
}

/** Ids filtrados (el complemento de los visibles); el motor los pinta distinto de un hueco. */
export function ocultasPorFiltros(unidades: AtributosUnidad[], f: FiltrosGlobales, mes: number, enso?: ContextoEnso): Set<string> {
  const vis = aplicarFiltros(unidades, f, mes, enso)
  return new Set(unidades.filter((u) => !vis.has(u.id)).map((u) => u.id))
}
