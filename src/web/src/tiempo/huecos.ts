// asistido por SI: Claude Code (Anthropic), escritura y revisión de código; base del prototipo migrada en el hackatón
import { t } from '../textos/i18n'
import type { ClaveTexto } from '../textos/en'
import { MES_INICIO, N_MESES, idDeMes } from './valor'
import meta from '../../public/datos/meta.json'
import type { Matriz } from '../datos/estatico'

// el año sale de meta.mes0 (MES_INICIO), no de una cifra escrita a mano
export const mesIdAEtiqueta = (mes: number) => { const k = MES_INICIO.mes - 1 + mes; return `${t(`mes.corto.${(k % 12) + 1}` as ClaveTexto)}-${MES_INICIO.anio + Math.floor(k / 12)}` }

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

const rango = (a: number, b: number) => Array.from({ length: b - a + 1 }, (_, i) => a + i)

// Solo productos con archivo estático y meta (director, 08:55): lo disponible es lo del manifiesto y meta.json
export const CALENDARIO: Record<string, Producto> = {
  merra2: { nombre: 'MERRA-2', ...disponible('t2m') },
  gldas: { get nombre() { return t('producto.gldas') }, ...disponible('sm_raiz') },
  mod13: { nombre: 'MODIS MOD13', ...disponible('ndvi') },
  imerg: { get nombre() { return t('producto.imerg') }, ...disponible('precip') }, // provisionalDesde: provisionalDesdeDe(matriz)
}

/** Meses del eje sin dato: fuera de [inicio, fin] o dentro de un hueco entero. */
export function mesesConHueco(p: Pick<Producto, 'inicio' | 'fin' | 'huecos'>): number[] {
  const h = new Set(p.huecos)
  return rango(0, N_MESES - 1).filter((m) => m < p.inicio || m > p.fin || h.has(m))
}
