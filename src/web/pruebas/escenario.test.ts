// asistido por SI: Claude Code (Anthropic), escritura y revisión de código; base del prototipo migrada en el hackatón
import { describe, expect, it, vi } from 'vitest'
import { limitarEscenario, percentil, sincronizarCamaras } from '../src/comparar/sincronia'

describe('limitarEscenario', () => {
  it('fuera del rango se recorta y se explica', () => {
    const r = limitarEscenario(120, 50, 100)
    expect(r).toMatchObject({ valor: 100, bloqueado: true })
    expect(r.motivo).toMatch(/p25-p75/)
    expect(limitarEscenario(10, 50, 100)).toMatchObject({ valor: 50, bloqueado: true })
  })
  it('dentro del rango no bloquea', () => {
    expect(limitarEscenario(70, 50, 100)).toEqual({ valor: 70, bloqueado: false })
  })
})

describe('percentil', () => {
  it('interpola e ignora null', () => {
    expect(percentil([1, null, 2, 3, 4, 5], 0.25)).toBe(2)
    expect(percentil([1, 2, 3, 4, 5], 0.75)).toBe(4)
    expect(percentil([null], 0.5)).toBeNull()
  })
})

// Mapa falso con bus de eventos mínimo
function falso() {
  const oy: Record<string, (() => void)[]> = {}
  const m = {
    jumpTo: vi.fn(() => { oy.move?.forEach((f) => f()) }), // jumpTo dispara move, como MapLibre
    getCenter: () => ({ lng: 1, lat: 2 }), getZoom: () => 3, getBearing: () => 0, getPitch: () => 0,
    on: vi.fn((e: string, f: () => void) => { (oy[e] ??= []).push(f) }),
    off: vi.fn((e: string, f: () => void) => { oy[e] = (oy[e] ?? []).filter((x) => x !== f) }),
    emit: (e: string) => oy[e]?.forEach((f) => f()),
  }
  return m
}
describe('sincronizarCamaras', () => {
  it('un evento hace un solo jumpTo, sin rebote', () => {
    const a = falso(), b = falso()
    const quitar = sincronizarCamaras(a as never, b as never)
    a.emit('move')
    expect(b.jumpTo).toHaveBeenCalledTimes(1)
    expect(a.jumpTo).toHaveBeenCalledTimes(0)
    b.emit('move')
    expect(a.jumpTo).toHaveBeenCalledTimes(1)
    quitar()
    a.emit('move')
    expect(b.jumpTo).toHaveBeenCalledTimes(1)
  })
})
