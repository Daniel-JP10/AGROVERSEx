// asistido por SI: Claude Code (Anthropic), pruebas de los huecos del guion leídos de archivos públicos de Datos y del Gemelo
import { describe, expect, it } from 'vitest'
import { cargarHuecos, resumenHls } from '../src/app/recorrido/cargarHuecos'
import { en } from '../src/textos/en'
import { es } from '../src/textos/es'
import { PASOS } from '../src/app/recorrido/pasos'

const ARCHIVOS: Record<string, unknown> = {
  '/datos/lotes_demo.json': { lotes: [{ lote_id: 'DEMO-USA-01', unidad_id: 'USA-ADM2-X' }, { lote_id: 'DEMO-COL-01', unidad_id: 'COL-ADM2-Y' }] },
  '/datos/meta.json': { variables: { precip: { meses_disponibles: { desde: '2000-01', hasta: '2026-10' } } } },
  '/datos/lotes/hls_validez_DEMO-COL-01.json': { meses: { '2022-01': { media: 0.1 }, '2022-02': { media: 0 }, '2022-03': { media: 0.2 } } },
  '/datos/lotes/hls_validez_DEMO-USA-01.json': { meses: { '2022-01': { media: 0.6 }, '2022-02': { media: 0.4 } } },
  '/datos/publicos/gemelo/indice.json': { lotes: [{ lote_id: 'DEMO-COL-01', escenarios: { historico: { optimizacion: 'C/opt.json' } }, calibraciones: [{ id: 'cualquiera', archivo: 'C/cal.json' }] }] },
  '/datos/publicos/gemelo/C/opt.json': { frente: [{}, {}, {}] },
}
const pedirDe = (a: Record<string, unknown>) => async (u: string) => (u in a ? new Response(JSON.stringify(a[u])) : new Response('no', { status: 404 }))

describe('huecos del guion', () => {
  it('resumenHls promedia la fracción válida mensual y da mínimo y máximo', () => {
    const r = resumenHls({ meses: { a: { media: 0.1 }, b: { media: null }, c: { media: 0.3 } } })!
    expect(r.media).toBeCloseTo(0.2)
    expect([r.min, r.max]).toEqual([0.1, 0.3])
    expect(resumenHls({ meses: {} })).toBeNull()
  })
  it('con todos los archivos llena cada hueco que piden los pasos del mundo y de Ipiales', async () => {
    const v = await cargarHuecos('en', pedirDe(ARCHIVOS))
    expect(v).toMatchObject({
      unidad_lote_eeuu: 'USA-ADM2-X', unidad_ipiales: 'COL-ADM2-Y', lote_ipiales: 'DEMO-COL-01', mes_inicio: '2000-01', mes_fin: '2026-10',
      hls_validos_ipiales: '10%', hls_ipiales_min: '0%', hls_ipiales_max: '20%', hls_validos_saunders: '50%',
      n_alternativas: '3',
    })
    for (const id of ['2.2', '3.1', '3.2']) for (const n of PASOS.find((p) => p.id === id)!.datos) expect(v[n], `${id} ${n}`).toBeDefined()
    // Web no elige calibración: el paso del agricultor queda sin dato y nunca se pide un archivo de calibración
    for (const n of PASOS.find((p) => p.id === '3.5')!.datos) expect(v[n], n).toBeUndefined()
  })
  it('una fuente que falta solo deja vacíos sus huecos', async () => {
    const sinHls = { ...ARCHIVOS }
    delete sinHls['/datos/lotes/hls_validez_DEMO-COL-01.json']
    const v = await cargarHuecos('en', pedirDe(sinHls))
    expect(v.hls_validos_ipiales).toBeUndefined()
    expect(v.hls_validos_saunders).toBe('50%')
    expect(v.mes_inicio).toBe('2000-01')
    expect(await cargarHuecos('en', pedirDe({}))).toEqual({})
  })
  it('ningún texto del recorrido usa acto ni encabezados numerados de ese tipo', () => {
    expect(Object.keys(en).some((k) => /^recorrido\.acto/.test(k))).toBe(false)
    const textos = [en, es].flatMap((d) => Object.entries(d).filter(([k]) => k.startsWith('recorrido.')).map(([, v]) => v as string))
    expect(textos.length).toBeGreaterThan(10)
    expect('Act two · x').toMatch(/\bacts?\b|\bactos?\b/i)
    for (const x of textos) expect(x).not.toMatch(/\bacts?\b|\bactos?\b/i)
  })
})
