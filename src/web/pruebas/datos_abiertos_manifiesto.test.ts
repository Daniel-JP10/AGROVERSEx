// asistido por SI: Claude Code (Anthropic), pruebas de Datos abiertos (plan v2 §6): una tarjeta por archivo del manifiesto, licencia por archivo y notas D-038 y D-040
import { readFileSync } from 'node:fs'
import { createElement } from 'react'
import { renderToStaticMarkup } from 'react-dom/server'
import { afterEach, describe, expect, it } from 'vitest'
import { DatosAbiertos, REPO_TESELAS } from '../src/secciones/datos-abiertos/DatosAbiertos'
import { cargarManifiesto, desdeManifiesto, type Manifiesto } from '../src/secciones/datos-abiertos/manifiesto'
import { alternar, idioma } from '../src/textos/i18n'
import * as textos from '../src/textos/secciones/datos'

afterEach(() => { if (idioma() !== 'en') alternar() })

// Valores de prueba con la forma de public/datos/manifiesto.json
const SHA = 'a'.repeat(64)
const M: Manifiesto = {
  generado_utc: '2026-11-14T22:50:00Z',
  variables: { precip: { niveles: [0], meses_disponibles: { desde: '2000-01', hasta: '2026-10', n_meses_con_producto: 322 }, productos: [{ producto: 'IMERG Final', version: '07B', estado: 'final' }] } },
  archivos: { 'COL/precip_0.json.gz': { bytes: 2941, sha256: SHA }, '../fuera.json': { bytes: 1, sha256: SHA }, 'unidades_geo.json.gz': { bytes: 1236212, sha256: 'corto' }, 'meta.json': { bytes: 1717 } },
}
const html = (d: Parameters<typeof DatosAbiertos>[0]['datos']) => renderToStaticMarkup(createElement(DatosAbiertos, { datos: d }))

describe('datos abiertos desde el manifiesto', () => {
  it('una tarjeta por archivo seguro, con su tipo de licencia; las rutas con .. se descartan', () => {
    const d = desdeManifiesto(M, '/base/')
    expect(d.archivos.map((a) => [a.ruta, a.tipo])).toEqual([['COL/precip_0.json.gz', 'serie'], ['unidades_geo.json.gz', 'geometria'], ['meta.json', 'proyecto']])
    expect(d.archivos[0]).toMatchObject({ url: '/base/datos/COL/precip_0.json.gz', bytes: 2941, sha256: SHA, serie: { pais: 'COL', variable: 'precip', nivel: 0, desde: '2000-01', hasta: '2026-10', meses: 322 } })
    expect(d.archivos[1].sha256).toBeUndefined()
  })
  it('la tarjeta muestra variable, nivel, meses, producto, tamaño, SHA-256 y licencia; lo ausente dice Not available yet', () => {
    const h = html(desdeManifiesto(M, '/'))
    expect((h.match(/data-archivo=/g) ?? []).length).toBe(3)
    const serie = h.split('data-archivo="COL/precip_0.json.gz"')[1].split('</article>')[0]
    for (const x of ['Monthly rainfall', 'Country', '2000-01 to 2026-10 (322 months with product)', 'IMERG Final · 07B · final', SHA, 'NASA Earthdata data use policy', 'href="/datos/COL/precip_0.json.gz"']) expect(serie, x).toContain(x)
    expect(h.split('data-archivo="unidades_geo.json.gz"')[1]).toContain('ODbL 1.0')
    expect(h.split('data-archivo="meta.json"')[1].split('</article>')[0]).toContain('Not available yet')
  })
  it('notas fijas: paquetes del gemelo con el rótulo Model simulation, repo de teselas y GHCN fuera del dataset', () => {
    const h = html(desdeManifiesto(M, '/'))
    expect(h).toContain('Model simulation')
    expect(h).toContain(`href="${REPO_TESELAS}"`)
    expect(h).toContain('not part of this open dataset (decision D-038)')
  })
  it('sin manifiesto (404 o red caída) lo dice y no inventa archivos', async () => {
    expect(await cargarManifiesto(async () => new Response('no', { status: 404 }), '/')).toBeNull()
    expect(await cargarManifiesto(async () => { throw new Error('red') }, '/')).toBeNull()
    const h = html(null)
    expect(h).toContain('Not available yet')
    expect(h).not.toContain('data-archivo=')
  })
  it('lee el manifiesto real de public/: cada archivo listado tiene tarjeta con su huella', () => {
    const real = JSON.parse(readFileSync(new URL('../public/datos/manifiesto.json', import.meta.url), 'utf8')) as Manifiesto
    const d = desdeManifiesto(real, '/')
    expect(d.archivos.length).toBe(Object.keys(real.archivos ?? {}).length)
    const h = html(d)
    for (const [ruta, a] of Object.entries(real.archivos ?? {})) { expect(h, ruta).toContain(`data-archivo="${ruta}"`); if (a.sha256) expect(h).toContain(a.sha256) }
  })
  it('español completo y textos sin cifras escritas a mano (salvo D-0xx, Resolución 40 y SHA-256)', () => {
    alternar()
    expect(html(desdeManifiesto(M, '/'))).toContain('Lluvia mensual')
    for (const v of [...Object.values(textos.en), ...Object.values(textos.es)]) expect(v.replace(/\{\w+\}|D-0\d\d|Resolution 40|Resolución 40|SHA-256|ODbL 1\.0|CC BY 4\.0/g, ''), v).not.toMatch(/\d/)
  })
})
