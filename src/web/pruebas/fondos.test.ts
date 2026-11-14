// asistido por SI: Claude Code (Anthropic), escritura y revisión de código; base del prototipo migrada en el hackatón
import { describe, expect, it } from 'vitest'
import { FONDOS, fondoBase, fondoDetalle } from '../src/globo/fondos'
import { construirEstilo, ATRIBUCION } from '../src/globo/config'

describe('fondos', () => {
  it('todo fondo declara licencia, atribución y token', () => {
    for (const f of FONDOS) {
      expect(f.licencia).not.toBe('')
      expect(f.atribucion.trim()).not.toBe('')
      expect(typeof f.requiereToken).toBe('boolean')
    }
  })
  it('el detalle por defecto no requiere token y Blue Marble es el respaldo', () => {
    expect(fondoDetalle(true)?.requiereToken).toBe(false)
    expect(fondoBase().id).toBe('bluemarble')
  })
  it('sin red no hay fondo de detalle', () => {
    expect(fondoDetalle(false)).toBeNull()
    expect(fondoDetalle(true, 'inexistente')).toBeNull()
  })
  it('el estilo apila Blue Marble abajo y detalle encima; sin red solo Blue Marble', () => {
    const ids = (e: any) => e.layers.map((l: any) => l.id)
    const on = ids(construirEstilo('http://x', true))
    expect(on.indexOf('bluemarble')).toBeLessThan(on.indexOf('detalle'))
    expect(on.indexOf('detalle')).toBeLessThan(on.indexOf('adm0-relleno'))
    expect(ids(construirEstilo('http://x', false))).not.toContain('detalle')
  })
  it('la atribución visible exige el texto de NASA GIBS (ESDIS)', () => {
    expect(ATRIBUCION).toContain("NASA's Global Imagery Browse Services (GIBS)")
    expect(ATRIBUCION).toContain('ESDIS')
  })
  it('ninguna URL ni texto de fondo menciona EOX ni cloudless', () => {
    const todo = JSON.stringify(FONDOS).toLowerCase() + ATRIBUCION.toLowerCase()
    expect(todo).not.toMatch(/eox|cloudless/)
    for (const f of FONDOS) for (const u of f.tiles) expect(u).toContain('gibs.earthdata.nasa.gov')
  })
  it('el fondo por defecto es un mosaico sin fecha y la fuente usa el zoom nativo', () => {
    const det = fondoDetalle(true)!
    for (const u of [...det.tiles, ...fondoBase().tiles]) expect(u).not.toMatch(/\d{4}-\d{2}-\d{2}/)
    const fuentes = (construirEstilo('http://x', true) as any).sources
    expect(fuentes.detalle.maxzoom).toBe(det.maxzoom)
    expect(det.maxzoom).toBe(8)
    expect(fuentes.bluemarble.maxzoom).toBe(fondoBase().maxzoom)
  })
  it('la capa MODIS de un día existe solo como opción, no por defecto', () => {
    expect(FONDOS.some((f) => f.id === 'gibs-modis-terra' && f.maxzoom === 9)).toBe(true)
    expect(fondoDetalle(true)!.id).not.toBe('gibs-modis-terra')
  })
})
