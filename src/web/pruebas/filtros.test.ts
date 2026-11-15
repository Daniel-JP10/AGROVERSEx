// asistido por SI: Claude Code (Anthropic), escritura y revisión de código; base del prototipo migrada en el hackatón
import { describe, expect, it } from 'vitest'
import { aplicarFiltros, ocultasPorFiltros } from '../src/datos/filtrar'
import { filtrosRegionalesPara } from '../src/paneles/filtros/filtros_regionales'
import { estadoUnidad } from '../src/globo/coropleta'

const ids = (u: { id: string }[]) => u.map((x) => x.id)
const nombres = (u: object) => filtrosRegionalesPara(u as never).map((f) => f.id)

describe('filtros regionales', () => {
  it('piso térmico: 1.500 m a 5° N sí, a 45° N no', () => {
    expect(nombres({ id: 'a', lat: 5, elevMin: 0, elevMax: 1500 })).toContain('piso_termico')
    expect(nombres({ id: 'b', lat: 45, elevMin: 0, elevMax: 1500 })).not.toContain('piso_termico')
  })
  it('hueco de datos solo por encima de 60° N', () => {
    expect(nombres({ id: 'a', lat: 65 })).toContain('hueco_alta_latitud')
    expect(nombres({ id: 'a', lat: 59 })).not.toContain('hueco_alta_latitud')
  })
  it('unidad sin atributos: lista vacía, sin error', () => {
    expect(filtrosRegionalesPara({ id: 'x' })).toEqual([])
  })
  it('zona DEMO y acidez salen de los atributos y citan evidencia', () => {
    const f = filtrosRegionalesPara({ id: 'x', zona: 'cerrado', ph: 5 })
    expect(f.map((x) => x.id)).toEqual(expect.arrayContaining(['safrinha', 'acidez']))
    expect(f.every((x) => x.evidencia.length > 0)).toBe(true)
  })
})

describe('filtros globales', () => {
  const U = [
    { id: 'a', igbp: 10, eventos: true, valor: 50, fraccion: 0.9 },
    { id: 'b', igbp: 12, eventos: false, valor: 400, fraccion: 0.2 },
    { id: 'c', valor: undefined },
  ]
  it('sin filtros todo es visible', () => { expect([...aplicarFiltros(U, {}, 0)]).toEqual(['a', 'b', 'c']) })
  it('igbp deja solo coincidencias; una unidad sin atributo no coincide', () => {
    expect([...aplicarFiltros(U, { igbp: [10] }, 0)]).toEqual(['a'])
    expect([...aplicarFiltros(U, { igbp: [12] }, 0)]).toEqual(['b'])
  })
  it('soloEventos y rango; rango no vuelve 0 un hueco: sin valor queda fuera', () => {
    expect([...aplicarFiltros(U, { soloEventos: true }, 0)]).toEqual(['a'])
    expect([...aplicarFiltros(U, { rango: [0, 100] }, 0)]).toEqual(['a'])
    expect([...aplicarFiltros(U, { fraccionMin: 0.5 }, 0)]).toEqual(['a'])
  })
  it('enso sin umbral fijado (PENDIENTE) no filtra; con umbral deja solo los meses de La Niña', () => {
    expect(aplicarFiltros(U, { enso: 'nina' }, 5, { roni: [0, 0, 0, 0, 0, -1.2] }).size).toBe(3)
    expect(aplicarFiltros(U, { enso: 'nina' }, 5, { roni: [0, 0, 0, 0, 0, -1.2], umbral: 0.5 }).size).toBe(3)
    expect(aplicarFiltros(U, { enso: 'nina' }, 1, { roni: [0, 0.1], umbral: 0.5 }).size).toBe(0)
  })
  it('las ocultas son las no visibles y una filtrada no es un hueco', () => {
    const o = ocultasPorFiltros(U, { igbp: [10] }, 0)
    expect([...o].sort()).toEqual(['b', 'c'])
    const e = estadoUnidad(100, 1, [0, 500], { ocultas: o }, 'b')
    expect(e.ok).toBe(false)
    expect(e.hueco).toBe(false)
    expect(estadoUnidad(NaN, undefined, [0, 500], { ocultas: o }, 'b').hueco).toBe(true)
  })
})
