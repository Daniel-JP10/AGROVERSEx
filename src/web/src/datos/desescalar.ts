// asistido por SI: Claude Code (Anthropic), escritura y revisión de código; base del prototipo migrada en el hackatón
import { paraMostrar, type Mes } from '../comun/unidades'

export const SIN_DATO = -32768 // relleno del producto: nunca es un valor válido

export function desescalar(entero: number | null, escala: number, desplazamiento: number): number | null {
  if (entero === null || entero === SIN_DATO) return null
  return entero * escala + desplazamiento
}

// Nunca un número solo: siempre con su rango p05-p95 y su unidad.
export function formatearRango(p05: number, p50: number, p95: number, unidad: string): string {
  const f = (n: number) => n.toLocaleString('es', { maximumFractionDigits: 2 })
  return `${f(p50)} ${unidad} (rango ${f(p05)} a ${f(p95)} ${unidad})`
}

// La lluvia se guarda en mm/h (IMERG); la conversión a mm/mes es explícita y solo para mostrar.
export const mmHoraAMmMes = (mmh: number, mes: Mes) => paraMostrar('precip', mmh, 'mm/h', mes).valor as number
