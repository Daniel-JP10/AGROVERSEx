// asistido por SI: Claude Code (Anthropic), pruebas del formato de las claves de texto del gemelo v1.1
import { describe, expect, it } from 'vitest'
import { formatoG, traducir } from '../src/secciones/rotaciones/textosGemelo'

describe('formatoG imita %g de Python', () => {
  it('casos de referencia de Python', () => {
    // Valores de format(v, spec) en Python 3.12
    expect(formatoG(0.23977571080636217, '+.3g')).toBe('+0.24')
    expect(formatoG(-0.0791, '+.3g')).toBe('-0.0791')
    expect(formatoG(0.4752252964868339, '.3g')).toBe('0.475')
    expect(formatoG(155.68165423832124, '.3g')).toBe('156')
    expect(formatoG(1234.5, '.3g')).toBe('1.23e+03')
    expect(formatoG(0.00001234, '.3g')).toBe('1.23e-05')
    expect(formatoG(5, '+g')).toBe('+5')
    expect(formatoG(0, '+.3g')).toBe('+0')
  })
})

describe('traducir', () => {
  const cat = {
    'card.benefit.delta': '{indicador}: {delta:+.3g} {unidad} (p10 {p10:.3g}, p90 {p90:.3g})',
    'indicator.x.name': 'Production', 'unit.mm/año': 'mm/yr',
    'label.model_simulation': 'Model simulation with {fuentes} data',
    'source.a': 'NASA POWER', 'source.b': 'SoilGrids', 'joiner.and': 'and',
  }
  it('llena la plantilla, traduce las claves anidadas y formatea los números', () => {
    expect(traducir(cat, 'card.benefit.delta', { indicador: { clave: 'indicator.x.name' }, delta: 0.2397, unidad: { clave: 'unit.mm/año' }, p10: 0.4752, p90: 0.8225 }))
      .toBe('Production: +0.24 mm/yr (p10 0.475, p90 0.823)')
  })
  it('une las fuentes con joiner.and', () => {
    expect(traducir(cat, 'label.model_simulation', { fuentes: ['source.a', 'source.b'] })).toBe('Model simulation with NASA POWER and SoilGrids data')
  })
  it('una clave sin texto o un parámetro ausente no se inventa', () => {
    expect(traducir(cat, 'no.existe')).toBe('no.existe')
    expect(traducir(cat, 'card.benefit.delta', {})).toContain('{delta:+.3g}')
  })
})
