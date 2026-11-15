// asistido por SI: Claude Code (Anthropic), escritura y revisión de código; base del prototipo migrada en el hackatón; serie por país del mundo (S1w)
import { cargarMatriz, iso3DeUnidad, nivelDeUnidad, type ProductoMes } from './estatico'
import { N_MESES } from '../tiempo/valor'
import { t } from '../textos/i18n'
import type { ClaveTexto } from '../textos/es'
import { paraMostrar, type Mes } from '../comun/unidades'

export type Num = number | null

export interface SerieVar {
  valor: Num[]; p10: Num[]; p90: Num[]; frac: Num[]
  /** Unidad del producto de cada mes (null = mes sin producto); IMERG cambia de mm/hr a mm/day en 2025-10 */
  unidad_mes: (string | null)[]
  productos: ProductoMes[]; producto_mes: number[]
}
export interface RespSerie { meses: number[]; series: Record<string, SerieVar> }

// Serie de una unidad desde los archivos estáticos (datos/estatico.ts); valores en la unidad del producto, sin convertir.
export async function pedirSerie(id: string, vars: string[], desde = 0, hasta = N_MESES - 1): Promise<RespSerie> {
  const meses = Array.from({ length: hasta - desde + 1 }, (_, i) => desde + i)
  const series: Record<string, SerieVar> = {}
  for (const v of vars) {
    const m = await cargarMatriz(v, nivelDeUnidad(id), iso3DeUnidad(id))
    const r = m.ids.indexOf(id)
    if (r < 0) throw new Error(`sin dato real para ${id}`)
    const cut = (a: Num[][]) => meses.map((k) => a[r][k] ?? null)
    series[v] = {
      valor: cut(m.valor), p10: cut(m.p10), p90: cut(m.p90), frac: cut(m.frac), productos: m.productos,
      producto_mes: meses.map((k) => m.producto_mes[k] ?? -1),
      unidad_mes: meses.map((k) => (m.producto_mes[k] >= 0 ? m.productos[m.producto_mes[k]].unidad : null)),
    }
  }
  return { meses, series }
}

// Lluvia (unidad del producto, obligatoria) -> mm/mes del mes dado (la conversión vive en comun/unidades.ts)
export const mmPorMes = (v: number, mes: Mes, unidad: string) => paraMostrar('precip', v, unidad, mes).valor as number

// Resta la media de la base [baseDesde, baseHasta] (índices incluidos), ignorando null.
export function anomalia(s: Num[], baseDesde: number, baseHasta: number): Num[] {
  const b = s.slice(baseDesde, baseHasta + 1).filter((x): x is number => x !== null)
  if (!b.length) return s.map(() => null)
  const m = b.reduce((a, x) => a + x, 0) / b.length
  return s.map((x) => (x === null ? null : x - m))
}

// Mínimos cuadrados sobre los puntos con dato; IC ~95% (z=1,96, shortcut: sin t de Student, válido con n grande).
export function tendencia(s: Num[]): { pendiente: number; ic: [number, number] } {
  const p = s.map((y, x) => [x, y] as const).filter((q): q is [number, number] => q[1] !== null)
  const n = p.length
  if (n < 3) return { pendiente: NaN, ic: [NaN, NaN] }
  const mx = p.reduce((a, q) => a + q[0], 0) / n, my = p.reduce((a, q) => a + q[1], 0) / n
  const sxx = p.reduce((a, q) => a + (q[0] - mx) ** 2, 0)
  const pend = p.reduce((a, q) => a + (q[0] - mx) * (q[1] - my), 0) / sxx
  const sse = p.reduce((a, q) => a + (q[1] - my - pend * (q[0] - mx)) ** 2, 0)
  const se = Math.sqrt(sse / (n - 2) / sxx)
  return { pendiente: pend, ic: [pend - 1.96 * se, pend + 1.96 * se] }
}

// Tramos continuos sin null: nunca cruzan un hueco.
export function segmentar(s: Num[]): { desde: number; valores: number[] }[] {
  const out: { desde: number; valores: number[] }[] = []
  s.forEach((x, i) => {
    if (x === null) return
    const u = out[out.length - 1]
    if (u && u.desde + u.valores.length === i) u.valores.push(x)
    else out.push({ desde: i, valores: [x] })
  })
  return out
}

const CLAVE_VAR: Record<string, ClaveTexto> = {
  precip: 'capa.precipCorta', t2m: 'capa.t2m', ndvi: 'capa.ndvi', sm_raiz: 'capa.sm_raiz',
}
export const nombreVar = (v: string) => (CLAVE_VAR[v] ? t(CLAVE_VAR[v]) : v)

