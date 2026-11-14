// asistido por SI: Claude Code (Anthropic), pruebas de que los textos de la sección Tierra salen por clave (contrato web_componentes §6)
import { describe, expect, it, vi } from 'vitest'
import { createElement } from 'react'
import { renderToStaticMarkup } from 'react-dom/server'

vi.stubGlobal('localStorage', { getItem: () => 'en', setItem: () => {} })
const { Riel } = await import('../src/secciones/tierra/Riel')
const { Medir } = await import('../src/herramientas/Medir')
const { CAPAS } = await import('../src/datos/capas')
const { nombreVar } = await import('../src/datos/series')
const { rotulosBandera, BANDERA } = await import('../src/datos/banderas')
const { en } = await import('../src/textos/en')
const { es } = await import('../src/textos/es')

describe('textos de Tierra por clave', () => {
  it('en inglés el riel y la capa salen en inglés', () => {
    const html = renderToStaticMarkup(createElement(Riel, { activa: '', onElegir: () => {} }))
    expect(html).toContain('Layers')
    expect(html).toContain('Compare')
    expect(html).not.toContain('Capas')
    expect(CAPAS[0].nombre).toBe('Monthly rainfall')
    expect(nombreVar('t2m')).toBe('Temperature at 2 m')
    expect(rotulosBandera(BANDERA.NUBE)).toEqual(['cloud'])
  })
  it('Medir no deja texto en español en inglés', () => {
    const map = { on() {}, off() {}, getCenter: () => ({ lng: 0, lat: 0 }), getSource: () => null, getLayer: () => null, addSource() {}, addLayer() {}, getCanvas: () => ({ style: {} }), getZoom: () => 1 }
    const html = renderToStaticMarkup(createElement(Medir, { mapa: map as never }))
    expect(html).toContain('Distance')
    expect(html).not.toContain('Distancia')
  })
  it('las claves nuevas del inglés no son copia del español, salvo nombres propios', () => {
    const iguales = Object.keys(es).filter((k) => (en as Record<string, string>)[k] === (es as Record<string, string>)[k])
    for (const k of iguales) expect(['idioma.boton', 'capa.ndvi', 'enso.real', 'lotes.error', 'bandera.provisional', 'series.variable', 'resumen.eventos'].includes(k) || /^(ayuda|modo|idioma)/.test(k), k).toBe(true)
  })
})
