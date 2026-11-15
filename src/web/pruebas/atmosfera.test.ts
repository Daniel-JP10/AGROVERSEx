// asistido por SI: Claude Code (Anthropic), escritura y revisión de código; base del prototipo migrada en el hackatón
import { describe, expect, it } from 'vitest'
import { radioGlobo, opacidadHalo } from '../src/globo/atmosfera'

describe('atmósfera', () => {
  it('radioGlobo crece con el zoom y es 0 sin canvas', () => {
    let previo = 0
    for (let z = 0; z <= 7; z += 0.5) { const r = radioGlobo(z, 10, 800); expect(r).toBeGreaterThan(previo); previo = r }
    expect(radioGlobo(2, 0, 0)).toBe(0)
  })
  it('el halo es pleno a zoom 5 y nulo a zoom 7', () => {
    expect(opacidadHalo(5)).toBe(1)
    expect(opacidadHalo(7)).toBe(0)
  })
})
