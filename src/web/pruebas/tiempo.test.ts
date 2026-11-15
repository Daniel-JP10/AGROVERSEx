// asistido por SI: Claude Code (Anthropic), escritura y revisión de código; base del prototipo migrada en el hackatón
import { describe, expect, it, vi } from 'vitest'
import { crearReproductor } from '../src/tiempo/Reproductor'
import { CALENDARIO, mesIdAEtiqueta, mesesConHueco } from '../src/tiempo/huecos'
import { enEspanol } from './idioma_es'

enEspanol() // las aserciones son en español y el idioma por defecto es el inglés (D-039)

describe('etiquetas y huecos', () => {
  it('mesIdAEtiqueta', () => {
    expect(mesIdAEtiqueta(0)).toBe('ene-2000')
    expect(mesIdAEtiqueta(322)).toBe('nov-2026')
  })
  it('SMAP: feb-2015 (mes 181) sin dato, mar-2015 (182) con dato, hueco jun-2019', () => {
    const h = mesesConHueco(CALENDARIO.smap_l3)
    expect(h).toContain(181)
    expect(h).not.toContain(182)
    expect(h).not.toContain(233) // jun-2019 es parcial: no se sombrea entero
    expect(h.filter((m) => m < 182)).toHaveLength(182)
  })
  it('GRACE: 33 meses sin solución dentro de su rango', () => {
    const g = CALENDARIO.grace
    const dentro = mesesConHueco(g).filter((m) => m >= g.inicio && m <= g.fin)
    expect(dentro).toHaveLength(33)
  })
  it('IMERG: provisional desde oct-2025 (mes 309), sin sombrear', () => {
    expect(CALENDARIO.imerg.provisionalDesde).toBe(309)
    expect(mesesConHueco(CALENDARIO.imerg)).toEqual([])
  })
})

describe('reproductor', () => {
  it('se detiene en 322 y precarga los 12 siguientes', async () => {
    vi.useFakeTimers()
    const vistos: number[] = []
    const pre: [number, number][] = []
    const r = crearReproductor({ velocidad: 4, siguiente: async (m) => { vistos.push(m) }, precargar: (a, b) => pre.push([a, b]) })
    r.irA(319)
    r.play()
    await vi.advanceTimersByTimeAsync(5000)
    expect(vistos).toEqual([320, 321, 322])
    expect(pre[0]).toEqual([321, 322])
    r.irA(0); r.play(); await vi.advanceTimersByTimeAsync(260)
    expect(pre.at(-1)).toEqual([3, 14])
    r.pausa(); vi.useRealTimers()
  })
  it('con siguiente lento hay a lo sumo 1 petición en vuelo', async () => {
    vi.useFakeTimers()
    let vuelo = 0, maximo = 0
    const r = crearReproductor({ velocidad: 4, precargar: () => {}, siguiente: async () => {
      maximo = Math.max(maximo, ++vuelo); await new Promise((f) => setTimeout(f, 1000)); vuelo--
    } })
    r.play(); await vi.advanceTimersByTimeAsync(5000); r.pausa()
    expect(maximo).toBe(1)
    vi.useRealTimers()
  })
  it('pausar cancela la precarga y el avance', async () => {
    vi.useFakeTimers()
    const pre = vi.fn(), sig = vi.fn(async () => {})
    const r = crearReproductor({ velocidad: 4, siguiente: sig, precargar: pre })
    r.play(); await vi.advanceTimersByTimeAsync(300); r.pausa()
    const n = pre.mock.calls.length, s = sig.mock.calls.length
    await vi.advanceTimersByTimeAsync(3000)
    expect(pre.mock.calls.length).toBe(n); expect(sig.mock.calls.length).toBe(s)
    vi.useRealTimers()
  })
})
