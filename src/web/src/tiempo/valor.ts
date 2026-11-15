// asistido por SI: Claude Code (Anthropic), escritura y revisión de código; base del prototipo migrada en el hackatón
// Valor PLACEHOLDER SIMULADO para la coropleta de prueba. No es dato real:
// se reemplaza por /api/coropleta cuando exista la simulación de la fase 2.

// El eje temporal sale de meta.json (lo escribe src/mapa_estatico/construir.py): ni el inicio ni el fin van a mano
import meta from '../../public/datos/meta.json'

const [ANIO0, MES0] = meta.mes0.split('-').map(Number)
export const MES_INICIO = { anio: ANIO0, mes: MES0 }

/** 'AAAA-MM' -> índice desde mes0 del eje (0 = mes0) */
export const idDeMes = (aaaamm: string): number => (Number(aaaamm.slice(0, 4)) - ANIO0) * 12 + Number(aaaamm.slice(5, 7)) - MES0

/** Meses del eje: hasta el último mes con producto de alguna variable (los archivos traen un mes más, siempre vacío) */
export const N_MESES = 1 + Math.max(...Object.values(meta.variables).map((v) => idDeMes(v.meses_disponibles.hasta)))

/** Hash FNV-1a de un id (texto o número) a [0, 1). */
export function hash01(id: string | number): number {
  let h = 0x811c9dc5
  for (const ch of String(id)) {
    h ^= ch.charCodeAt(0)
    h = Math.imul(h, 0x01000193)
  }
  return (h >>> 0) / 4294967296
}

/** Valor 0..1 determinista por id y mes (índice 0 = 2000-01). */
export function valorSimulado(id: string | number, mes: number): number {
  const base = hash01(id)
  const fase = hash01(`${id}:f`) * 2 * Math.PI
  const v = 0.5 + 0.5 * (base - 0.5) + 0.22 * Math.sin((2 * Math.PI * mes) / 12 + fase) + 0.12 * Math.sin((2 * Math.PI * mes) / (60 + 40 * base) + fase)
  return Math.min(1, Math.max(0, v))
}

/** Incertidumbre simulada fija (±), para mostrar siempre un rango junto al valor. */
export const MARGEN_SIMULADO = 0.08

export function etiquetaMes(mes: number): string {
  const total = MES_INICIO.anio * 12 + (MES_INICIO.mes - 1) + mes
  return `${Math.floor(total / 12)}-${String((total % 12) + 1).padStart(2, '0')}`
}
