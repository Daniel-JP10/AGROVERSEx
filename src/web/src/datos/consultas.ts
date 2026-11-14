// asistido por SI: Claude Code (Anthropic), escritura y revisión de código; base del prototipo migrada en el hackatón
import { useQuery, useQueryClient, type QueryClient } from '@tanstack/react-query'
import { crearCliente, type Cliente } from './cliente'
import type { Coropleta, Nivel } from './tipos'

const MAX_MESES = 48
export const clienteDefecto = crearCliente()

const clave = (nivel: Nivel, variable: string, mes: number) => ['coropleta', nivel, variable, mes] as const

export const opcionesCoropleta = (c: Cliente, nivel: Nivel, variable: string, mes: number) => ({
  queryKey: clave(nivel, variable, mes),
  queryFn: () => c.coropleta(nivel, variable, mes),
  staleTime: Infinity,
  gcTime: Infinity,
  retry: false, // el reintento ya lo hace el cliente
})

// Caché de hasta 48 meses por nivel y variable: se descartan los más lejanos al mes pedido.
function podar(qc: QueryClient, nivel: Nivel, variable: string, mes: number) {
  const q = qc.getQueryCache().findAll({ queryKey: ['coropleta', nivel, variable] })
  q.sort((a, b) => Math.abs((b.queryKey[3] as number) - mes) - Math.abs((a.queryKey[3] as number) - mes))
  q.slice(0, Math.max(0, q.length - MAX_MESES)).forEach((x) => qc.getQueryCache().remove(x))
}

// Último mes con datos buenos en caché, buscando hacia atrás desde el pedido.
export function ultimoMesBueno(qc: QueryClient, nivel: Nivel, variable: string, mes: number): Coropleta | undefined {
  for (let m = mes; m >= 0; m--) {
    const d = qc.getQueryData<Coropleta>(clave(nivel, variable, m))
    if (d) return d
  }
}

export async function cargarMes(qc: QueryClient, c: Cliente, nivel: Nivel, variable: string, mes: number) {
  const d = await qc.fetchQuery(opcionesCoropleta(c, nivel, variable, mes))
  podar(qc, nivel, variable, mes)
  return d
}

export async function precargarMeses(nivel: Nivel, variable: string, desde: number, hasta: number, qc: QueryClient, c: Cliente = clienteDefecto) {
  for (let m = desde; m <= hasta; m++) await cargarMes(qc, c, nivel, variable, m).catch(() => undefined)
}

// Si el mes pedido falla, `datos` sigue siendo el último mes bueno y `error` queda visible.
export function useCoropleta(nivel: Nivel, variable: string, mes: number, c: Cliente = clienteDefecto) {
  const qc = useQueryClient()
  const q = useQuery({ ...opcionesCoropleta(c, nivel, variable, mes), queryFn: () => cargarMes(qc, c, nivel, variable, mes) })
  const datos = q.data ?? ultimoMesBueno(qc, nivel, variable, mes)
  return { datos, mesMostrado: datos?.mes, error: q.isError ? q.error : null, cargando: q.isPending }
}
