// asistido por SI: Claude Code (Anthropic), escritura y revisión de código; base del prototipo migrada en el hackatón
// Índice de búsqueda y de unidades (generado junto con las teselas).
import { cargarIndice as cargarCrudo, type FilaIndice } from './busqueda'

export interface Unidad {
  id: number | string
  nivel: number
  nombre: string
  pais: string
  pais_id?: number | string
  bbox?: [number, number, number, number]
}

export const porClave = new Map<string, Unidad>()
export const claveUnidad = (nivel: number, id: number | string) => `${nivel}:${id}`

let cargado: Promise<FilaIndice[]> | null = null
/** Una sola descarga y un solo parseo: devuelve las filas crudas (el Worker arma MiniSearch con ellas) y llena porClave. */
export function cargarFilas(): Promise<FilaIndice[]> {
  cargado ??= cargarCrudo().then((filas) => {
    for (const x of filas) {
      if (x.nivel > 2) continue
      porClave.set(claveUnidad(x.nivel, x.id), { id: x.id, nivel: x.nivel, nombre: x.n, pais: x.ctx, pais_id: x.nivel ? x.id.split('.')[0] : x.id })
    }
    return filas
  })
  return cargado
}
export const cargarIndice = (): Promise<Unidad[]> => cargarFilas().then(() => [...porClave.values()])
