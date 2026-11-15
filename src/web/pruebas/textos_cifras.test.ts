// asistido por SI: Claude Code (Anthropic), prueba O1: ninguna cifra de datos escrita a mano en los textos visibles; salen de huecos {…}
import { readFileSync } from 'node:fs'
import { describe, expect, it } from 'vitest'
import { cifra, conCifras } from '../src/textos/cifras'
import { en } from '../src/textos/en'
import { es } from '../src/textos/es'

// Excepciones reconocidas, clave -> tokens permitidos: nomenclatura de interfaz, no cifras de datos
const PERMITIDOS: Record<string, string[]> = {
  'capa.t2m': ['2'], // altura de la variable (a 2 m)
  'filtros.fraccion': ['0', '1'], // rango del campo numérico
  'medir.anillo': ['3'], 'medir.min2': ['2'], 'medir.min3': ['3'], // cuántos puntos pide la herramienta
  'series.ic': ['95'], // nivel convencional del intervalo de confianza
  ...Object.fromEntries(['arcilla', 'arena', 'carbono', 'cic', 'densidad', 'limo', 'nitrogeno', 'ph'].map((k) => [`suelo.${k}`, ['0-30']])), // capa de profundidad del producto
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
