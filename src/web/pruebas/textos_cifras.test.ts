// asistido por SI: Claude Code (Anthropic), prueba O1: ninguna cifra de datos escrita a mano en los textos visibles; salen de huecos {…}
import { readFileSync } from 'node:fs'
import { describe, expect, it } from 'vitest'
import { areaKm2 } from '../src/herramientas/geodesia'
import { resumen } from '../src/herramientas/Medir'
import { tendencia } from '../src/datos/series'
import { cifra, conCifras } from '../src/textos/cifras'
import { en } from '../src/textos/en'
import { es } from '../src/textos/es'

// Excepciones: definiciones fijas del método, cada una atada por una prueba de este archivo al valor que usa el código o el dato (D-039.3)
const PERMITIDOS: Record<string, string[]> = {
  'capa.t2m': ['2'], // altura del producto: la variable t2m (temperatura a 2 m)
  'medir.anillo': ['3'], 'medir.min2': ['2'], 'medir.min3': ['3'], // puntos mínimos que exige la herramienta
  'series.ic': ['95'], // nivel del intervalo: z = 1,96 de datos/series.ts
  ...Object.fromEntries(['arcilla', 'arena', 'carbono', 'cic', 'densidad', 'limo', 'nitrogeno', 'ph'].map((k) => [`suelo.${k}`, ['0-30']])), // capa 0-30 cm de SoilGrids
}
// Identificadores y nombres de producto (D-001, FAO-56, Sentinel-2) no cuentan como cifras
const SIN_NOMBRES = /\b[A-Za-z]+-\d+\b/g
const NUMEROS = /(?<![\w])\d+(?:[.,:\-–]\d+)*(?!\w)/g

export function cifrasSueltas(textos: Record<string, string | undefined>): string[] {
  const malas: string[] = []
  for (const [k, v] of Object.entries(textos)) {
    const limpio = (v ?? '').replace(/\{\w+\}/g, ' ').replace(SIN_NOMBRES, ' ')
    for (const n of limpio.match(NUMEROS) ?? []) if (!(PERMITIDOS[k] ?? []).includes(n)) malas.push(`${k}: ${n}`)
  }
  return malas
}

describe('cifras de datos en los textos', () => {
  it('el detector marca años, decimales y fechas, y deja pasar identificadores y huecos', () => {
    expect(cifrasSueltas({ a: 'serie 2000-2026', b: 'menor de 0.5', c: 'menor de 0,5', d: 'desde 2000-01-01', e: 'mes 2015-12' })).toHaveLength(5)
    expect(cifrasSueltas({ a: 'ver D-001, FAO-56 y Sentinel-2 en {anios_serie}', b: 'p10 a p90, 2D' })).toEqual([])
  })
  it('en.ts y es.ts no traen ninguna cifra de datos escrita a mano', () => {
    expect(cifrasSueltas(en)).toEqual([])
    expect(cifrasSueltas(es)).toEqual([])
  })
  it('las excepciones reconocidas siguen existiendo (si una clave cambia, se revisa la lista)', () => {
    for (const [k, tokens] of Object.entries(PERMITIDOS)) for (const tk of tokens) expect(en[k as keyof typeof en], k).toContain(tk)
  })
  it('cada hueco de cifra usado en los textos tiene valor y se sustituye en los dos idiomas', () => {
    const nombres = new Set(Object.values({ ...en, ...es }).flatMap((v) => [...String(v).matchAll(/\{(\w+)\}/g)].map((m) => m[1])))
    for (const n of ['anios_serie', 'anios_base', 'fecha_inicio_serie', 'fraccion_minima', 'error_esfera', 'fondo_fecha']) {
      expect(nombres.has(n), n).toBe(true)
      for (const l of ['en', 'es']) expect(cifra(n, l), `${n} ${l}`).toBeTruthy()
    }
    expect(conCifras('menor de {fraccion_minima}', 'es')).toBe('menor de 0,5')
    expect(conCifras('menor de {fraccion_minima}', 'en')).toBe('menor de 0.5')
    expect(conCifras('{recorrido_otro} {anios_serie}', 'en')).toMatch(/^\{recorrido_otro\} \d{4}-\d{4}$/)
  })
  it('los años de la serie salen de los mismos archivos de datos: coinciden con meta.json', () => {
    const meta = JSON.parse(readFileSync(new URL('../public/datos/meta.json', import.meta.url), 'utf8')) as { mes0: string; n_meses: number; variables: Record<string, { meses_disponibles?: { desde: string; hasta: string } }> }
    const m = Object.values(meta.variables).flatMap((v) => (v.meses_disponibles ? [v.meses_disponibles.desde, v.meses_disponibles.hasta] : [])).map((x) => Number(x.slice(0, 4)))
    expect(cifra('fecha_inicio_serie', 'en')).toBe(`${meta.mes0}-01`)
    const [a0, m0] = meta.mes0.split('-').map(Number)
    expect(cifra('anios_serie', 'en')).toBe(`${a0}-${a0 + Math.floor((m0 - 1 + meta.n_meses - 1) / 12)}`)
    expect(cifra('anios_serie', 'en')).toBe(`${Math.min(...m)}-${Math.max(...m)}`)
  })
})

// Pruebas que atan cada excepción al valor del código o del dato
describe('excepciones atadas a su fuente', () => {
  const unico = (txt: string) => txt.match(/\d[\d-]*/g)!.join(',')
  it('95 % es el nivel del intervalo que calcula tendencia(): su z = 1,96 deja 95 % de la normal', () => {
    const y = [1, 3, 2, 5, 4, 7, 6, 9, 8, 12, 10, 13]
    const { pendiente, ic } = tendencia(y)
    const n = y.length, xm = (n - 1) / 2, ym = y.reduce((a, b) => a + b) / n
    const sxx = y.reduce((a, _, i) => a + (i - xm) ** 2, 0)
    const rss = y.reduce((a, v, i) => a + (v - ym - pendiente * (i - xm)) ** 2, 0)
    const se = Math.sqrt(rss / (n - 2) / sxx)
    const z = (ic[1] - pendiente) / se
    expect(z).toBeCloseTo(1.96, 2)
    const cobertura = (zz: number) => { let s = 0; for (let t = 0; t < 1; t += 1e-5) s += Math.exp(-((t * zz) ** 2) / 2) * zz * 1e-5; return 2 * s / Math.sqrt(2 * Math.PI) }
    expect(Math.round(cobertura(z) * 100)).toBe(Number(unico(en['series.ic'])))
    expect(unico(es['series.ic']!)).toBe(unico(en['series.ic']))
  })
  it('0-30 cm es la capa que declaran los parámetros de suelo y la que suman las tres capas de SoilGrids', () => {
    for (const lote of ['DEMO-COL-01', 'DEMO-USA-01']) {
      const j = JSON.parse(readFileSync(new URL(`../../../datos/lotes/parametros_suelo_${lote}.json`, import.meta.url), 'utf8')) as { parametros: Record<string, { profundidad_cm: [number, number] }> }
      expect(j.parametros.cos_t_ha.profundidad_cm, lote).toEqual([0, 30])
    }
    const zonal = readFileSync(new URL('../../../src/simulacion/geo/zonal.py', import.meta.url), 'utf8')
    const m = zonal.match(/\((\d+) \* v_0_5 \+ (\d+) \* v_5_15 \+ (\d+) \* v_15_30\) \/ (\d+)/)!
    expect(Number(m[1]) + Number(m[2]) + Number(m[3])).toBe(Number(m[4]))
    for (const k of Object.keys(PERMITIDOS).filter((x) => x.startsWith('suelo.'))) {
      expect(en[k as keyof typeof en], k).toContain(`0-${m[4]}`)
      expect(es[k as keyof typeof es], k).toContain(`0-${m[4]}`)
    }
  })
  it('los puntos mínimos de Medir salen de lo que la herramienta realmente exige', () => {
    const p: [number, number][] = [[0, 0], [1, 0], [1, 1], [0, 1]]
    const minimo = (f: (n: number) => boolean) => [1, 2, 3, 4].find(f)!
    expect(minimo((n) => resumen('distancia', p.slice(0, n)) !== en['medir.min2'])).toBe(Number(unico(en['medir.min2'])))
    expect(minimo((n) => resumen('area', p.slice(0, n)) !== en['medir.min3'])).toBe(Number(unico(en['medir.min3'])))
    expect(minimo((n) => { try { areaKm2(p.slice(0, n)); return true } catch { return false } })).toBe(Number(unico(en['medir.anillo'])))
    for (const k of ['medir.min2', 'medir.min3', 'medir.anillo'] as const) expect(unico(es[k]!)).toBe(unico(en[k]))
  })
  it('2 m de capa.t2m es el 2 del identificador de la variable t2m', () => {
    expect(unico(en['capa.t2m'])).toBe('t2m'.match(/\d+/)![0])
    expect(unico(es['capa.t2m']!)).toBe('2')
  })
})
