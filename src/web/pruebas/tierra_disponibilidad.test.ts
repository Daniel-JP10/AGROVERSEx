// asistido por SI: Claude Code (Anthropic), prueba de que N_MESES y la disponibilidad de productos salen de meta.json y coinciden con manifiesto.json (D-037 O1)
import { readFileSync } from 'node:fs'
import { gunzipSync } from 'node:zlib'
import { join } from 'node:path'
import { describe, expect, it, vi } from 'vitest'

vi.stubGlobal('localStorage', { getItem: () => null, setItem: () => {} })

const { N_MESES, idDeMes, etiquetaMes } = await import('../src/tiempo/valor')
const { CALENDARIO, provisionalDesdeDe } = await import('../src/tiempo/huecos')
const { enRevision, textoEstado } = await import('../src/datos/estatico')

const PUBLICO = join(__dirname, '..', 'public', 'datos')
const leer = (f: string) => JSON.parse(readFileSync(join(PUBLICO, f), 'utf8'))
const meta = leer('meta.json')
const manifiesto = leer('manifiesto.json')
const matriz = (v: string) => JSON.parse(gunzipSync(readFileSync(join(PUBLICO, 'COL', `${v}_0.json.gz`))).toString('utf8'))

describe('disponibilidad desde meta.json', () => {
  it('meta y manifiesto cuentan la misma disponibilidad', () => {
    for (const [v, info] of Object.entries<any>(meta.variables)) {
      expect(manifiesto.variables[v].meses_disponibles, v).toEqual(info.meses_disponibles)
      expect(manifiesto.variables[v].productos, v).toEqual(info.productos)
    }
    expect(manifiesto.n_meses).toBe(meta.n_meses)
    expect(manifiesto.mes0).toBe(meta.mes0)
  })
  it('N_MESES termina en el último mes con producto de meta, no en el del eje de los archivos', () => {
    const ultimo = Math.max(...Object.values<any>(meta.variables).map((v) => v.meses_disponibles.hasta).map(idDeMes))
    expect(N_MESES - 1).toBe(ultimo)
    expect(etiquetaMes(N_MESES - 1)).toBe(Object.values<any>(meta.variables).map((v) => v.meses_disponibles.hasta).sort().at(-1))
    expect(N_MESES).toBeLessThanOrEqual(meta.n_meses)
  })
  it('cada producto con archivo estático toma inicio y fin de meta', () => {
    const por = { imerg: 'precip', merra2: 't2m', gldas: 'sm_raiz', mod13: 'ndvi' } as const
    for (const [k, v] of Object.entries(por)) {
      const d = meta.variables[v].meses_disponibles
      expect(CALENDARIO[k].inicio, k).toBe(idDeMes(d.desde))
      expect(CALENDARIO[k].fin, k).toBe(idDeMes(d.hasta))
    }
  })
  it('el mes provisional de IMERG sale de la matriz real y es el primero con producto Late', () => {
    const m = matriz('precip')
    const i = provisionalDesdeDe(m)!
    expect(m.productos[m.producto_mes[i]].estado).toBe('provisional')
    expect(m.productos[m.producto_mes[i - 1]].estado).toBe('final')
    expect(i).toBe(309) // oct-2025: lo que antes afirmaba tiempo.test.ts a mano
    expect(provisionalDesdeDe(matriz('t2m'))).toBeUndefined() // MERRA-2 es todo final
  })
})

describe('enero y febrero de 2026 en revisión (D-033, hallazgo de lluvia)', () => {
  const e = (m: string) => idDeMes(m)
  it('precip marca 2026-01 y 2026-02 y no sus vecinos ni otras variables', () => {
    expect(enRevision('precip', e('2026-01'))).toBe(true)
    expect(enRevision('precip', e('2026-02'))).toBe(true)
    expect(enRevision('precip', e('2025-12'))).toBe(false)
    expect(enRevision('precip', e('2026-03'))).toBe(false)
    expect(enRevision('t2m', e('2026-02'))).toBe(false)
  })
  it('esos meses salen provisionales y en revisión en pantalla', () => {
    for (const m of ['2026-01', '2026-02']) expect(textoEstado('provisional', 'precip', e(m))).toMatch(/revis|review/i)
    expect(textoEstado('provisional', 'precip', e('2026-03'))).not.toMatch(/revis|review/i)
  })
  it('ambos meses tienen producto provisional en la matriz', () => {
    const m = matriz('precip')
    for (const mes of ['2026-01', '2026-02']) expect(m.productos[m.producto_mes[e(mes)]].estado, mes).toBe('provisional')
  })
})
