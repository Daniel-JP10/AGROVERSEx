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

const MM_HORA = new Set(['mm/h', 'mm/hr'])

export function paraMostrar(variable: string, valor: number | null | undefined, unidadProducto: string | null, mes: Mes): { valor: number | null; unidad: string } {
  const dias = diasDelMes(mes) // valida el mes aunque no haga falta
  const v = valor ?? null
  if (variable === 'precip' && unidadProducto && MM_HORA.has(unidadProducto)) return { valor: v === null ? null : v * 24 * dias, unidad: 'mm/mes' }
  const u = unidadProducto === 'C' ? '°C' : unidadProducto === 'adim' || !unidadProducto ? (variable === 'ndvi' || unidadProducto === 'adim' ? 'adimensional' : '') : unidadProducto
  return { valor: v, unidad: u }
}
