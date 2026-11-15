// asistido por SI: Claude Code (Anthropic), pruebas de la lectura del paquete estático del gemelo v1.1 con un fetch falso
import { describe, expect, it } from 'vitest'
import ejemplo from '../src/secciones/rotaciones/ejemplo_gemelo.json'
import { cargarGemelo } from '../src/secciones/rotaciones/lector'

const LOTES = { version: 1, lotes: [{ lote_id: 'DEMO-COL-01', unidad_id: 'COL-ADM2-X', nombre: 'Lote DEMO' }] }
const INDICE = { textos: { en: 'textos/en.json', es: 'textos/es.json' }, lotes: [{ lote_id: 'DEMO-COL-01', escenarios: { historico: { optimizacion: 'DEMO-COL-01/optimizacion_historico.json' } } }] }
const CAT = { 'card.risk.local_review': 'Revisar con un agrónomo local.' }

// Sirve un mapa ruta -> cuerpo y anota cada URL pedida
function falso(archivos: Record<string, unknown>) {
  const pedidas: string[] = []
  const pedir = async (u: string) => {
    pedidas.push(u)
    return u in archivos ? new Response(JSON.stringify(archivos[u]), { status: 200 }) : new Response('no', { status: 404 })
  }
  return { pedir, pedidas }
}
const COMPLETO: Record<string, unknown> = {
  '/datos/lotes_demo.json': LOTES,
  '/datos/publicos/gemelo/indice.json': INDICE,
  '/datos/publicos/gemelo/DEMO-COL-01/optimizacion_historico.json': ejemplo,
  '/datos/publicos/gemelo/textos/es.json': CAT,
}

describe('cargarGemelo sin ejemplos', () => {
  it('lee lotes_demo.json, luego indice.json y luego la optimización histórica y el catálogo, relativo a la base', async () => {
    const { pedir, pedidas } = falso(COMPLETO)
    const f = await cargarGemelo('DEMO-COL-01', 'es', pedir)
    expect(f.estado).toBe('listo')
    if (f.estado !== 'listo') return
    expect(f.origen).toBe('modelo')
    expect(f.catalogo).toEqual(CAT)
    expect(f.doc.linea_base.id).toBe(ejemplo.linea_base.id)
    expect(pedidas.slice(0, 2)).toEqual(['/datos/lotes_demo.json', '/datos/publicos/gemelo/indice.json'])
    expect(pedidas.slice(2).sort()).toEqual(['/datos/publicos/gemelo/DEMO-COL-01/optimizacion_historico.json', '/datos/publicos/gemelo/textos/es.json'])
  })
  it('un id que no es DEMO-XXX-NN no pide nada', async () => {
    for (const id of ['../../etc', 'DEMO-COL-1', 'demo-col-01', 'DEMO-COL-01/../x']) {
      const { pedir, pedidas } = falso(COMPLETO)
      expect((await cargarGemelo(id, 'es', pedir)).estado, id).toBe('sin_dato')
      expect(pedidas, id).toEqual([])
    }
  })
  it('un lote que no está en lotes_demo.json o en indice.json da sin_dato', async () => {
    expect((await cargarGemelo('DEMO-USA-01', 'es', falso(COMPLETO).pedir)).estado).toBe('sin_dato')
    const sinIndice = { ...COMPLETO, '/datos/publicos/gemelo/indice.json': { ...INDICE, lotes: [] } }
    expect((await cargarGemelo('DEMO-COL-01', 'es', falso(sinIndice).pedir)).estado).toBe('sin_dato')
  })
  it('una ruta de indice.json que sube de carpeta no se pide', async () => {
    const malo = { ...COMPLETO, '/datos/publicos/gemelo/indice.json': { ...INDICE, lotes: [{ lote_id: 'DEMO-COL-01', escenarios: { historico: { optimizacion: '../../secreto.json' } } }] } }
    const { pedir, pedidas } = falso(malo)
    expect((await cargarGemelo('DEMO-COL-01', 'es', pedir)).estado).toBe('sin_dato')
    expect(pedidas.some((u) => u.includes('secreto'))).toBe(false)
  })
  it('un archivo ausente (404) da sin_dato sin romper', async () => {
    const sinTextos = { ...COMPLETO }
    delete sinTextos['/datos/publicos/gemelo/textos/es.json']
    expect((await cargarGemelo('DEMO-COL-01', 'es', falso(sinTextos).pedir)).estado).toBe('sin_dato')
    expect((await cargarGemelo('DEMO-COL-01', 'es', falso({}).pedir)).estado).toBe('sin_dato')
  })
})
