// asistido por SI: Claude Code (Anthropic), escritura y revisión de código; base del prototipo migrada en el hackatón
export interface Ventana { temporada: string; inicio: number | null; fin: number | null; error_semanas: number | null; detectada: number }
export interface Lote { id?: string; unidad_id?: string; geom_wkt?: string; cultivo_actual?: string; ventanas: Ventana[] }

// Última temporada con detección; inicio y fin son días desde 2000-01-01.
export function ventanaSueloExpuesto(lote: Pick<Lote, 'ventanas'>): { inicio: number; fin: number; errorSemanas: number } | null {
  const v = [...lote.ventanas].reverse().find((x) => x.detectada && x.inicio !== null && x.fin !== null)
  return v ? { inicio: v.inicio!, fin: v.fin!, errorSemanas: v.error_semanas ?? NaN } : null
}

import { t } from '../../textos/i18n'
import type { ClaveTexto } from '../../textos/en'

/** nombre y nota son claves de texto: se traducen al mostrar */
export interface Riesgo { id: string; nombre: ClaveTexto; resolucion: string | null; valor: number | null; nota: ClaveTexto }
// Valores en NULL: no hay pendiente de 30 m ni validación POWER; no se inventan.
export const RIESGOS: Record<'erosion' | 'estres' | 'helada', Riesgo> = {
  erosion: { id: 'erosion', nombre: 'lotes.riesgo.erosion', resolucion: null, valor: null, nota: 'lotes.riesgo.erosion.nota' },
  estres: { id: 'estres', nombre: 'lotes.riesgo.estres', resolucion: 'SMAP 9 km', valor: null, nota: 'lotes.riesgo.estres.nota' },
  helada: { id: 'helada', nombre: 'lotes.riesgo.helada', resolucion: 'POWER ~0,5°', valor: null, nota: 'lotes.riesgo.helada.nota' },
}
export const rotuloRiesgo = (r: Riesgo) => (r.resolucion ? `${t('lotes.contextoDe')} ${r.resolucion}, ${t('lotes.noDelLote')}` : t('lotes.escalaLote'))

export const fechaDia = (d: number) => new Date(Date.UTC(2000, 0, 1) + d * 864e5).toISOString().slice(0, 10)
