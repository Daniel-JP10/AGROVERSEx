// asistido por SI: Claude Code (Anthropic), escritura y revisión de código; base del prototipo migrada en el hackatón
import { describe, expect, it } from 'vitest'
import { valorSimulado, etiquetaMes, N_MESES } from '../src/tiempo/valor'
import { NIVELES, capasNivel, construirEstilo, nivelParaZoom } from '../src/globo/config'

describe('valor placeholder', () => {
  it('es determinista y está en [0,1]', () => {
    for (const id of [1, 77, 'COL.1.2_1']) for (let m = 0; m < N_MESES; m += 7) {
      expect(valorSimulado(id, m)).toBe(valorSimulado(id, m))
      expect(valorSimulado(id, m)).toBeGreaterThanOrEqual(0)
      expect(valorSimulado(id, m)).toBeLessThanOrEqual(1)
    }
    expect(valorSimulado(1, 0)).not.toBe(valorSimulado(2, 0))
  })
  it('el rango de meses es 2000-01 a 2026-11', () => {
    expect(etiquetaMes(0)).toBe('2000-01')
    expect(etiquetaMes(N_MESES - 1)).toBe('2026-11')
  })
})

describe('configuración de capas', () => {
  it('niveles consecutivos, con zoom coherente y fuentes únicas', () => {
    NIVELES.forEach((c, i) => {
      expect(c.nivel).toBe(i)
      expect(c.zoomDesde).toBeLessThan(c.zoomHasta)
      if (i) expect(c.zoomDesde).toBeLessThan(NIVELES[i - 1].zoomHasta)
    })
    expect(new Set(NIVELES.map((c) => c.fuente)).size).toBe(NIVELES.length)
  })
  it('el estilo referencia solo fuentes existentes y ids de capa únicos', () => {
    const e = construirEstilo('http://x') as { sources: Record<string, unknown>; layers: { id: string; source: string }[] }
    const ids = e.layers.map((l) => l.id)
    expect(new Set(ids).size).toBe(ids.length)
    for (const l of e.layers) expect(e.sources).toHaveProperty(l.source)
    expect(capasNivel(NIVELES[0]).length).toBe(8) // huecos x2, relleno, respaldo, disputa, línea, hover, selección
  })
  it('países al alejar, nivel 1 al acercar', () => {
    expect(nivelParaZoom(2)).toBe(0)
    expect(nivelParaZoom(5)).toBe(1)
  })
})
