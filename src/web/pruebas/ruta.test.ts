// asistido por SI: Claude Code (Anthropic), pruebas de las rutas por hash y de la navegación del universo
import { createElement } from 'react'
import { renderToStaticMarkup } from 'react-dom/server'
import { describe, expect, it } from 'vitest'
import { SECCIONES, aHash, leerRuta } from '../src/app/ruta'
import { Navegacion } from '../src/app/Navegacion'
import { enEspanol } from './idioma_es'
enEspanol()

describe('rutas por hash', () => {
  it('las siete rutas del contrato §3 se leen y se escriben', () => {
    const esperado = ['', 'tierra', 'gemelo', 'rotaciones', 'ciencia', 'datos', 'fuentes']
    expect([...SECCIONES].map((s) => aHash({ seccion: s, params: {} }))).toEqual(esperado.map((e) => `#/${e}`))
    SECCIONES.forEach((s, i) => expect(leerRuta(`#/${esperado[i]}`).seccion).toBe(s))
  })
  it('la ruta vacía o desconocida va a la portada', () => {
    for (const h of ['', '#', '#/', '#/nada', '#/tierra/otra', '#tierra']) expect(leerRuta(h).seccion, h).toBe('portada')
  })
  it('lee los parámetros que admite cada sección y descarta el resto', () => {
    expect(leerRuta('#/tierra?unidad=COL-ADM1-x&variable=sm&mes=2024-03&lote=DEMO-COL-01')).toEqual({
      seccion: 'tierra', params: { unidad: 'COL-ADM1-x', variable: 'sm', mes: '2024-03' },
    })
    expect(leerRuta('#/rotaciones?unidad=USA-ADM2-1&lote=DEMO-USA-01&mes=2024-03').params).toEqual({ unidad: 'USA-ADM2-1', lote: 'DEMO-USA-01' })
    expect(leerRuta('#/gemelo?lote=DEMO-COL-02').params).toEqual({ lote: 'DEMO-COL-02' })
    expect(leerRuta('#/ciencia?lote=x').params).toEqual({})
  })
  it('escribir y leer devuelve la misma ruta, con valores codificados', () => {
    const r = { seccion: 'rotaciones' as const, params: { unidad: 'COL-ADM1-a b&c', lote: 'DEMO-COL-01' } }
    expect(aHash(r)).toBe('#/rotaciones?unidad=COL-ADM1-a+b%26c&lote=DEMO-COL-01')
    expect(leerRuta(aHash(r))).toEqual(r)
  })
})

describe('navegación', () => {
  it('enlaza las siete secciones y marca solo la actual con aria-current', () => {
    for (const s of SECCIONES) {
      const html = renderToStaticMarkup(createElement(Navegacion, { actual: s }))
      expect((html.match(/<a /g) ?? []).length).toBe(7)
      expect((html.match(/aria-current="page"/g) ?? []).length).toBe(1)
      expect(html).toMatch(new RegExp(`href="${aHash({ seccion: s, params: {} })}"[^>]*aria-current="page"`))
    }
    expect(renderToStaticMarkup(createElement(Navegacion, { actual: 'datos' }))).toContain('Datos abiertos')
  })
})
