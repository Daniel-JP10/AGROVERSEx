// asistido por SI: Claude Code (Anthropic), aplica unidad, variable y mes de #/tierra?... al globo (contrato web_componentes §3, D-037 C2)
import { CAPAS } from '../../datos/capas'
import { cargarFilas } from '../../datos/indice'
import { cambiarMes, cambiarVariable, irAUnidad } from './interfaz'

const MES = /^\d{4}-(0[1-9]|1[0-2])$/

/** Cada parámetro válido se aplica; uno inválido se ignora sin tocar los demás. Devuelve false si la unidad no existe. */
export async function aplicarParams(p: Record<string, string>): Promise<boolean> {
  if (p.variable && CAPAS.some((c) => c.id === p.variable)) cambiarVariable(p.variable)
  if (p.mes && MES.test(p.mes)) cambiarMes(p.mes)
  if (!p.unidad) return true
  await cargarFilas() // sin servidor el índice es un archivo estático: la unidad existe cuando llega
  try { return irAUnidad(p.unidad) } catch { return false } // unidad_id con formato inválido
}
