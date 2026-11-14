// asistido por SI: Claude Code (Anthropic), escritura y revisión de código; base del prototipo migrada en el hackatón
import { describe, expect, it } from 'vitest'
import { anomalia, tendencia, segmentar, mmPorMes } from '../src/datos/series'

describe('series', () => {
  it('anomalia resta la media de la base ignorando null', () => {
    expect(anomalia([1, null, 3, 10, null], 0, 2)).toEqual([-1, null, 1, 8, null])
  })
  it('tendencia: el IC contiene la pendiente', () => {
    const t = tendencia([1, 2.1, 2.9, 4.2, 4.8, 6.1, 7])
    expect(t.pendiente).toBeGreaterThan(0.9)
    expect(t.ic[0]).toBeLessThanOrEqual(t.pendiente); expect(t.ic[1]).toBeGreaterThanOrEqual(t.pendiente)
  })
  it('segmentar no cruza huecos', () => {
    expect(segmentar([1, 2, null, null, 5, 6, 7, null])).toEqual([{ desde: 0, valores: [1, 2] }, { desde: 4, valores: [5, 6, 7] }])
  })
  it('lluvia mm/h a mm/mes', () => expect(mmPorMes(1)).toBeCloseTo(730.5, 1))
})

import { paraMostrar, nombreVar } from '../src/datos/series'
describe('mostrar', () => {
  it('unidad por variable y sin dato nunca es 0', () => {
    expect(paraMostrar('precip', 1, 'mm/h')).toEqual({ valor: 730.5, unidad: 'mm/mes' })
    expect(paraMostrar('t2m', 21.5, 'C')).toEqual({ valor: 21.5, unidad: '°C' })
    expect(paraMostrar('ndvi', 0.6, 'adim').unidad).toBe('adimensional')
    expect(paraMostrar('t2m', null, 'C').valor).toBeNull()
    expect(nombreVar('t2m')).toBe('Temperatura a 2 m')
  })
})
