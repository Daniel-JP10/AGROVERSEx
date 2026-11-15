// asistido por SI: Claude Code (Anthropic), pruebas de la ficha de Datos abiertos leída del manifiesto de web_datos v0
import { createElement } from 'react'
import { renderToStaticMarkup } from 'react-dom/server'
import { describe, expect, it } from 'vitest'
import { DatosAbiertos, type FichaDatos } from '../src/secciones/datos-abiertos/DatosAbiertos'
import { cargarManifiesto, fichaDesdeManifiesto, type Manifiesto } from '../src/secciones/datos-abiertos/manifiesto'
import { t } from '../src/textos/i18n'

// Misma forma que src/web/public/datos/manifiesto.json de la rama datos; valores de prueba
const SHA = 'a'.repeat(64)
const M: Manifiesto = {
  version_contrato: 'web_datos v0',
  paises: ['COL'],
  variables: {
    precip: { meses_disponibles: { desde: '2000-01', hasta: '2026-10' }, productos: [{ producto: 'IMERG Final', version: '07B', estado: 'final' }] },
    ndvi: { meses_disponibles: { desde: '2000-02', hasta: '2026-11' }, productos: [{ producto: 'MOD13C2', version: '061', estado: 'final' }] },
  },
  archivos: { 'COL/precip_0.json.gz': { bytes: 10, sha256: SHA }, '../fuera.json': { bytes: 1, sha256: SHA }, 'lotes_demo.json': { bytes: 5, sha256: 'corto' } },
}

describe('ficha desde el manifiesto', () => {
  it('toma periodo, variables, cobertura y descargas del manifiesto, relativas a la base', () => {
    const f = fichaDesdeManifiesto(M, '/base/')
    expect(f.campos?.periodo).toBe('2000-01 – 2026-11')
    expect(f.campos?.cobertura).toBe('COL')
    expect(f.campos?.variables).toContain('precip: IMERG Final · 07B · final')
    expect(f.descargas?.map((d) => d.url)).toEqual(['/base/datos/COL/precip_0.json.gz', '/base/datos/lotes_demo.json'])
    expect(f.descargas?.[0].sha256).toBe(SHA)
    expect(f.descargas?.[1].sha256).toBeUndefined()
  })
  it('lo que web_datos v0 no trae queda sin dato: licencia, atribuciones, cita y comando', () => {
    const h = renderToStaticMarkup(createElement<FichaDatos>(DatosAbiertos, fichaDesdeManifiesto(M, '/')))
    for (const c of ['licencia', 'atribuciones', 'cita']) expect(h).toMatch(new RegExp(`data-campo="${c}"><dt>[^<]*</dt><dd><span class="sin-dato">`))
    expect(h).not.toContain('<pre>')
    expect(h).toContain('href="/datos/COL/precip_0.json.gz"')
    expect(h).toContain(t('datos.huella'))
  })
  it('un enlace del mismo sitio fuera de datos/ o con .. no se pinta', () => {
    const h = renderToStaticMarkup(createElement<FichaDatos>(DatosAbiertos, { descargas: [{ nombre: 'x', url: '/otra/x.json' }, { nombre: 'y', url: '/datos/../y' }, { nombre: 'z', url: '//malo.example/datos/z' }] }))
    expect(h).not.toContain('<a ')
  })
  it('sin manifiesto (404 o red caída) la ficha queda vacía y no rompe', async () => {
    expect(await cargarManifiesto(async () => new Response('no', { status: 404 }), '/')).toEqual({})
    expect(await cargarManifiesto(async () => { throw new Error('red') }, '/')).toEqual({})
  })
  it('con manifiesto pide datos/manifiesto.json bajo la base', async () => {
    const pedidas: string[] = []
    const f = await cargarManifiesto(async (u) => { pedidas.push(u); return new Response(JSON.stringify(M)) }, '/base/')
    expect(pedidas).toEqual(['/base/datos/manifiesto.json'])
    expect(f.campos?.cobertura).toBe('COL')
  })
})
