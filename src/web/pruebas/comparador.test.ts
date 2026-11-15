// asistido por SI: Claude Code (Anthropic), escritura y revisión de código; base del prototipo migrada en el hackatón
import { describe, expect, it } from 'vitest'
import { ordenar, sensibilidad, type Estrategia, type Pesos } from '../src/paneles/comparador/ordenar'
import { adaptar } from '../src/paneles/comparador/datos'
import { FIX_CORN_BELT, FIX_PAMPA } from '../src/paneles/comparador/fixtures'

const ceros: Pesos = { agua: 0, forraje: 0, nitrogeno: 0, erosion: 0, materiaOrganica: 0, mercado: 0 }
const e = (id: string, b: Partial<Estrategia['beneficios']>, o: Partial<Estrategia> = {}): Estrategia => ({
  id, nombre: id, cultivos: [], aguaMm: null, exige: { siembraDirecta: false, cosechaForraje: false }, efecto2: null,
  beneficios: { agua: null, forraje: null, nitrogeno: null, erosion: null, materiaOrganica: null, mercado: null, ...b }, ...o,
})
const sin = { cultivosAceptados: null, aguaMaxMm: null, siembraDirecta: true, cosechaForraje: true }

describe('ordenar', () => {
  it('pesos en 0: orden original, sin error', () => {
    const r = ordenar([e('b', { erosion: { v: 1 } }), e('a', { erosion: { v: 9 } })], ceros, sin)
    expect(r.map((x) => x.estrategia.id)).toEqual(['b', 'a'])
  })
  it('rinde menos queda marcada aunque sea primera', () => {
    const r = ordenar([e('h', { erosion: { v: 1 } }), e('c', { erosion: { v: 9 } }, { efecto2: -5.5 })], { ...ceros, erosion: 5 }, sin)
    expect(r[0].estrategia.id).toBe('c')
    expect(r[0].rindeMenosQueHabitual).toBe(-5.5)
  })
  it('viola restricción: se marca y no se oculta', () => {
    const r = ordenar([e('a', {}, { aguaMm: 600, cultivos: ['maiz'], exige: { siembraDirecta: true, cosechaForraje: false } })],
      ceros, { cultivosAceptados: ['soya'], aguaMaxMm: 500, siembraDirecta: false, cosechaForraje: true })
    expect(r).toHaveLength(1)
    expect(r[0].viola.length).toBe(3)
  })
  it('empate: orden determinista por posición original', () => {
    const l = [e('x', { erosion: { v: 2 } }), e('y', { erosion: { v: 2 } }), e('z', { erosion: { v: 2 } })]
    expect(ordenar(l, { ...ceros, erosion: 3 }, sin).map((x) => x.estrategia.id)).toEqual(['x', 'y', 'z'])
  })
  it('intervalo contiene al puntaje', () => {
    const r = ordenar([e('a', { erosion: { v: 5, rango: [3, 7] } }), e('b', { erosion: { v: 4 } })], { ...ceros, erosion: 2 }, sin)
    for (const x of r) { expect(x.intervalo[0]).toBeLessThanOrEqual(x.puntaje); expect(x.intervalo[1]).toBeGreaterThanOrEqual(x.puntaje) }
  })
})

describe('sensibilidad', () => {
  const l = [e('a', { erosion: { v: 10 }, nitrogeno: { v: 0 } }), e('b', { erosion: { v: 0 }, nitrogeno: { v: 10 } })]
  it('mover un peso hasta su umbral cambia el primer lugar', () => {
    const p: Pesos = { ...ceros, erosion: 3, nitrogeno: 2 }
    expect(ordenar(l, p, sin)[0].estrategia.id).toBe('a')
    const s = sensibilidad(l, p)
    const d = s.cambioMinimoPorPeso.nitrogeno!
    expect(d).toBeGreaterThan(0.9)
    expect(ordenar(l, { ...p, nitrogeno: 2 + d + 0.06 }, sin)[0].estrategia.id).toBe('b')
    expect(s.cambioMinimoPorPeso.forraje).toBeNull()
  })
  it('primero estable solo si su intervalo mínimo supera al máximo de los demás', () => {
    expect(sensibilidad([e('a', { erosion: { v: 10 } }), e('b', { erosion: { v: 0 } })], { ...ceros, erosion: 3 }).primeroEstable).toBe(true)
    expect(sensibilidad([e('a', { erosion: { v: 6, rango: [0, 10] } }), e('b', { erosion: { v: 5, rango: [0, 10] } })], { ...ceros, erosion: 3 }).primeroEstable).toBe(false)
  })
})

describe('adaptar (forma de las tablas reales)', () => {
  it('Corn Belt: 3 estrategias, efecto2/eff_div/betas por separado, sin combinación', () => {
    const a = adaptar(FIX_CORN_BELT)
    expect(a.estrategias).toHaveLength(3)
    expect(a.etiqueta).toBe('FUENTE')
    expect(a.antecesor[0]).toMatchObject({ efecto2: expect.any(Number), eff_div: expect.any(Number), beta_lluvia: expect.any(Number), beta_t: expect.any(Number) })
    expect(JSON.stringify(a)).not.toMatch(/combinaci/i)
  })
  it('Pampa: PENDIENTE visible, no se rellena', () => {
    const a = adaptar(FIX_PAMPA)
    expect(a.pendientes.length).toBeGreaterThan(0)
  })
  it('vacío: motivo literal', () => {
    // código S (soya) no casa por subcadena con cualquier texto; solo S→C con ambos nombres presentes
    const a = adaptar({ vacio: false, sistemas: [{ id: 's', region: 'R', habitual: 'x', alternativa_1: 'Maíz-soya', alternativa_2: 'Trigo', fuente_id: 'f', etiqueta: 'FUENTE' }], cultivos: [{ id: 'Maíz grano', nombre: 'Maíz', familia: '', fija_n: 0, ndfa_media: null, etiqueta: '' }], antecesor: [{ pais: 'EE. UU.', antecesor: 'S', cultivo: 'C', efecto2: 0.9, eff_div: null, beta_lluvia: null, beta_t: null, significativo: 1, fuente_id: 'f' }] })
    expect(a.estrategias[1].efecto2).toBe(0.9)
    expect(a.estrategias[2].efecto2).toBeNull()
    expect(adaptar({ vacio: true, motivo: 'sin sistema de rotación documentado', regiones_disponibles: [] }).estrategias).toEqual([])
  })
})
