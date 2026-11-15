// asistido por SI: Claude Code (Anthropic), escritura y revisión de código; base del prototipo migrada en el hackatón
import { describe, expect, it } from 'vitest'
import { nivelesARecolorear, crearCola } from '../src/globo/recoloreo'
import { SIN_ADM1, SIN_ADM2 } from '../src/globo/config'

describe('selección de niveles a recolorear', () => {
  it('nivel 0: solo países, sin respaldos', () => {
    expect(nivelesARecolorear(0)).toEqual([{ nivel: 0, paises: null }])
  })
  it('nivel 1: adm1 entero y adm0 solo para los países sin ADM1', () => {
    expect(nivelesARecolorear(1)).toEqual([{ nivel: 0, paises: SIN_ADM1 }, { nivel: 1, paises: null }])
  })
  it('nivel 2: adm2 entero y respaldos de adm0 y adm1 solo para países sin nivel inferior', () => {
    expect(nivelesARecolorear(2)).toEqual([{ nivel: 0, paises: SIN_ADM1 }, { nivel: 1, paises: SIN_ADM2 }, { nivel: 2, paises: null }])
  })
  it('nunca selecciona niveles mayores al activo', () => {
    for (const a of [0, 1, 2]) expect(nivelesARecolorear(a).every((x) => x.nivel <= a)).toBe(true)
  })
})

describe('cola de recoloreo durante gestos', () => {
  it('sin gesto pinta de inmediato', () => {
    const p: number[] = []
    const c = crearCola((m) => p.push(m))
    c.pedir(3); c.pedir(4)
    expect(p).toEqual([3, 4])
  })
  it('durante el gesto no pinta; al terminar pinta solo el último mes pedido', () => {
    const p: number[] = []
    const avisos: boolean[] = []
    const c = crearCola((m) => p.push(m), (h) => avisos.push(h))
    c.inicioGesto()
    c.pedir(1); c.pedir(2); c.pedir(3)
    expect(p).toEqual([])
    expect(c.pendiente).toBe(3)
    c.finGesto()
    expect(p).toEqual([3])
    expect(c.pendiente).toBeNull()
    expect(avisos).toContain(true)
  })
  it('un gesto sin meses pedidos no pinta nada', () => {
    const p: number[] = []
    const c = crearCola((m) => p.push(m))
    c.inicioGesto(); c.finGesto()
    expect(p).toEqual([])
  })
})
