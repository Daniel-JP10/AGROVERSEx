// asistido por SI: Claude Code (Anthropic), escritura y revisión de código; base del prototipo migrada en el hackatón
import { describe, expect, it } from 'vitest'
import { desescalar, formatearRango, SIN_DATO } from '../src/datos/desescalar'
import { decodificarCoropleta } from '../src/datos/binario'
import { BANDERA } from '../src/datos/banderas'

describe('desescalar', () => {
  it('el relleno y null dan null', () => {
    expect(desescalar(-32768, 0.01, 0)).toBeNull()
    expect(desescalar(null, 0.01, 0)).toBeNull()
    expect(desescalar(SIN_DATO, 1, 5)).toBeNull() // con desplazamiento tampoco se vuelve válido
  })
  it('aplica escala y desplazamiento', () => expect(desescalar(2550, 0.01, -10)).toBeCloseTo(15.5, 6))
  it('decodifica Int16 LE con NaN en huecos', () => {
    const r = decodificarCoropleta(new Int16Array([100, -32768]).buffer, 0.01, 0)
    expect(r[0]).toBeCloseTo(1, 5)
    expect(r[1]).toBeNaN()
  })
  it('el rango lleva unidad', () => {
    const t = formatearRango(1, 2, 3, 'mm')
    expect(t).toContain('mm'); expect(t).toContain('1'); expect(t).toContain('3')
  })
  it('banderas en el orden de la fase 2', () => {
    expect(Object.values(BANDERA)).toEqual([1, 2, 4, 8, 16])
  })
})
