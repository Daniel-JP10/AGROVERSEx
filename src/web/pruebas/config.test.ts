// asistido por SI: Claude Code (Anthropic), escritura y revisión de código; base del prototipo migrada en el hackatón
import { describe, expect, it } from 'vitest'
import { NIVELES, capasNivel, construirEstilo, nivelParaZoom, SIN_ADM2, SIN_ADM1 } from '../src/globo/config'

describe('tres niveles reales', () => {
  it('hay tres niveles con capa igual a la fuente y propId unidad_id', () => {
    expect(NIVELES.length).toBe(3)
    for (const c of NIVELES) {
      expect(c.capaFuente).toBe(c.fuente)
      expect(c.propId).toBe('unidad_id')
    }
  })
  it('rangos de las teselas: 0-6, 2-9, 6-11 (adm2 llega a z10 por D-016, más un nivel de margen)', () => {
    expect(NIVELES.map((c) => [c.zoomDesde, c.zoomHasta])).toEqual([[0, 6], [2, 9], [6, 11]])
  })
  // Director 08:55: a z11 el relleno de ADM2 se ve. MapLibre sobreescala desde el maxzoom de la cabecera (z10), así que
  // el último nivel no se apaga al acercar ni su capa se corta (antes se apagaba entre z10,5 y z11)
  it('adm2 sigue con relleno al acercar: sin apagado por opacidad y la capa no se corta', () => {
    const r = capasNivel(NIVELES[2]).find((l) => l.id === 'adm2-relleno') as unknown as { maxzoom: number; paint: Record<string, unknown[]> }
    expect(r.maxzoom).toBe(24)
    const op = r.paint['fill-opacity'] as unknown[]
    const paradas = op.slice(3).filter((_, i) => i % 2 === 0)
    expect(paradas.at(-1)).toBe(NIVELES[2].zoomDesde + NIVELES[2].fundido)
    expect(JSON.stringify(op.at(-1))).not.toContain(',0,0]') // la última parada pinta (no vale 0)
  })
  it('se solapan sin dejar zooms sin nivel', () => {
    for (let z = 0; z <= 11; z += 0.25) expect(NIVELES.some((c) => z >= c.zoomDesde && z <= c.zoomHasta)).toBe(true)
    NIVELES.forEach((c, i) => { if (i) expect(c.zoomDesde).toBeLessThanOrEqual(NIVELES[i - 1].zoomHasta) })
  })
  it('nivel de interacción por zoom (color de ADM2 desde 7, D-015)', () => {
    expect(nivelParaZoom(0.5)).toBe(0)
    expect(nivelParaZoom(3)).toBe(1)
    expect(nivelParaZoom(5.5)).toBe(1)
    expect(nivelParaZoom(6)).toBe(1)
    expect(nivelParaZoom(6.9)).toBe(1)
    expect(nivelParaZoom(7)).toBe(2)
  })
  it('adm0 separa las zonas en disputa (es_disputa = 1) con trama', () => {
    const ids = capasNivel(NIVELES[0]).map((l) => l.id)
    expect(ids).toContain('adm0-disputa')
    const rel = capasNivel(NIVELES[0]).find((l) => l.id === 'adm0-relleno') as { filter: unknown[] }
    expect(JSON.stringify(rel.filter)).toContain('es_disputa')
  })
  it('respaldo de ADM1 sin ADM2 (Liechtenstein) y estilo coherente', () => {
    expect(SIN_ADM2).toContain('LIE')
    expect(SIN_ADM1).toContain('ATA')
    const e = construirEstilo('http://x') as { sources: Record<string, unknown>; layers: { id: string; source: string }[] }
    const ids = e.layers.map((l) => l.id)
    expect(new Set(ids).size).toBe(ids.length)
    expect(ids).toContain('adm1-respaldo')
    for (const l of e.layers) expect(e.sources).toHaveProperty(l.source)
  })
})
