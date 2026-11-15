// asistido por SI: Claude Code (Anthropic), escritura y revisión de código; base del prototipo migrada en el hackatón
import type { Map as MapaGL } from 'maplibre-gl'
import { registrarPatron } from './patron'
import { t } from '../textos/i18n'

// Motor de datos de la coropleta. El pintado por rebanadas, la cola durante gestos y el límite
// de niveles viven en recoloreo.ts (D-015, medido en la PoC); este motor solo calcula el estado
// por unidad y se lo entrega a recoloreo.

// ocultas: ids filtrados por atributos (Task 14); se ven apagados, nunca como hueco.
export interface FiltroUnidad { min?: number; max?: number; fraccionMin?: number; ocultas?: Set<string> }
/** v: 0..1 para el color; ok: pintar con color; hueco: pintar con trama (sin dato del producto). */
// Unidad sin valor en la base: se pinta la trama "sin dato" en vez de quedar en blanco
export const SIN_DATO = { v: 0, ok: false, hueco: true, valor: NaN }

/** p10 y p90 son la dispersión entre celdas de la unidad (tipo_rango espacial), en la unidad de pantalla; frac es frac_valida */
// Unidad sin dato real (fuera de Colombia): ni color ni trama; el tooltip dice "sin dato real todavía"
export const SIN_DATO_REAL = { v: 0, ok: false, hueco: false, valor: NaN }

export interface EstadoUnidad { v: number; ok: boolean; hueco: boolean; valor: number; p10?: number; p90?: number; frac?: number }
export interface Extra { p10?: number; p90?: number }

export const OPACIDAD_DEFECTO = 62
const CLAVE_OPACIDAD = 'agroversex.coropleta.opacidad'

export function estadoUnidad(valor: number, fraccion: number | undefined, rango: [number, number], f: FiltroUnidad, id?: string, extra: Extra = {}): EstadoUnidad {
  if (!Number.isFinite(valor)) return { v: 0, ok: false, hueco: true, valor: NaN, frac: fraccion }
  const [a, b] = rango
  const v = Math.min(1, Math.max(0, (valor - a) / (b - a)))
  const fuera = (id !== undefined && !!f.ocultas?.has(id)) || (f.min !== undefined && valor < f.min) || (f.max !== undefined && valor > f.max) ||
    (f.fraccionMin !== undefined && fraccion !== undefined && !(fraccion >= f.fraccionMin))
  return { v, ok: !fuera, hueco: false, valor, frac: fraccion, ...extra }
}

export function partirEnRebanadas<T>(items: T[], n: number): T[][] {
  const r: T[][] = []
  for (let i = 0; i < items.length; i += n) r.push(items.slice(i, i + n))
  return r
}

export interface MotorCoropleta {
  readonly nivel: number
  aplicar(valores: Float32Array, ids: string[], filtro: FiltroUnidad, fracciones?: Float32Array, rangos?: { p10: Float32Array; p90: Float32Array }): void
  estado(id: string): EstadoUnidad | undefined
  destruir(): void
}

export function crearMotorCoropleta(map: Pick<MapaGL, 'hasImage' | 'addImage'>, opts: { nivel: number; rango: [number, number]; alCambiar?: () => void }): MotorCoropleta {
  registrarPatron(map)
  let estados = new Map<string, EstadoUnidad>()
  return {
    nivel: opts.nivel,
    aplicar(valores, ids, filtro, fracciones, rangos) {
      const n = new Map<string, EstadoUnidad>()
      ids.forEach((id, i) => n.set(id, estadoUnidad(valores[i], fracciones?.[i], opts.rango, filtro, id, rangos ? { p10: rangos.p10[i], p90: rangos.p90[i] } : {})))
      estados = n
      opts.alCambiar?.()
    },
    estado: (id) => estados.get(id),
    destruir() { estados = new Map() },
  }
}

const f2 = (n: number) => n.toLocaleString('es', { maximumFractionDigits: 1 })
// Nunca un número solo: valor + unidad + rango p10 a p90 entre celdas si el dato lo trae; si no, el rango de la escala
export function textoValor(e: EstadoUnidad | undefined, unidad: string, rango: [number, number]): string {
  if (!e) return t('globo.sinCargados')
  if (e.hueco) return t('globo.sinDatoProducto')
  const dispersion = Number.isFinite(e.p10) && Number.isFinite(e.p90)
  const txt = dispersion
    ? `${f2(e.valor)} ${unidad} (${t('globo.rangoCeldas')} ${f2(e.p10!)} ${t('series.a')} ${f2(e.p90!)} ${unidad})`
    : `${f2(e.valor)} ${unidad} (${t('globo.rangoEscala')} ${f2(rango[0])} ${t('series.a')} ${f2(rango[1])} ${unidad})`
  return e.ok ? txt : `${txt} · ${t('globo.fueraFiltro')}`
}

export const opacidadValida = (n: number) => (Number.isFinite(n) ? Math.min(100, Math.max(0, Math.round(n))) : OPACIDAD_DEFECTO)
export function leerOpacidad(s: Pick<Storage, 'getItem'> = localStorage): number {
  try { const v = s.getItem(CLAVE_OPACIDAD); return v === null ? OPACIDAD_DEFECTO : opacidadValida(Number(v)) } catch { return OPACIDAD_DEFECTO }
}
export function guardarOpacidad(n: number, s: Pick<Storage, 'setItem'> = localStorage) {
  try { s.setItem(CLAVE_OPACIDAD, String(n)) } catch { /* sin almacenamiento: solo dura la sesión */ }
}
