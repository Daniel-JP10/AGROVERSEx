// asistido por SI: Claude Code (Anthropic), prueba del orden por prioridades con los casos de contratos/prioridades_casos.json (gemelo_api §4, v1.2)
import { readFileSync } from 'node:fs'
import { describe, expect, it } from 'vitest'
import ejemplo from '../src/secciones/rotaciones/ejemplo_gemelo.json'
import type { SalidaOptimizacion } from '../src/secciones/rotaciones/gemelo'
import { DESLIZADORES, OBJETIVOS_DE, ordenar, ordenDelDocumento, PESOS_IGUALES, puntajes, SENTIDO, type Pesos } from '../src/secciones/rotaciones/ordenPrioridades'

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
  it('sobre el ejemplo, el orden usa la línea base y el frente y cambia con los pesos', () => {
    const doc = ejemplo as unknown as SalidaOptimizacion
    const ids = [doc.linea_base.id, ...doc.frente.map((e) => e.id)]
    const iguales = ordenDelDocumento(doc, PESOS_IGUALES)
    expect([...iguales].sort()).toEqual([...ids].sort())
    const soloSuelo = ordenDelDocumento(doc, { agua: 0, suelo: 5, insumos: 0, estabilidad_climatica: 0 })
    const soloEstab = ordenDelDocumento(doc, { agua: 0, suelo: 0, insumos: 0, estabilidad_climatica: 5 })
    expect(soloSuelo).not.toEqual(soloEstab)
  })
})
