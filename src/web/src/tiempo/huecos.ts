// asistido por SI: Claude Code (Anthropic), escritura y revisión de código; base del prototipo migrada en el hackatón
import { t } from '../textos/i18n'
import type { ClaveTexto } from '../textos/en'
import { N_MESES } from './valor'

export const mesIdAEtiqueta = (mes: number) => `${t(`mes.corto.${(mes % 12) + 1}` as ClaveTexto)}-${2000 + Math.floor(mes / 12)}`

export interface Producto {
  nombre: string
  inicio: number
  fin: number
  /** Meses enteros sin solución dentro de [inicio, fin] */
  huecos?: number[]
  /** Meses con hueco de días, pero con algo de dato */
  parciales?: number[]
  provisionalDesde?: number
}

const id = (a: number, m: number) => (a - 2000) * 12 + m - 1
const rango = (a: number, b: number) => Array.from({ length: b - a + 1 }, (_, i) => a + i)

// DEUDA: duplica src/simulacion/productos.py (COBERTURAS, fase 2), sin endpoint de calendario.
// Si cambia allí, cambia aquí; lo ideal es servirlo desde la API.
export const CALENDARIO: Record<string, Producto> = {
  smap_l3: { nombre: 'SMAP L3', inicio: id(2015, 3), fin: N_MESES - 1, parciales: [id(2019, 6), id(2019, 7), id(2022, 8), id(2022, 9)] },
  grace: {
    nombre: 'GRACE / GRACE-FO', inicio: id(2002, 4), fin: id(2026, 8),
    huecos: [
      [2002, 6], [2002, 7], [2003, 6], [2011, 1], [2011, 6], [2012, 5], [2012, 10], [2013, 3], [2013, 8], [2013, 9],
      [2014, 2], [2014, 7], [2014, 12], [2015, 6], [2015, 10], [2015, 11], [2016, 4], [2016, 9], [2016, 10], [2017, 2],
      ...rango(7, 12).map((m) => [2017, m]), ...rango(1, 5).map((m) => [2018, m]), [2018, 8], [2018, 9],
    ].map(([a, m]) => id(a, m)),
  },
  power: { nombre: 'NASA POWER', inicio: 0, fin: N_MESES - 1 },
  merra2: { nombre: 'MERRA-2', inicio: 0, fin: id(2026, 9) },
  gldas: { get nombre() { return t('producto.gldas') }, inicio: 0, fin: id(2026, 7) },
  mod13: { nombre: 'MODIS MOD13', inicio: id(2000, 2), fin: id(2026, 10) },
  mod16: { nombre: 'MODIS MOD16', inicio: 0, fin: N_MESES - 1, provisionalDesde: id(2026, 1) },
  mod11: { nombre: 'MODIS MOD11', inicio: id(2000, 2), fin: N_MESES - 1 },
  imerg: { get nombre() { return t('producto.imerg') }, inicio: 0, fin: N_MESES - 1, provisionalDesde: id(2025, 10) },
}

/** Meses del eje 0..322 sin dato: fuera de [inicio, fin] o dentro de un hueco entero. */
export function mesesConHueco(p: Pick<Producto, 'inicio' | 'fin' | 'huecos'>): number[] {
  const h = new Set(p.huecos)
  return rango(0, N_MESES - 1).filter((m) => m < p.inicio || m > p.fin || h.has(m))
}
