// asistido por SI: Claude Code (Anthropic), conversión única de unidades para mostrar (contrato web_componentes §5)
// Los datos guardan la unidad del producto (IMERG, mm/hr); la conversión es solo para mostrar.
import { MES_INICIO } from '../tiempo/valor'

/** mes: 'AAAA-MM' (UTC) o índice desde 2000-01 */
export type Mes = string | number

/** Días reales del mes en UTC, con febrero bisiesto. Lanza si el mes no es válido. */
export function diasDelMes(mes: Mes): number {
  let anio: number, m: number
  if (typeof mes === 'number' && Number.isInteger(mes) && mes >= 0) {
    const total = MES_INICIO.anio * 12 + (MES_INICIO.mes - 1) + mes
    anio = Math.floor(total / 12); m = (total % 12) + 1
  } else {
    const r = typeof mes === 'string' ? /^(\d{4})-(0[1-9]|1[0-2])$/.exec(mes) : null
    if (!r) throw new Error(`mes inválido: ${String(mes)}`)
    anio = Number(r[1]); m = Number(r[2])
  }
  return new Date(Date.UTC(anio, m, 0)).getUTCDate()
}

type Conv = (v: number, dias: number) => { valor: number; unidad: string }
const id: (u: string) => Conv = (u) => (v) => ({ valor: v, unidad: u })
const mmHora: Conv = (v, d) => ({ valor: v * 24 * d, unidad: 'mm/mes' })
const mmDia: Conv = (v, d) => ({ valor: v * d, unidad: 'mm/mes' })
const kC: Conv = (v) => ({ valor: v - 273.15, unidad: '°C' })

// Un caso explícito por cada par (variable, unidad): los de serie_mensual (contratos/serie_mensual.md) y los de la base del prototipo.
// Un par ausente lanza error; nunca se devuelve el valor tal cual.
const CONV: Record<string, Record<string, Conv>> = {
  precip: { 'mm/h': mmHora, 'mm/hr': mmHora, 'mm/day': mmDia, 'mm/d': mmDia, 'mm/dia': mmDia, 'mm/día': mmDia },
  t2m: { K: kC, C: id('°C') },
  t2m_p10: { C: id('°C') }, t2m_p90: { C: id('°C') },
  sm_raiz: { 'kg m-2': id('kg/m²') }, // GLDAS (modelo), sin conversión (el contrato no pide otra)
  ndvi: { '1': id('adimensional'), adim: id('adimensional') },
  nbr2: { adim: id('adimensional') },
  sm_verdad: { 'm3/m3': id('m³/m³') },
}
const ALIAS: Record<string, string> = { precipitacion: 'precip', humedad_radicular: 'sm_raiz' }

export function paraMostrar(variable: string, valor: number | null | undefined, unidadProducto: string | null, mes: Mes): { valor: number | null; unidad: string } {
  const dias = diasDelMes(mes) // valida el mes aunque no haga falta
  const v = valor ?? null
  const f = CONV[ALIAS[variable] ?? variable]?.[unidadProducto ?? '']
  if (!f) throw new Error(`sin conversión para (variable=${variable}, unidad=${unidadProducto})`)
  return { valor: v === null ? null : f(v, dias).valor, unidad: f(0, dias).unidad }
}
