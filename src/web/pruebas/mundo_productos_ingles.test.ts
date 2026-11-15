// asistido por SI: Claude Code (Anthropic), los nombres de producto que ve el usuario van en inglés (H-F3-1, S1w)
import { existsSync, readFileSync } from 'node:fs'
import { join } from 'node:path'
import { describe, expect, it } from 'vitest'

// Tildes o palabras sueltas en español (la misma regla que ESPANOL en construir.py)
const ESPANOL = /[áéíóúñÁÉÍÓÚÑ]|\b(mensual|diario|agregado|grados|rean[aá]lisis|superficie|terrestre|modelo|mes|en)\b/i
const productos = (ruta: string): string[] =>
  Object.values(JSON.parse(readFileSync(ruta, 'utf-8')).variables as Record<string, { productos: { producto: string }[] }>).flatMap((v) => v.productos.map((p) => p.producto))

describe('productos en inglés', () => {
  it('la regla detecta los nombres viejos', () => {
    expect(ESPANOL.test('GPM IMERG Late Run, diario agregado a mes en UTC (GPM_3IMERGDL)')).toBe(true)
    expect(ESPANOL.test('MERRA-2 reanálisis, M2TMNXSLV (T2M)')).toBe(true)
  })
  // public siempre; dist solo con PROHIBIDOS_DIST, como las demás pruebas sobre el build (un dist sin desplegar todavía trae los nombres viejos)
  const carpetas = [join(__dirname, '..', 'public', 'datos'), ...(process.env.PROHIBIDOS_DIST ? [join(process.env.PROHIBIDOS_DIST, 'datos')] : [])]
  for (const c of carpetas) for (const n of ['meta.json', 'manifiesto.json']) {
    const ruta = join(c, n)
    it.runIf(existsSync(ruta))(`${ruta.split(/[\\/]/).slice(-3).join('/')} sin español`, () => {
      const ps = productos(ruta)
      expect(ps.length).toBeGreaterThan(0)
      for (const p of ps) expect(p).not.toMatch(ESPANOL)
    })
  }
})
