// asistido por SI: Claude Code (Anthropic), prueba del orden por prioridades con los casos de contratos/prioridades_casos.json (gemelo_api §4, v1.2)
import { readFileSync } from 'node:fs'
import { describe, expect, it } from 'vitest'
import ejemplo from '../src/secciones/rotaciones/ejemplo_gemelo.json'
import type { SalidaOptimizacion } from '../src/secciones/rotaciones/gemelo'
import { DESLIZADORES, OBJETIVOS_DE, ordenar, faltantes, faltantesDelDocumento, ordenDelDocumento, PESOS_IGUALES, puntajes, SENTIDO, type Pesos } from '../src/secciones/rotaciones/ordenPrioridades'

interface Casos {
  deslizadores: Record<string, string[]>; objetivos: Record<string, { sentido: 'max' | 'min' }>
  tabla: Record<string, Record<string, number>>; casos: { nombre: string; pesos: Pesos; puntajes: Record<string, number>; orden: string[] }[]
}
const J = JSON.parse(readFileSync(new URL('../../../contratos/prioridades_casos.json', import.meta.url), 'utf8')) as Casos
const estrategias = Object.entries(J.tabla).map(([id, valores]) => ({ id, valores }))

describe('orden por prioridades (gemelo_api §4 v1.2)', () => {
  it('el mapa de deslizadores y los sentidos coinciden con el contrato', () => {
    expect(Object.keys(OBJETIVOS_DE).sort()).toEqual(Object.keys(J.deslizadores).sort())
    for (const k of DESLIZADORES) expect([...OBJETIVOS_DE[k]]).toEqual(J.deslizadores[k])
    for (const [o, v] of Object.entries(J.objetivos)) expect(SENTIDO[o], o).toBe(v.sentido)
    expect(J.deslizadores.suelo).toContain('exposicion_erosiva')
    expect(J.deslizadores.suelo).not.toContain('lluvia_intensa_suelo_desnudo')
  })
  for (const c of J.casos) {
    it(`caso «${c.nombre}»: puntajes y orden del contrato`, () => {
      const s = puntajes(estrategias, c.pesos)
      for (const [id, v] of Object.entries(c.puntajes)) expect(s[id], id).toBeCloseTo(v, 5)
      expect(ordenar(estrategias, c.pesos)).toEqual(c.orden)
    })
  }
  it('el alias obsoleto lluvia_intensa_suelo_desnudo da el mismo orden que exposicion_erosiva', () => {
    const viejo = estrategias.map(({ id, valores: { exposicion_erosiva, ...resto } }) => ({ id, valores: { ...resto, lluvia_intensa_suelo_desnudo: exposicion_erosiva } }))
    const solo = J.casos.find((c) => c.nombre === 'solo suelo')!
    expect(ordenar(viejo, solo.pesos)).toEqual(solo.orden)
  })
  it('sobre el ejemplo v1.1, todas las estrategias salen incompletas y conservan el orden del documento', () => {
    const doc = ejemplo as unknown as SalidaOptimizacion
    const ids = [doc.linea_base.id, ...doc.frente.map((e) => e.id)]
    const iguales = ordenDelDocumento(doc, PESOS_IGUALES)
    expect([...iguales].sort()).toEqual([...ids].sort())
    // el ejemplo v1.1 no trae riego, fertilizante ni demás objetivos: todas incompletas, orden del documento y nada imputado
    expect(Object.keys(faltantesDelDocumento(doc)).sort()).toEqual([...ids].sort())
    // C-4 (director, 08:55): las incompletas se ordenan por objetivos faltantes, suma de normalizados y id (antes: orden del documento)
    const orden = ordenDelDocumento(doc, { agua: 0, suelo: 5, insumos: 0, estabilidad_climatica: 0 })
    expect([...orden].sort()).toEqual([...ids].sort())
    const nf = faltantesDelDocumento(doc)
    for (let i = 1; i < orden.length; i++) expect(nf[orden[i]].length).toBeGreaterThanOrEqual(nf[orden[i - 1]].length)
  })
})

describe('objetivo de prioridad sin valor (D-039.4)', () => {
  const completas = [
    { id: 'A', valores: { riego: 0, deficit: 0.2, carbono: 0.1, exposicion_erosiva: 20, fertilizante: 100, riesgo_produccion: 0.3 } },
    { id: 'B', valores: { riego: 0, deficit: 0.3, carbono: -0.1, exposicion_erosiva: 30, fertilizante: 150, riesgo_produccion: 0.25 } },
  ]
  // C es la mejor en lo que tiene, pero no trae fertilizante: no se imputa y va después de las completas
  const C = { id: 'C', valores: { riego: 0, deficit: 0.1, carbono: 0.5, exposicion_erosiva: 5, fertilizante: null, riesgo_produccion: 0.9 } }
  it('la incompleta queda marcada con el objetivo que le falta', () => {
    expect(faltantes([...completas, C])).toEqual({ C: ['fertilizante'] })
    expect(faltantes(completas)).toEqual({})
  })
  it('se ordena después de las completas con cualquier peso, aunque su puntaje parcial sea el mayor', () => {
    for (const pesos of [PESOS_IGUALES, { agua: 0, suelo: 5, insumos: 0, estabilidad_climatica: 0 }, { agua: 0, suelo: 0, insumos: 0, estabilidad_climatica: 0 }])
      expect(ordenar([C, ...completas], pesos).at(-1)).toBe('C')
  })
  it('las completas conservan el orden que tendrían sin la incompleta en el normalizado de las que sí tienen valor', () => {
    expect(ordenar([...completas, C], PESOS_IGUALES).slice(0, 2)).toEqual(['A', 'B'])
  })
  it('nunca se imputa: el valor ausente no se lee como cero ni como media', () => {
    const cero = { ...C, valores: { ...C.valores, fertilizante: 0 } }
    expect(faltantes([...completas, cero])).toEqual({})
    expect(ordenar([...completas, cero], { agua: 0, suelo: 0, insumos: 5, estabilidad_climatica: 0 })[0]).toBe('C')
  })
})

describe('C-4: normalización y orden interno de las incompletas (D-039, director 08:55)', () => {
  const A = { id: 'A', valores: { riego: 0, deficit: 0.2, carbono: 0.1, exposicion_erosiva: 20, fertilizante: 100, riesgo_produccion: 0.3 } }
  const B = { id: 'B', valores: { riego: 0, deficit: 0.3, carbono: -0.1, exposicion_erosiva: 30, fertilizante: 150, riesgo_produccion: 0.25 } }
  it('la normalización de cada objetivo usa todas las estrategias con valor en ese objetivo, también las incompletas', () => {
    const Z = { id: 'Z', valores: { riego: null, deficit: 0.9, carbono: 2, exposicion_erosiva: 1, fertilizante: 300, riesgo_produccion: 0.1 } }
    expect(puntajes([A, B, Z], PESOS_IGUALES).A).not.toBe(puntajes([A, B], PESOS_IGUALES).A)
  })
  it('incompletas: primero menos objetivos faltantes, luego mayor suma de normalizados disponibles, luego id', () => {
    const D = { id: 'D', valores: { riego: null, deficit: 0.1, carbono: 0.5, exposicion_erosiva: 5, fertilizante: null, riesgo_produccion: 0.9 } }
    const E = { id: 'E', valores: { riego: 0, deficit: 0.3, carbono: -0.1, exposicion_erosiva: 30, fertilizante: null, riesgo_produccion: 0.25 } }
    const F = { id: 'F', valores: { riego: 0, deficit: 0.1, carbono: 0.5, exposicion_erosiva: 5, fertilizante: null, riesgo_produccion: 0.9 } }
    const G = { id: 'G', valores: { ...F.valores } }
    // D le faltan 2; E, F y G les falta 1. F y G empatan en suma: decide el id
    expect(ordenar([D, G, E, A, F, B], PESOS_IGUALES)).toEqual([...ordenar([A, B], PESOS_IGUALES), 'F', 'G', 'E', 'D'])
  })
})
