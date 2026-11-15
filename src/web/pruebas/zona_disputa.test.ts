// asistido por SI: Claude Code (Anthropic), pruebas de zonas en disputa (es_disputa = 1)
import { describe, expect, it } from 'vitest'
import { NIVELES, capasNivel, capasInteractivas, esDisputa, nombreUnidad } from '../src/globo/config'
import { porClave, claveUnidad, cargarFilas } from '../src/datos/indice'
import { t } from '../src/textos/i18n'

// propiedades reales de una tesela CGAZ: iso3 '111' (Abyei), es_disputa 1
const abyei = { id: '111-ADM0', iso3: '111', nivel: 0, nombre: 'Abyei', es_disputa: 1 }
const colombia = { id: 'COL-ADM0', iso3: 'COL', nivel: 0, nombre: 'Colombia', es_disputa: 0 }

describe('zona en disputa', () => {
  it('detecta es_disputa = 1 y no otra cosa', () => {
    expect(esDisputa(abyei)).toBe(true)
    expect(esDisputa(colombia)).toBe(false)
    expect(esDisputa({ iso3: '111' })).toBe(true) // teselas sin es_disputa
    expect(esDisputa({ iso3: 'ESH' })).toBe(true)
    expect(esDisputa({ iso3: 'COL' })).toBe(false)
    expect(esDisputa({ iso3: '130' })).toBe(false)
    expect(esDisputa({})).toBe(false)
    expect(esDisputa(undefined)).toBe(false)
  })
  it('nunca muestra el nombre ni el código como país', () => {
    expect(nombreUnidad(abyei.nombre, true)).toBe(t('unidad.disputa'))
    expect(nombreUnidad(abyei.nombre, true)).not.toContain('111')
    expect(nombreUnidad('Colombia', false)).toBe('Colombia')
  })
  it('hay clave de texto en inglés y español', () => {
    expect(t('unidad.disputa')).not.toBe('unidad.disputa')
  })
  it('las tres capas filtran la disputa y tienen trama', () => {
    for (const c of NIVELES) {
      const capas = capasNivel(c) as { id: string; filter?: unknown; paint?: Record<string, unknown> }[]
      const d = capas.find((l) => l.id === `${c.fuente}-disputa`)
      expect(d, c.fuente).toBeTruthy()
      expect(JSON.stringify(d!.filter)).toContain('es_disputa')
      expect(d!.paint!['fill-pattern']).toBe('trama')
      expect(JSON.stringify(capas.find((l) => l.id === `${c.fuente}-relleno`)!.filter)).toContain('es_disputa')
    }
    expect(JSON.stringify(capasNivel(NIVELES[0]))).not.toContain('"nivel"],9')
  })
  it('la capa en disputa se puede consultar para mostrar "Zona en disputa"', () => {
    expect(capasInteractivas(0)).toContain('adm0-disputa')
  })
  it('el índice marca la disputa con d: 1', async () => {
    const orig = globalThis.fetch
    const fila = [{ id: '111-ADM0', nivel: 0, n: 'Abyei', a: 'abyei', ctx: 'Zona en disputa', d: 1 }]
    const gz = new Response(new Blob([JSON.stringify(fila)]).stream().pipeThrough(new CompressionStream('gzip')))
    globalThis.fetch = (() => Promise.resolve(gz)) as never
    await cargarFilas()
    globalThis.fetch = orig
    expect(porClave.get(claveUnidad(0, '111-ADM0'))?.disputa).toBe(true)
  })
})
