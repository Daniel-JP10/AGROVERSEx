// asistido por SI: Claude Code (Anthropic), escritura y revisión de código; base del prototipo migrada en el hackatón
import { N_MESES, idDeMes } from './valor'
import meta from '../../public/datos/meta.json'
import type { Matriz } from '../datos/estatico'

const MESES = ['ene', 'feb', 'mar', 'abr', 'may', 'jun', 'jul', 'ago', 'sep', 'oct', 'nov', 'dic']
export const mesIdAEtiqueta = (mes: number) => `${MESES[mes % 12]}-${2000 + Math.floor(mes / 12)}`

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

// Disponibilidad de un producto con archivo estático: sale de meta.json (y coincide con manifiesto.json, ver pruebas/tierra_disponibilidad.test.ts)
const disponible = (v: keyof typeof meta.variables) => ({ inicio: idDeMes(meta.variables[v].meses_disponibles.desde), fin: idDeMes(meta.variables[v].meses_disponibles.hasta) })

/** Primer mes cuyo producto es provisional, leído de la propia matriz (producto_mes); undefined si no hay ninguno */
export function provisionalDesdeDe(m: Pick<Matriz, 'productos' | 'producto_mes'>): number | undefined {
  const i = m.producto_mes.findIndex((p) => p >= 0 && m.productos[p].estado === 'provisional')
  return i < 0 ? undefined : i
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
  merra2: { nombre: 'MERRA-2', ...disponible('t2m') },
  gldas: { nombre: 'GLDAS Noah (modelo)', ...disponible('sm_raiz') },
  mod13: { nombre: 'MODIS MOD13', ...disponible('ndvi') },
  mod16: { nombre: 'MODIS MOD16', inicio: 0, fin: N_MESES - 1, provisionalDesde: id(2026, 1) },
  mod11: { nombre: 'MODIS MOD11', inicio: id(2000, 2), fin: N_MESES - 1 },
  imerg: { nombre: 'IMERG (Final y Late provisional)', ...disponible('precip') }, // provisionalDesde: provisionalDesdeDe(matriz)
}

/** Meses del eje sin dato: fuera de [inicio, fin] o dentro de un hueco entero. */
export function mesesConHueco(p: Pick<Producto, 'inicio' | 'fin' | 'huecos'>): number[] {
  const h = new Set(p.huecos)
  return rango(0, N_MESES - 1).filter((m) => m < p.inicio || m > p.fin || h.has(m))
}
