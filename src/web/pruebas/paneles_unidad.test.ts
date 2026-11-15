// asistido por SI: Claude Code (Anthropic), prueba de que los paneles muestran error y no el número crudo ante una unidad sin conversión
import { beforeAll, describe, expect, it, vi } from 'vitest'
import { createElement } from 'react'
import { renderToString } from 'react-dom/server'
import type { SerieVar } from '../src/datos/series'

const serie = (unidad: string | null): SerieVar => ({ valor: [123.456], p10: [100], p90: [150], frac: [1], unidad_mes: [unidad], productos: [], producto_mes: [-1] })

let FilaDato: typeof import('../src/paneles/Resumen').FilaDato
let convertirSerie: typeof import('../src/paneles/Series').convertirSerie
beforeAll(async () => {
  vi.stubGlobal('localStorage', { getItem: () => null, setItem: () => {}, removeItem: () => {} })
  FilaDato = (await import('../src/paneles/Resumen')).FilaDato
  convertirSerie = (await import('../src/paneles/Series')).convertirSerie
})

describe('paneles ante una unidad sin conversión', () => {
  it('Resumen con unidad null muestra el estado de error y no el valor', () => {
    const h = renderToString(createElement(FilaDato, { v: 'precip', s: serie(null), mes: 0 })).replace(/<!-- -->/g, '')
    expect(h).toContain('unidad sin conversión: precip/null')
    expect(h).not.toContain('123')
  })
  it('Resumen con unidad válida sí muestra el valor', () => {
    expect(renderToString(createElement(FilaDato, { v: 't2m', s: serie('C'), mes: 0 }))).toContain('123')
  })
  it('Series: unidad null da null (el panel muestra el error) y una válida convierte', () => {
    expect(convertirSerie('precip', serie(null))).toBeNull()
    expect(convertirSerie('precip', serie('mm/day'))?.unidad).toBe('mm/mes')
  })
})
