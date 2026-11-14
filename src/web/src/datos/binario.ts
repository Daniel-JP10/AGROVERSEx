// asistido por SI: Claude Code (Anthropic), escritura y revisión de código; base del prototipo migrada en el hackatón
import { desescalar } from './desescalar'

// Int16 little-endian; -32768 (sin dato) pasa a NaN.
export function decodificarCoropleta(buf: ArrayBuffer, escala: number, desplazamiento: number): Float32Array {
  const dv = new DataView(buf)
  const out = new Float32Array(buf.byteLength >> 1)
  for (let i = 0; i < out.length; i++) out[i] = desescalar(dv.getInt16(2 * i, true), escala, desplazamiento) ?? NaN
  return out
}
