// asistido por SI: Claude Code (Anthropic), escritura y revisión de código; base del prototipo migrada en el hackatón
import { describe, expect, it } from 'vitest'
import { crearBuscador, migaDe, type FilaIndice, type UnidadMiga } from '../src/datos/busqueda'

const f = (id: string, nivel: number, n: string, ctx = '', es?: string): FilaIndice => ({ id, nivel, n, a: n.normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase(), es, ctx })
const filas = [
  f('COL', 0, 'Colombia'), f('COL.6_2', 1, 'Bolívar', 'Colombia'), f('VEN.6_1', 1, 'Bolívar', 'Venezuela'),
  f('COL.3_1', 1, 'Bogotá D.C.', 'Colombia'), f('CIV', 0, "Côte d'Ivoire", '', 'Costa de Marfil'),
  f('RUS.1_1', 1, 'Москва', 'Russia'), f('X.1_1', 2, "O'Higgins", 'Chile'), f('Z01', 9, 'Zona en disputa (Z01)', 'Zona en disputa'),
]
const b = crearBuscador(filas)

describe('buscador', () => {
  it('bogota encuentra Bogotá', () => expect(b.buscar('bogota').map((x) => x.id)).toContain('COL.3_1'))
  it('cote d encuentra Costa de Marfil', () => expect(b.buscar('cote d').map((x) => x.id)).toContain('CIV'))
  it('Costa de Marfil por nombre en español', () => expect(b.buscar('costa de marfil')[0].id).toBe('CIV'))
  it('apóstrofo y escritura no latina sin error', () => {
    expect(b.buscar("o'higgins")[0].id).toBe('X.1_1')
    expect(b.buscar('Москва')[0].id).toBe('RUS.1_1')
    expect(() => b.buscar("'")).not.toThrow()
  })
  it('homónimos traen ctx; el nivel 9 se busca', () => {
    expect(b.buscar('bolivar').map((x) => x.ctx).sort()).toEqual(['Colombia', 'Venezuela'])
    expect(b.buscar('disputa')[0].id).toBe('Z01')
  })
})

describe('migaDe', () => {
  const un = new Map<string, UnidadMiga>([
    ['COL', { padre_id: null, iso3: 'COL', nombre: 'Colombia', nivel: 0 }],
    ['COL.1_1', { padre_id: 'COL', iso3: 'COL', nombre: 'Meta', nivel: 1 }],
    ['COL.1.1_1', { padre_id: 'COL.1_1', iso3: 'COL', nombre: 'Acacías', nivel: 2 }],
    ['CYP', { padre_id: null, iso3: 'CYP', nombre: 'Chipre', nivel: 0 }],
    ['CYP.9_1', { padre_id: null, iso3: 'CYP', nombre: 'Huérfano', nivel: 2 }],
  ])
  it('tres niveles', () => expect(migaDe('COL.1.1_1', un).map((p) => p.nombre)).toEqual(['Colombia', 'Meta', 'Acacías']))
  it('ADM2 sin padre_id usa iso3 y omite el departamento', () => {
    const m = migaDe('CYP.9_1', un)
    expect(m.map((p) => p.nombre)).toEqual(['Chipre', 'Huérfano'])
    expect(m.some((p) => String(p.nombre) === 'undefined')).toBe(false)
  })
})
