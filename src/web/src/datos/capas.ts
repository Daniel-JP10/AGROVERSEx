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
  /** Escala de color; SUPUESTO visual, lo que se salga se pinta en el extremo */
  rango: [number, number]
  /** Clave del calendario de producto (tiempo/huecos.ts) */
  calendario: string
}

// Solo las cuatro variables núcleo con dato real (T-D2, Colombia). Las capas simuladas de la fase 1 salieron: no hay dato real que las respalde.
export const CAPAS: Capa[] = [
  { id: 'precip', tema: 'Agua', get nombre() { return t('capa.precip') }, get unidad() { return t('unidad.mmMes') }, rango: [0, 500], calendario: 'imerg' },
  { id: 'sm_raiz', tema: 'Agua', get nombre() { return t('capa.sm_raiz') }, unidad: 'kg/m²', rango: [0, 900], calendario: 'gldas' },
  { id: 't2m', tema: 'Clima', get nombre() { return t('capa.t2m') }, unidad: '°C', rango: [-10, 35], calendario: 'merra2' },
  { id: 'ndvi', tema: 'Vegetación', nombre: 'NDVI', get unidad() { return t('unidad.adimensional') }, rango: [0, 1], calendario: 'mod13' },
]

export const CAPA_INICIAL = 'precip'
export const capaPorId = (id: string): Capa => CAPAS.find((c) => c.id === id) ?? CAPAS[0]
export const TEMAS: Tema[] = ['Agua', 'Clima', 'Vegetación']
export const TEMA_CLAVE: Record<Tema, ClaveTexto> = { Agua: 'tema.Agua', Clima: 'tema.Clima', Vegetación: 'tema.Vegetación' }

// La unidad del producto la pone quien llama (Final mm/hr, Late mm/day, T2M en K...); la conversión a pantalla es de paraMostrar.
export function valoresCapa(c: Capa, valores: Float32Array, mes: number, unidad: string): Float32Array {
  return valores.map((x) => (Number.isNaN(x) ? x : (paraMostrar(c.id, x, unidad, mes).valor as number)))
}
