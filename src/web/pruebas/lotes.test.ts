// asistido por SI: Claude Code (Anthropic), escritura y revisión de código; base del prototipo migrada en el hackatón
import { describe, expect, it } from 'vitest'
import { parsearWkt } from '../src/datos/wkt'
import { ventanaSueloExpuesto, rotuloRiesgo, RIESGOS } from '../src/paneles/lotes/modelo'

describe('lotes', () => {
  it('parsearWkt devuelve un polígono cerrado', () => {
    const p = parsearWkt('POLYGON((0 0,1 0,1 1,0 0))')
    expect(p.type).toBe('Polygon')
    expect(p.coordinates[0]).toHaveLength(4)
    expect(p.coordinates[0][0]).toEqual(p.coordinates[0].at(-1))
  })
  it('acepta el espacio tras POLYGON de la base real', () => {
    expect(parsearWkt('POLYGON ((-72.4 6.7, -72.4 6.8, -72.5 6.8, -72.4 6.7))').coordinates[0][1]).toEqual([-72.4, 6.8])
  })
  it('WKT inválido lanza error controlado', () => {
    for (const m of ['', 'POINT(1 1)', 'POLYGON((0 0,1 x))', 'POLYGON((0 0,1 0,1 1))', 'POLYGON((0 0,1 0,1 1,0 0),(0 0,1 0,1 1,0 0))'])
      expect(() => parsearWkt(m)).toThrow(/WKT/)
  })
  it('ventana de suelo expuesto: última temporada detectada', () => {
    const v = ventanaSueloExpuesto({ ventanas: [
      { temporada: '2000', inicio: 5, fin: 21, error_semanas: 0.6, detectada: 1 },
      { temporada: '2001', inicio: null, fin: null, error_semanas: null, detectada: 0 },
    ] })
    expect(v).toEqual({ inicio: 5, fin: 21, errorSemanas: 0.6 })
    expect(ventanaSueloExpuesto({ ventanas: [] })).toBeNull()
  })
  it('riesgos: contexto de resolución salvo erosión', () => {
    expect(rotuloRiesgo(RIESGOS.estres)).toBe('contexto de SMAP 9 km, no del lote')
    expect(rotuloRiesgo(RIESGOS.helada)).toBe('contexto de POWER ~0,5°, no del lote')
    expect(rotuloRiesgo(RIESGOS.erosion)).not.toMatch(/contexto de/)
    expect(RIESGOS.erosion.valor).toBeNull()
  })
})
