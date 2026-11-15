// asistido por SI: Claude Code (Anthropic), escritura y revisión de código; base del prototipo migrada en el hackatón
// Construye el buscador fuera del hilo principal (54 mil filas); las filas llegan ya descargadas.
import { crearBuscador, type FilaIndice } from './busqueda'

let buscador: ReturnType<typeof crearBuscador> | null = null
const pendientes: { rid: number; texto: string }[] = []
const responder = (m: { rid: number; texto: string }) => self.postMessage({ rid: m.rid, res: buscador!.buscar(m.texto) })
self.onmessage = (e: MessageEvent<{ filas: FilaIndice[] } | { rid: number; texto: string }>) => {
  if ('filas' in e.data) { buscador = crearBuscador(e.data.filas); pendientes.splice(0).forEach(responder) }
  else if (buscador) responder(e.data)
  else pendientes.push(e.data)
}
