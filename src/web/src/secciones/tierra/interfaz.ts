// asistido por SI: Claude Code (Anthropic), interfaz del globo para el resto del universo (contrato web_componentes §4)
import { useEstado } from '../../app/estado'
import { porClave } from '../../datos/indice'
import { capaPorId } from '../../datos/capas'
import { MES_INICIO } from '../../tiempo/valor'

const FORMATO_UNIDAD = /^([A-Z0-9]{3})-ADM(?:0|([12])-[A-Za-z0-9]+)$/

/**
 * unidad_id (contratos/unidades.md) -> clave interna `nivel:id` del globo.
 * Las teselas CGAZ de T-D1 usan unidad_id como id de entidad (promoteId) y el índice de búsqueda trae los mismos ids:
 * la clave interna es nivel:unidad_id, sin tabla de traducción.
 */
export function claveDeUnidadId(unidadId: string): string {
  const m = FORMATO_UNIDAD.exec(unidadId)
  if (!m) throw new Error(`unidad_id inválido: ${unidadId}`)
  return `${m[2] ?? '0'}:${unidadId}`
}

/** Selecciona la unidad y el globo vuela a ella; devuelve false si el índice no la tiene. */
export function irAUnidad(unidadId: string): boolean {
  const u = porClave.get(claveDeUnidadId(unidadId))
  if (!u) return false
  useEstado.getState().seleccionar(u)
  return true
}

export function cambiarVariable(id: string): void {
  useEstado.getState().setCapa(capaPorId(id).id)
}

/** mes 'AAAA-MM' en UTC -> índice desde 2000-01 */
export function cambiarMes(mes: string): void {
  const m = /^(\d{4})-(0[1-9]|1[0-2])$/.exec(mes)
  if (!m) throw new Error(`mes inválido (se espera AAAA-MM): ${mes}`)
  useEstado.getState().setMes((Number(m[1]) - MES_INICIO.anio) * 12 + Number(m[2]) - MES_INICIO.mes)
}

export const activarComparador = (activo: boolean): void => useEstado.getState().activarComparador(activo)

export const abrirPestana = (nombre: string): void => useEstado.getState().abrirPestana(nombre)

/** fn recibe el unidad_id seleccionado o null; devuelve la baja. */
export function alSeleccionar(fn: (unidadId: string | null) => void): () => void {
  return useEstado.subscribe((s, previo) => {
    if (s.seleccion !== previo.seleccion) fn(s.seleccion ? String(s.seleccion.id) : null)
  })
}
