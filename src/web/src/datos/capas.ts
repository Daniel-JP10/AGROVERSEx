// asistido por SI: Claude Code (Anthropic), escritura y revisión de código; base del prototipo migrada en el hackatón
import { mmHoraAMmMes } from './desescalar'

export type Tema = 'Agua' | 'Clima' | 'Vegetación'
export interface Capa {
  id: string
  tema: Tema
  nombre: string
  unidad: string
  /** Escala de color; SUPUESTO visual, lo que se salga se pinta en el extremo */
  rango: [number, number]
  fraccion?: string
  /** Clave del calendario de producto (tiempo/huecos.ts) */
  calendario: string
}

export const CAPAS: Capa[] = [
  { id: 'precip', tema: 'Agua', nombre: 'Lluvia mensual', unidad: 'mm/mes', rango: [0, 500], fraccion: 'precip_frac', calendario: 'imerg' },
  { id: 'sm_sup', tema: 'Agua', nombre: 'Humedad superficial', unidad: 'm³/m³', rango: [0, 0.6], fraccion: 'sm_frac', calendario: 'smap_l3' },
  { id: 'sm_raiz', tema: 'Agua', nombre: 'Humedad en la raíz', unidad: 'm³/m³', rango: [0, 0.6], fraccion: 'sm_frac', calendario: 'smap_l3' },
  { id: 'tws', tema: 'Agua', nombre: 'Agua almacenada (contexto regional)', unidad: 'cm', rango: [-30, 30], fraccion: 'tws_frac', calendario: 'grace' },
  { id: 't2m', tema: 'Clima', nombre: 'Temperatura a 2 m', unidad: '°C', rango: [-30, 40], calendario: 'power' },
  { id: 'rad_sw', tema: 'Clima', nombre: 'Radiación solar', unidad: 'MJ/m²/día', rango: [0, 30], calendario: 'power' },
  { id: 'rh2m', tema: 'Clima', nombre: 'Humedad relativa', unidad: '%', rango: [0, 100], calendario: 'power' },
  { id: 'ndvi', tema: 'Vegetación', nombre: 'NDVI', unidad: 'adimensional', rango: [0, 1], fraccion: 'ndvi_frac', calendario: 'mod13' },
  { id: 'et', tema: 'Vegetación', nombre: 'Evapotranspiración', unidad: 'kg/m²/8 días', rango: [0, 60], fraccion: 'et_frac', calendario: 'mod16' },
  { id: 'lst_dia', tema: 'Vegetación', nombre: 'Temperatura de la superficie', unidad: 'K', rango: [250, 330], fraccion: 'lst_frac', calendario: 'mod11' },
]

export const CAPA_INICIAL = 'precip'
export const capaPorId = (id: string): Capa => CAPAS.find((c) => c.id === id) ?? CAPAS[0]
export const TEMAS: Tema[] = ['Agua', 'Clima', 'Vegetación']

// La base guarda la lluvia en mm/h, como IMERG; se muestra en mm/mes con los días reales del mes
export function valoresCapa(c: Capa, valores: Float32Array, mes: number): Float32Array {
  if (c.id !== 'precip') return valores
  const dias = new Date(Date.UTC(2000, mes + 1, 0)).getUTCDate()
  return valores.map((x) => mmHoraAMmMes(x, dias))
}
