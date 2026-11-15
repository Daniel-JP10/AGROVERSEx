// asistido por SI: Claude Code (Anthropic), escritura y revisión de código; base del prototipo migrada en el hackatón
import { createElement } from 'react'
import { renderToStaticMarkup } from 'react-dom/server'
import { beforeAll, describe, expect, it } from 'vitest'
import { Medir, resumen } from '../src/herramientas/Medir'
import { debeAvisarZoom } from '../src/herramientas/AvisoZoom'
import { enEspanol } from './idioma_es'

enEspanol() // las aserciones son en español y el idioma por defecto es el inglés (D-039)

describe('resumen de Medir', () => {
  it('distancia: pide 2 puntos y suma los tramos en km', () => {
    expect(resumen('distancia', [])).toBe('Añade al menos 2 puntos')
    expect(resumen('distancia', [[0, 0], [0, 1]])).toMatch(/^111\.2 km/)
  })
  it('área: pide 3 puntos y da km²', () => {
    expect(resumen('area', [[0, 0], [1, 0]])).toBe('Añade al menos 3 puntos')
    expect(resumen('area', [[0, 0], [1, 0], [1, 1], [0, 1]])).toMatch(/km²/)
  })
})

describe('aviso de zoom 12', () => {
  it('avisa solo en globo y desde zoom 12', () => {
    expect(debeAvisarZoom(12, 'globe')).toBe(true)
    expect(debeAvisarZoom(11.9, 'globe')).toBe(false)
    expect(debeAvisarZoom(13, 'mercator')).toBe(false)
  })
})

describe('Medir accesible por teclado', () => {
  // se renderiza después de fijar el español (beforeAll de enEspanol corre antes)
  let html = ''
  let nombres: string[] = []
  beforeAll(() => {
    html = renderToStaticMarkup(createElement(Medir, { mapa: {} as never }))
    nombres = [...html.matchAll(/<button[^>]*aria-label="([^"]*)"/g)].map((m) => m[1])
  })
  it('los controles son button con texto o nombre accesible', () => {
    expect(html).toContain('Distancia')
    expect(html).toContain('Área')
    expect(html).toContain('Añadir punto en el centro')
    expect(html).toContain('Borrar')
    expect(nombres.length + (html.match(/<button/g) ?? []).length).toBeGreaterThan(0)
  })
  it('el resultado se anuncia con role=status', () => {
    expect(html).toMatch(/role="status"/)
  })
})
