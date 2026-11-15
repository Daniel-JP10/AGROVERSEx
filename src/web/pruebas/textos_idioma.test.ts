// asistido por SI: Claude Code (Anthropic), pruebas de C3: inglés por defecto, paridad de claves EN y ES y glosario técnico bilingüe
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { en } from '../src/textos/en'
import { FALTANTES_ES, es } from '../src/textos/es'
import { GLOSARIO } from '../src/textos/glosario'

const memoria = (inicial?: string) => {
  const d: Record<string, string> = inicial ? { 'agroversex-idioma': inicial } : {}
  return { getItem: (k: string) => d[k] ?? null, setItem: (k: string, v: string) => { d[k] = v }, removeItem: () => {}, clear: () => {}, key: () => null, length: 0 }
}
const cargar = async (inicial?: string) => { vi.resetModules(); vi.stubGlobal('localStorage', memoria(inicial)); return import('../src/textos/i18n') }

describe('idioma por defecto', () => {
  beforeEach(() => vi.unstubAllGlobals())
  it('sin preferencia guardada es inglés', async () => { expect((await cargar()).idioma()).toBe('en') })
  it('respeta la preferencia guardada en español y en inglés', async () => {
    expect((await cargar('es')).idioma()).toBe('es')
    expect((await cargar('en')).idioma()).toBe('en')
  })
  it('alternar pasa de inglés a español y vuelve', async () => {
    const m = await cargar()
    m.alternar(); expect(m.idioma()).toBe('es')
    m.alternar(); expect(m.idioma()).toBe('en')
  })
})

describe('paridad de claves', () => {
  it('cada clave de en existe en es y al revés, sin lista de faltantes ni textos vacíos', () => {
    expect(FALTANTES_ES).toEqual([])
    expect(Object.keys(es).filter((k) => !(k in en))).toEqual([])
    expect(Object.keys(en).filter((k) => !(k in es))).toEqual([])
    for (const [k, v] of [...Object.entries(en), ...Object.entries(es)]) expect(String(v).trim().length, k).toBeGreaterThan(0)
  })
  it('los huecos {nombre} son los mismos en los dos idiomas de cada clave', () => {
    const huecos = (s: string) => [...s.matchAll(/\{(\w+)\}/g)].map((m) => m[1]).sort()
    for (const k of Object.keys(en) as (keyof typeof en)[]) expect(huecos(es[k] ?? ''), k).toEqual(huecos(en[k]))
  })
})

describe('glosario técnico', () => {
  it('cada término trae su detalle técnico en inglés y en español, distinto entre sí', () => {
    for (const g of GLOSARIO) {
      expect(g.tecnico_en, g.termino).toBeTruthy()
      expect(g.tecnico, g.termino).toBeTruthy()
      expect(g.tecnico_en, g.termino).not.toBe(g.tecnico)
    }
  })
})
