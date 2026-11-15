// asistido por SI: Claude Code (Anthropic), pruebas de la sección El lote con los paquetes reales de public/gemelo y public/lotes
import { readFileSync } from 'node:fs'
import { join } from 'node:path'
import { createElement as h } from 'react'
import { renderToStaticMarkup } from 'react-dom/server'
import { describe, expect, it } from 'vitest'
import { cargarLote, escenariosDe, loteDeHash, type EstadoLote, type LoteJson, type Simulacion } from '../src/secciones/lote/datos'
import { tresPrimeras, VistaLote } from '../src/secciones/lote/Lote'
import { ordenar, PESOS_IGUALES } from '../src/secciones/rotaciones/ordenPrioridades'
import { t } from '../src/textos/i18n'

const PUB = join(__dirname, '..', 'public')
const leer = <T,>(r: string): T => JSON.parse(readFileSync(join(PUB, r), 'utf8'))
const LOTES = ['DEMO-COL-01', 'DEMO-USA-01']

function listo(lote: string, esc = 'historico'): Extract<EstadoLote, { estado: 'listo' }> {
  const l = leer<LoteJson>(`gemelo/${lote}/lote.json`)
  const ruta = l.escenarios[esc]?.simulacion ?? l.escenarios_enso[esc].simulacion
  return {
    estado: 'listo', lote: l, sim: leer<Simulacion>(`gemelo/${ruta}`), cat: leer('gemelo/textos/en.json'),
    relieve: leer<{ lotes: Record<string, never> }>('lotes/relieve_lotes.json').lotes[lote], perfil: leer(`lotes/perfil_${lote}.json`),
  }
}
const vista = (d: EstadoLote, lote = 'DEMO-COL-01') => renderToStaticMarkup(h(VistaLote, { estado: d, loteId: lote, escenario: 'historico', setEscenario: () => {} }))
const texto = (html: string) => html.replace(/<[^>]*>/g, ' ').replace(/&#x27;/g, "'").replace(/&amp;/g, '&')

describe('3 primeras estrategias (D-039)', () => {
  it('COL histórico: C, B, D, como prioridades.pesos_iguales.orden', () => {
    expect(tresPrimeras(listo('DEMO-COL-01').sim).map((e) => e.id)).toEqual(['C', 'B', 'D'])
  })
  for (const lote of LOTES) for (const esc of escenariosDe(leer<LoteJson>(`gemelo/${lote}/lote.json`))) {
    it(`${lote} ${esc}: el orden del paquete es el de la fórmula de Web con pesos iguales y la vista lo respeta`, () => {
      const d = listo(lote, esc)
      const web = ordenar(d.sim.estrategias.map((e) => ({ id: e.id, valores: d.sim.prioridades.valores[e.id] })), PESOS_IGUALES)
      expect(web).toEqual(d.sim.prioridades.pesos_iguales.orden)
      const ids = [...vista(d, lote).matchAll(/data-testid="estrategia-lote" data-id="(\w+)"/g)].map((m) => m[1])
      expect(ids).toEqual(d.sim.prioridades.pesos_iguales.orden.slice(0, 3))
    })
  }
})

describe('vista del lote', () => {
  const s = vista(listo('DEMO-COL-01'))
  it('muestra el gemelo con sus tres voces, el rótulo del paquete y en qué se basa', () => {
    for (const v of ['agua', 'helada', 'desnudo']) expect(s).toContain(`data-voz="${v}"`)
    expect(s).toContain('Model simulation with NASA POWER')
    expect(texto(s)).toContain(t('lote.base'))
    expect(s).toContain(t('lote.aviso_estacion'))
    expect(s).toContain('NASADEM_HGT v001')
  })
  it('selector con los 7 escenarios de lote.json', () => {
    const sel = s.slice(s.indexOf('aria-labelledby="h-escenario"><option'))
    expect((sel.slice(0, sel.indexOf('</select>')).match(/<option/g) ?? []).length).toBe(7)
  })
  it('cada tarjeta trae exposición erosiva y ET real con p10 a p90 y unidad', () => {
    expect((s.match(/data-indicador="indice_exposicion_erosiva"/g) ?? []).length).toBe(3)
    expect((s.match(/data-indicador="et_real_mm_anio"/g) ?? []).length).toBe(3)
    expect(s).toMatch(/\d+ \(\d+(\.\d+)?–\d+(\.\d+)?\) mm\/yr/)
    expect(s).toMatch(/\d(\.\d+)? \(\d(\.\d+)?–\d(\.\d+)?\) index/)
  })
  it('las etiquetas del bloque muestran el mes elegido con banda y unidad', () => {
    for (const v of ['agua_raiz', 'V', 'desnudo', 'P']) expect(s).toMatch(new RegExp(`data-variable="${v}"[^]*?data-banda`))
    expect(s).toContain('January')
  })
  it('pendiente rotulada con la media que usa factor_pendiente_mccool', () => {
    const py = readFileSync(join(__dirname, '..', '..', 'gemelo', 'entrada.py'), 'utf8')
    expect(py).toContain('"pendiente_m_m": float(x["relieve_nasadem_30m"]["pendiente_media_m_m"])')
    expect(s).toContain(t('lote.pendiente'))
  })
  it('sin carbono, ENSO, salud, Pred., SMAP ni calibración', () => {
    const x = texto(s)
    expect(x).not.toMatch(/carbon|t C\/ha|ONI|Lot health|Pred\.|SMAP|calibrat|IMERG/i)
  })
  it('cargando y sin dato no inventan números', () => {
    expect(texto(vista({ estado: 'cargando' }))).not.toMatch(/\d/)
    expect(texto(vista({ estado: 'sin_dato' }))).toContain(t('lote.no_disponible'))
  })
})

describe('lectura', () => {
  it('?lote= válido, inválido o ausente', () => {
    expect(loteDeHash('#/lote?lote=DEMO-USA-01')).toBe('DEMO-USA-01')
    expect(loteDeHash('#/lote?lote=../x')).toBe('DEMO-COL-01')
    expect(loteDeHash('#/lote')).toBe('DEMO-COL-01')
  })
  it('lee de public/gemelo y public/lotes; un id inválido no pide nada', async () => {
    const pedidas: string[] = []
    const pedir = async (u: string) => {
      pedidas.push(u)
      try { return new Response(readFileSync(join(PUB, u.replace(/^\//, '')), 'utf8')) } catch { return new Response('', { status: 404 }) }
    }
    const d = await cargarLote('DEMO-COL-01', 'enso_nino', 'en', pedir)
    expect(d.estado).toBe('listo')
    expect(pedidas).toContain('/gemelo/DEMO-COL-01/simulacion_enso_nino.json')
    expect(pedidas).toContain('/lotes/perfil_DEMO-COL-01.json')
    pedidas.length = 0
    expect((await cargarLote('DEMO-COL-01/../x', 'historico', 'en', pedir)).estado).toBe('sin_dato')
    expect(pedidas).toEqual([])
  })
})
