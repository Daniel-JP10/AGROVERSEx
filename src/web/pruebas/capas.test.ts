// asistido por SI: Claude Code (Anthropic), escritura y revisión de código; base del prototipo migrada en el hackatón
import { describe, expect, it } from 'vitest'
import { CAPAS, capaPorId, valoresCapa } from '../src/datos/capas'
import { CALENDARIO } from '../src/tiempo/huecos'
import { rotulosDeVariable, BANDERA, BANDERA_CALIDAD_BAJA } from '../src/datos/banderas'
import { enEspanol } from './idioma_es'

enEspanol() // las aserciones son en español y el idioma por defecto es el inglés (D-039)

describe('capas', () => {
  it('toda capa apunta a un producto del calendario y tiene un rango creciente', () => {
    for (const c of CAPAS) {
      expect(CALENDARIO[c.calendario], c.id).toBeDefined()
      expect(c.rango[0]).toBeLessThan(c.rango[1])
    }
  })
  it('un id desconocido cae en la capa inicial', () => expect(capaPorId('nada').id).toBe('precip'))
  it('solo hay capas con dato real: las cuatro variables núcleo', () => expect(CAPAS.map((c) => c.id)).toEqual(['precip', 'sm_raiz', 't2m', 'ndvi']))
  it('la lluvia pasa de mm/hr a mm/mes con los días del mes, la temperatura de K a °C y el NDVI no cambia', () => {
    expect(valoresCapa(capaPorId('precip'), new Float32Array([1]), 0, 'mm/hr')[0]).toBeCloseTo(744)
    expect(valoresCapa(capaPorId('t2m'), new Float32Array([273.15]), 0, 'K')[0]).toBeCloseTo(0, 4)
    expect(valoresCapa(capaPorId('ndvi'), new Float32Array([0.5]), 0, '1')[0]).toBeCloseTo(0.5)
    expect(() => valoresCapa(capaPorId('precip'), new Float32Array([1]), 0, '')).toThrow(/sin conversión/) // sin unidad no hay atajo
  })
})

describe('banderas por variable', () => {
  const todo = BANDERA.FUERA_COBERTURA | BANDERA_CALIDAD_BAJA
  it('con valor presente, la lluvia no hereda el fuera de cobertura de otro producto', () =>
    expect(rotulosDeVariable('precip', todo, true)).toEqual(['calidad baja']))
  it('la temperatura con valor no lleva banderas ajenas', () => expect(rotulosDeVariable('t2m', todo, true)).toEqual([]))
  it('sin valor se explican todos los motivos', () => expect(rotulosDeVariable('ndvi', todo, false)).toContain('fuera de cobertura'))
})
