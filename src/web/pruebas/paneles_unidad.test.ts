// asistido por SI: Claude Code (Anthropic), prueba de que los paneles muestran error y no el número crudo ante una unidad sin conversión
import { beforeAll, describe, expect, it, vi } from 'vitest'
import { createElement } from 'react'
import { renderToString } from 'react-dom/server'
import type { SerieVar } from '../src/datos/series'

const serie = (unidad: string | null): SerieVar => ({ valor: [123.456], p10: [100], p90: [150], frac: [1], unidad_mes: [unidad], productos: [], producto_mes: [-1] })

// en servidor zustand lee el estado inicial, por eso se simula el estado con una unidad elegida
let sel: Record<string, unknown> = { id: 'USA-ADM2-X', nombre: 'Prueba', nivel: 2, pais: 'Estados Unidos' }
vi.mock('../src/app/estado', () => {
  const st = { get seleccion() { return sel }, seleccionar: () => {}, aviso: null, pestana: 'Resumen', abrirPestana: () => {} }
  return { useEstado: (f: (s: unknown) => unknown) => f(st) }
})

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

  it('la cabecera del panel no lleva rótulo general de datos (D-036 c)', async () => {
    const { PanelRegion } = await import('../src/paneles/PanelRegion')
    const { t } = await import('../src/textos/i18n')
    const h = renderToString(createElement(PanelRegion))
    expect(h).toContain('Prueba')
    // solo la cabecera: el rótulo por variable lo ponen Resumen y Series
    const cab = /<p class="etiqueta">(.*?)<\/p>/.exec(h)?.[1] ?? ''
    expect(cab).toContain('Estados Unidos')
    expect(cab).not.toContain(t('globo.sinCargados'))
    expect(cab).not.toMatch(/real data|datos reales|panel\.datosReales/i)
  })
  it('la cabecera de un nivel 0 no termina en separador', async () => {
    sel = { id: 'COL-ADM0', nombre: 'Colombia', nivel: 0, pais: 'Colombia' }
    const { PanelRegion } = await import('../src/paneles/PanelRegion')
    const cab = /<p class="etiqueta">(.*?)<\/p>/.exec(renderToString(createElement(PanelRegion)).replace(/<!-- -->/g, ''))?.[1] ?? ''
    expect(cab).not.toBe('')
    expect(cab).not.toMatch(/·\s*$/)
  })
})
