// asistido por SI: Claude Code (Anthropic), escritura y revisión de código; base del prototipo migrada en el hackatón
export interface Ventana { temporada: string; inicio: number | null; fin: number | null; error_semanas: number | null; detectada: number }
export interface Lote { id?: string; unidad_id?: string; geom_wkt?: string; cultivo_actual?: string; ventanas: Ventana[] }

// Última temporada con detección; inicio y fin son días desde 2000-01-01.
export function ventanaSueloExpuesto(lote: Pick<Lote, 'ventanas'>): { inicio: number; fin: number; errorSemanas: number } | null {
  const v = [...lote.ventanas].reverse().find((x) => x.detectada && x.inicio !== null && x.fin !== null)
  return v ? { inicio: v.inicio!, fin: v.fin!, errorSemanas: v.error_semanas ?? NaN } : null
}

export interface Riesgo { id: string; nombre: string; resolucion: string | null; valor: number | null; nota: string }
// Valores en NULL: no hay pendiente de 30 m ni validación POWER; no se inventan.
export const RIESGOS: Record<'erosion' | 'estres' | 'helada', Riesgo> = {
  erosion: { id: 'erosion', nombre: 'Erosión', resolucion: null, valor: null, nota: 'PENDIENTE: sin pendiente NASADEM de 30 m en la base' },
  estres: { id: 'estres', nombre: 'Estrés hídrico', resolucion: 'SMAP 9 km', valor: null, nota: 'sin cifra por lote' },
  helada: { id: 'helada', nombre: 'Helada', resolucion: 'POWER ~0,5°', valor: null, nota: 'PENDIENTE: validación POWER' },
}
export const rotuloRiesgo = (r: Riesgo) => (r.resolucion ? `contexto de ${r.resolucion}, no del lote` : 'escala de lote (erosión)')

export const fechaDia = (d: number) => new Date(Date.UTC(2000, 0, 1) + d * 864e5).toISOString().slice(0, 10)
