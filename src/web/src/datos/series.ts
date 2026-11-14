// asistido por SI: Claude Code (Anthropic), escritura y revisión de código; base del prototipo migrada en el hackatón
import type { Fetcher } from './cliente'
import { t } from '../textos/i18n'
import type { ClaveTexto } from '../textos/es'
import { paraMostrar, type Mes } from '../comun/unidades'

export type Num = number | null

export interface SerieVar {
  valor: Num[]; bandera: number[]; p10?: Num[]; p90?: Num[]
  unidad_medida: string | null; rango: [number | null, number | null]; etiqueta: string | null; nivel_dato: string | null
}
export interface RespSerie { meses: number[]; series: Record<string, SerieVar> }

// Cliente de /api/serie/:id (Task 4); con fetcher inyectable para fixtures. Un reintento y luego sube el error.
export async function pedirSerie(id: string, vars: string[], desde = 0, hasta = 322, f: Fetcher = (u) => fetch(u)): Promise<RespSerie> {
  const url = `/api/serie/${encodeURIComponent(id)}?vars=${vars.map(encodeURIComponent).join(',')}&desde=${desde}&hasta=${hasta}`
  for (let i = 0; ; i++) {
    try {
      const r = await f(url)
      if (!r.ok) throw new Error(`${url}: HTTP ${r.status}`)
      return await r.json()
    } catch (e) { if (i >= 1) throw e }
  }
}

// Lluvia (unidad del producto, por omisión mm/h) -> mm/mes del mes dado (la conversión vive en comun/unidades.ts)
export const mmPorMes = (v: number, mes: Mes, unidad = 'mm/h') => paraMostrar('precip', v, unidad, mes).valor as number

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
  precip: 'capa.precipCorta', t2m: 'capa.t2m', ndvi: 'capa.ndvi', sm_sup: 'capa.sm_sup', sm_raiz: 'capa.sm_raiz',
  tws: 'capa.twsCorta', rad_sw: 'capa.rad_sw', rh2m: 'capa.rh2m', et: 'capa.et', lst_dia: 'capa.lst_dia',
}
export const nombreVar = (v: string) => (CLAVE_VAR[v] ? t(CLAVE_VAR[v]) : v)

