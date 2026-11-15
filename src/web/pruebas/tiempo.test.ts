// asistido por SI: Claude Code (Anthropic), escritura y revisión de código; base del prototipo migrada en el hackatón
import { describe, expect, it, vi } from 'vitest'
import { N_MESES } from '../src/tiempo/valor'
import { crearReproductor } from '../src/tiempo/Reproductor'
import { CALENDARIO, mesIdAEtiqueta, mesesConHueco } from '../src/tiempo/huecos'
import { CAPAS } from '../src/datos/capas'
import meta from '../public/datos/meta.json'
import { enEspanol } from './idioma_es'

enEspanol() // las aserciones son en español y el idioma por defecto es el inglés (D-039)

describe('etiquetas y huecos', () => {
  it('mesIdAEtiqueta', () => {
    expect(mesIdAEtiqueta(0)).toBe('ene-2000')
    expect(mesIdAEtiqueta(322)).toBe('nov-2026')
  })
  // Director 08:55 (O1/C-3): un producto sin meta no se ofrece; lo disponible es lo del manifiesto y meta.json
  // (sustituye a las pruebas de SMAP y GRACE, que afirmaban cotas escritas a mano de productos sin archivo)
  it('el calendario solo ofrece productos con meta: los de las capas con archivo estático', () => {
    expect(Object.keys(CALENDARIO).sort()).toEqual([...new Set(CAPAS.map((c) => c.calendario))].sort())
    for (const c of CAPAS) expect(Object.keys(meta.variables), c.id).toContain(c.id)
  })
  it('la etiqueta del primer mes sale de meta.mes0', () => {
    expect(mesIdAEtiqueta(0).endsWith(`-${meta.mes0.slice(0, 4)}`)).toBe(true)
  })
  // O1 (D-037): el mes provisional de IMERG ya no está escrito a mano; sale de la matriz (309 = oct-2025, ver tierra_disponibilidad.test.ts)
  it('IMERG: sin sombrear y sin mes provisional fijo en el calendario', () => {
    expect(CALENDARIO.imerg.provisionalDesde).toBeUndefined()
    expect(mesesConHueco(CALENDARIO.imerg)).toEqual([])
  })
})

describe('reproductor', () => {
  // O1 (D-037): el último mes es N_MESES - 1 (321 con meta.json actual), no 322 escrito a mano
  it('se detiene en el último mes y precarga los 12 siguientes', async () => {
    vi.useFakeTimers()
    const vistos: number[] = []
    const pre: [number, number][] = []
    const r = crearReproductor({ velocidad: 4, siguiente: async (m) => { vistos.push(m) }, precargar: (a, b) => pre.push([a, b]) })
    r.irA(N_MESES - 4)
    r.play()
    await vi.advanceTimersByTimeAsync(5000)
    expect(vistos).toEqual([N_MESES - 3, N_MESES - 2, N_MESES - 1])
    expect(pre[0]).toEqual([N_MESES - 2, N_MESES - 1])
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
