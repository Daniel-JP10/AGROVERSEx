// asistido por SI: Claude Code (Anthropic), escritura y revisión de código; base del prototipo migrada en el hackatón
import { describe, expect, it } from 'vitest'
import { estadoUnidad, partirEnRebanadas, crearMotorCoropleta, textoValor, opacidadValida, leerOpacidad } from '../src/globo/coropleta'
import { mmHoraAMmMes } from '../src/datos/desescalar'
import { capasNivel, NIVELES } from '../src/globo/config'
import { enEspanol } from './idioma_es'

enEspanol() // las aserciones son en español y el idioma por defecto es el inglés (D-039)

const R: [number, number] = [0, 100]
describe('estado por unidad', () => {
  it('normaliza a 0..1 con min/max y recorta fuera de rango', () => {
    expect(estadoUnidad(25, undefined, R, {}).v).toBeCloseTo(0.25)
    expect(estadoUnidad(250, undefined, R, {}).v).toBe(1)
    expect(estadoUnidad(-5, undefined, R, {}).v).toBe(0)
    expect(estadoUnidad(25, undefined, R, {}).ok).toBe(true)
  })
  it('NaN es hueco: ok=false, hueco=true, nunca 0 como valor pintable', () => {
    const e = estadoUnidad(NaN, undefined, R, {})
    expect(e).toMatchObject({ ok: false, hueco: true })
  })
  it('min/max filtran sin marcar hueco', () => {
    expect(estadoUnidad(10, undefined, R, { min: 20 })).toMatchObject({ ok: false, hueco: false })
    expect(estadoUnidad(90, undefined, R, { max: 80 }).ok).toBe(false)
    expect(estadoUnidad(50, undefined, R, { min: 20, max: 80 }).ok).toBe(true)
  })
  it('fraccionMin oculta unidades con fraccion valida menor', () => {
    expect(estadoUnidad(50, 0.03, R, { fraccionMin: 0.5 }).ok).toBe(false)
    expect(estadoUnidad(50, 0.9, R, { fraccionMin: 0.5 }).ok).toBe(true)
    expect(estadoUnidad(50, NaN, R, { fraccionMin: 0.5 }).ok).toBe(false)
  })
})

describe('partirEnRebanadas', () => {
  it('cubre todo sin repetir', () => {
    const a = Array.from({ length: 1234 }, (_, i) => i)
    const r = partirEnRebanadas(a, 500)
    expect(r.map((x) => x.length)).toEqual([500, 500, 234])
    expect(r.flat()).toEqual(a)
  })
  it('vacío da vacío', () => expect(partirEnRebanadas([], 5)).toEqual([]))
})

describe('motor', () => {
  it('guarda el estado por id y avisa del cambio', () => {
    let n = 0
    const m = crearMotorCoropleta({ hasImage: () => true } as never, { nivel: 1, rango: R, alCambiar: () => n++ })
    m.aplicar(new Float32Array([10, NaN, 90]), ['a', 'b', 'c'], { max: 50 })
    expect(m.estado('a')?.ok).toBe(true)
    expect(m.estado('b')?.hueco).toBe(true)
    expect(m.estado('c')?.ok).toBe(false)
    expect(m.estado('z')).toBeUndefined()
    expect(n).toBe(1)
    m.destruir()
    expect(m.estado('a')).toBeUndefined()
  })
})

describe('texto y unidades', () => {
  it('lluvia mm/h a mm/mes', () => expect(mmHoraAMmMes(0.1, '2023-04', 'mm/h')).toBeCloseTo(72))
  it('hueco se rotula, nunca 0', () => {
    expect(textoValor(estadoUnidad(NaN, undefined, R, {}), 'mm/mes', R)).toContain('sin dato del producto')
  })
  it('valor siempre con rango y unidad', () => {
    const t = textoValor(estadoUnidad(50, undefined, R, {}), 'mm/mes', R)
    expect(t).toMatch(/mm\/mes/); expect(t).toMatch(/rango/)
  })
})

describe('opacidad', () => {
  it('valida 0..100 y por defecto 62', () => {
    expect(opacidadValida(150)).toBe(100); expect(opacidadValida(-3)).toBe(0); expect(opacidadValida(NaN)).toBe(62)
  })
  it('leer tolera localStorage roto', () => {
    expect(leerOpacidad({ getItem: () => { throw new Error('x') } } as never)).toBe(62)
    expect(leerOpacidad({ getItem: () => '40' } as never)).toBe(40)
  })
})

describe('capas', () => {
  it('cada nivel trae su capa de huecos con trama', () => {
    for (const c of NIVELES) {
      const h = capasNivel(c).find((l) => l.id === `${c.fuente}-huecos`) as { paint: Record<string, unknown> } | undefined
      expect(h?.paint['fill-pattern']).toBe('sin-dato')
    }
  })
})
