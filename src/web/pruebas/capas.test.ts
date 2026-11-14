// asistido por SI: Claude Code (Anthropic), escritura y revisión de código; base del prototipo migrada en el hackatón
import { describe, expect, it } from 'vitest'
import { CAPAS, capaPorId, valoresCapa } from '../src/datos/capas'
import { CALENDARIO } from '../src/tiempo/huecos'
import { rotulosDeVariable, BANDERA, BANDERA_CALIDAD_BAJA } from '../src/datos/banderas'

describe('capas', () => {
  it('toda capa apunta a un producto del calendario y tiene un rango creciente', () => {
    for (const c of CAPAS) {
      expect(CALENDARIO[c.calendario], c.id).toBeDefined()
      expect(c.rango[0]).toBeLessThan(c.rango[1])
    }
  })
  it('un id desconocido cae en la capa inicial', () => expect(capaPorId('nada').id).toBe('precip'))
  it('la lluvia pasa de mm/h a mm/mes con los días del mes y el resto no cambia', () => {
    const ene = valoresCapa(capaPorId('precip'), new Float32Array([1]), 0)
    expect(ene[0]).toBeCloseTo(744)
    const v = new Float32Array([0.5])
    expect(valoresCapa(capaPorId('ndvi'), v, 0)).toBe(v)
  })
})

describe('banderas por variable', () => {
  const todo = BANDERA.FUERA_COBERTURA | BANDERA_CALIDAD_BAJA
  it('con valor presente, la lluvia no hereda el fuera de cobertura de otro producto', () =>
    expect(rotulosDeVariable('precip', todo, true)).toEqual(['calidad baja']))
  it('la temperatura con valor no lleva banderas ajenas', () => expect(rotulosDeVariable('t2m', todo, true)).toEqual([]))
  it('sin valor se explican todos los motivos', () => expect(rotulosDeVariable('ndvi', todo, false)).toContain('fuera de cobertura'))
})
