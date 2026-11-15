// asistido por SI: Claude Code (Anthropic), trayectorias ficticias de ejemplo; solo se importa con VITE_EJEMPLOS=1
import { EJEMPLOS } from '../../ejemplos'
import type { Banda, Estrategia } from './tipos'

// Ficticio: formas suaves para probar el diseño, no un resultado del gemelo
const MESES = 36
const serie = (f: (m: number) => number, ancho: (m: number) => number, lo = -Infinity, hi = Infinity): Banda => {
  const tope = (v: number) => Math.min(hi, Math.max(lo, v))
  const p50 = Array.from({ length: MESES }, (_, m) => tope(f(m)))
  return { p10: p50.map((v, m) => tope(v - ancho(m))), p50, p90: p50.map((v, m) => tope(v + ancho(m))) }
}
const ciclo = (m: number, fase: number) => Math.sin(((m + fase) / 12) * 2 * Math.PI)
const estrategia = (nombre: string, a: number, fase: number): Estrategia => ({
  nombre,
  trayectoria_mensual: {
    W: serie((m) => 160 + 40 * ciclo(m, fase), (m) => 12 + m / 6),
    N: serie((m) => 60 + 25 * ciclo(m, fase + 3) + a * m, (m) => 6 + m / 8),
    C: serie((m) => 40 + a * m / 4, (m) => 1 + m / 20),
    B: serie((m) => 2500 + 2000 * Math.max(0, ciclo(m, fase + 6)), (m) => 300 + m * 5),
    V: serie((m) => 0.5 + 0.35 * ciclo(m, fase + 6) * (a > 0 ? 0.6 : 1) + (a > 0 ? 0.15 : 0), () => 0.08, 0, 1),
    desnudo: serie((m) => (a > 0 ? 0.25 : 0.5) - 0.45 * ciclo(m, fase + 6), () => 0.12, 0, 1),
  },
})

export const ESTRATEGIAS_EJEMPLO = [estrategia('Ejemplo A', 0, 0), estrategia('Ejemplo B', 0.3, 0)] as const
// Referencia para que la compilación pública lo deje fuera junto con los ejemplos
export const MARCA = EJEMPLOS.marcador
