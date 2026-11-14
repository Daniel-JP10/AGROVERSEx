// asistido por SI: Claude Code (Anthropic), escritura y revisión de código; base del prototipo migrada en el hackatón
import { paraMostrar } from '../comun/unidades'
import { t } from '../textos/i18n'
import type { ClaveTexto } from '../textos/es'

export type Tema = 'Agua' | 'Clima' | 'Vegetación'
export interface Capa {
  id: string
  tema: Tema
  nombre: string
  unidad: string
  /** Unidad en que la base entrega la capa (solo las que se convierten para mostrar) */
  unidadProducto?: string
  /** Escala de color; SUPUESTO visual, lo que se salga se pinta en el extremo */
  rango: [number, number]
  fraccion?: string
  /** Clave del calendario de producto (tiempo/huecos.ts) */
  calendario: string
}

export const CAPAS: Capa[] = [
  { id: 'precip', tema: 'Agua', get nombre() { return t('capa.precip') }, unidad: 'mm/mes', unidadProducto: 'mm/h', rango: [0, 500], fraccion: 'precip_frac', calendario: 'imerg' },
  { id: 'sm_sup', tema: 'Agua', get nombre() { return t('capa.sm_sup') }, unidad: 'm³/m³', rango: [0, 0.6], fraccion: 'sm_frac', calendario: 'smap_l3' },
  { id: 'sm_raiz', tema: 'Agua', get nombre() { return t('capa.sm_raiz') }, unidad: 'm³/m³', rango: [0, 0.6], fraccion: 'sm_frac', calendario: 'smap_l3' },
  { id: 'tws', tema: 'Agua', get nombre() { return t('capa.tws') }, unidad: 'cm', rango: [-30, 30], fraccion: 'tws_frac', calendario: 'grace' },
  { id: 't2m', tema: 'Clima', get nombre() { return t('capa.t2m') }, unidad: '°C', rango: [-30, 40], calendario: 'power' },
  { id: 'rad_sw', tema: 'Clima', get nombre() { return t('capa.rad_sw') }, unidad: 'MJ/m²/día', rango: [0, 30], calendario: 'power' },
  { id: 'rh2m', tema: 'Clima', get nombre() { return t('capa.rh2m') }, unidad: '%', rango: [0, 100], calendario: 'power' },
  { id: 'ndvi', tema: 'Vegetación', nombre: 'NDVI', unidad: 'adimensional', rango: [0, 1], fraccion: 'ndvi_frac', calendario: 'mod13' },
  { id: 'et', tema: 'Vegetación', get nombre() { return t('capa.et') }, unidad: 'kg/m²/8 días', rango: [0, 60], fraccion: 'et_frac', calendario: 'mod16' },
  { id: 'lst_dia', tema: 'Vegetación', get nombre() { return t('capa.lst_dia') }, unidad: 'K', rango: [250, 330], fraccion: 'lst_frac', calendario: 'mod11' },
]

export const CAPA_INICIAL = 'precip'
export const capaPorId = (id: string): Capa => CAPAS.find((c) => c.id === id) ?? CAPAS[0]
export const TEMAS: Tema[] = ['Agua', 'Clima', 'Vegetación']
export const TEMA_CLAVE: Record<Tema, ClaveTexto> = { Agua: 'tema.Agua', Clima: 'tema.Clima', Vegetación: 'tema.Vegetación' }

// La unidad la pone quien llama (Final mm/hr, Late mm/day); sin valor por omisión; se muestra en mm/mes con los días reales del mes
export function valoresCapa(c: Capa, valores: Float32Array, mes: number, unidad: string): Float32Array {
  if (c.id !== 'precip') return valores
  return valores.map((x) => paraMostrar('precip', x, unidad, mes).valor as number)
}
