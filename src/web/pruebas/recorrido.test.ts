// asistido por SI: Claude Code (Anthropic), pruebas del recorrido guiado, los huecos de datos y la portada
import { createElement } from 'react'
import { renderToStaticMarkup } from 'react-dom/server'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { PASOS, type Valor } from '../src/app/recorrido/pasos'
import { ejecutar } from '../src/app/recorrido/acciones'
import { useRecorrido } from '../src/app/recorrido/estado'
import { PanelRecorrido, Recorrido, TextoPaso } from '../src/app/recorrido/Recorrido'
import { SECCIONES } from '../src/app/ruta'
import { rellenar } from '../src/textos/huecos'
import { en, type ClaveTexto } from '../src/textos/en'
import { es } from '../src/textos/es'
import { alternar, idioma, t } from '../src/textos/i18n'

// la interfaz del globo importa el almacén de Daniel, que lee localStorage al cargarse; en node no existe
vi.hoisted(() => vi.stubGlobal('localStorage', { getItem: () => null, setItem: () => {} }))

const IPIALES ='COL-ADM2-7082276B52108893597118'
const sinEtiquetas = (h: string) => h.replace(/<[^>]*>/g, '').replace(/&#x27;/g, "'")
const marcadores = (txt: string) => [...txt.matchAll(/\{(\w+)\}/g)].map((m) => m[1])
const datosDe = (v: Valor | undefined) => (typeof v === 'object' ? [v.dato] : [])
const enAmbosIdiomas = (fn: () => void) => { fn(); alternar(); try { fn() } finally { alternar() } }

describe('pasos del guion', () => {
  it('son los dieciséis del guion, en orden, sobre rutas que existen', () => {
    expect(PASOS.map((p) => p.id)).toEqual(['1.1', '1.2', '1.3', '1.4', '2.1', '2.2', '2.3', '2.4', '3.1', '3.2', '3.3', '3.4', '3.5', '3.6', '4.1', '4.2'])
    for (const p of PASOS) expect(SECCIONES, p.id).toContain(p.ruta)
  })
  it('cada paso tiene texto en inglés y en español', () => {
    for (const p of PASOS) { expect(en[p.texto], p.id).toBeTruthy(); expect(es[p.texto], p.id).toBeTruthy() }
  })
  it('todo hueco del texto y de las acciones está en la lista de datos del paso', () => {
    for (const p of PASOS) {
      const usados = [
        ...marcadores(en[p.texto]), ...marcadores(es[p.texto] ?? ''),
        ...Object.values(p.params ?? {}).flatMap(datosDe),
        ...(p.acciones ?? []).flatMap((a) => ('unidad' in a ? datosDe(a.unidad) : 'variable' in a ? datosDe(a.variable) : 'mes' in a ? datosDe(a.mes) : [])),
      ]
      for (const u of usados) expect(p.datos, `${p.id} {${u}}`).toContain(u)
    }
  })
  it('ningún texto de paso lleva un dígito escrito a mano', () => {
    // los nombres de los huecos pueden llevar dígitos (acierto_p10); el texto fijo no
    const fijo = (x: string) => x.replace(/\{\w+\}/g, '')
    for (const p of PASOS) { expect(fijo(en[p.texto]), p.id).not.toMatch(/\d/); expect(fijo(es[p.texto]!), p.id).not.toMatch(/\d/) }
  })
})

describe('huecos de datos', () => {
  it('rellena con el valor y deja hueco con el nombre cuando falta', () => {
    const r = rellenar('a {x} b {y}', (n) => (n === 'x' ? '1' : undefined))
    expect(r.partes).toEqual([{ t: 'texto', v: 'a ' }, { t: 'valor', v: '1' }, { t: 'texto', v: ' b ' }, { t: 'hueco', v: 'y' }])
    expect(r.faltan).toEqual(['y'])
  })
  it('un texto sin marcadores no tiene huecos', () => {
    expect(rellenar('sin nada', () => 'z')).toEqual({ partes: [{ t: 'texto', v: 'sin nada' }], faltan: [] })
  })
})

describe('recorrido sin datos', () => {
  it('cada paso con datos pendientes muestra aviso.sin_dato y ninguno muestra un dígito', () => {
    enAmbosIdiomas(() => {
      for (const p of PASOS) {
        const html = renderToStaticMarkup(createElement(TextoPaso, { paso: p }))
        const pendientes = p.datos.filter((n) => n !== 'unidad_ipiales')
        expect(sinEtiquetas(html), `${p.id} ${idioma()}`).not.toMatch(/\d/)
        if (pendientes.length) expect(html, `${p.id} ${idioma()}`).toContain(t('aviso.sin_dato'))
        else expect(html, `${p.id} ${idioma()}`).not.toContain(t('aviso.sin_dato'))
      }
    })
  })
  it('con una fuente que entrega los datos el paso muestra los valores y no el aviso', () => {
    const resolver = (n: string) => `Z${n.replace(/_/g, '')}`
    const p = PASOS.find((x) => x.id === '1.3')!
    const html = renderToStaticMarkup(createElement(TextoPaso, { paso: p, resolver }))
    for (const n of p.datos) expect(html).toContain(resolver(n))
    expect(html).not.toContain(t('aviso.sin_dato'))
  })
})

describe('acciones del paso', () => {
  const montar = () => ({
    ir: vi.fn(),
    globo: { irAUnidad: vi.fn(() => true), cambiarVariable: vi.fn(), cambiarMes: vi.fn(), activarComparador: vi.fn(), abrirPestana: vi.fn() },
  })
  const paso = (id: string) => PASOS.find((p) => p.id === id)!

  it('sin datos solo navega y omite lo que depende de un dato ausente', () => {
    const m = montar()
    ejecutar(paso('1.2'), m)
    ejecutar(paso('2.1'), m)
    ejecutar(paso('2.2'), m)
    expect(m.ir).toHaveBeenCalledWith('tierra', {})
    expect(m.globo.irAUnidad).not.toHaveBeenCalled()
    expect(m.globo.cambiarVariable).not.toHaveBeenCalled()
    expect(m.globo.cambiarMes).not.toHaveBeenCalled()
  })
  it('Ipiales sale de contratos/unidades.md y el comparador se enciende y se apaga', () => {
    const m = montar()
    ejecutar(paso('3.1'), m)
    ejecutar(paso('2.3'), m)
    expect(m.globo.irAUnidad).toHaveBeenCalledWith(IPIALES)
    expect(m.globo.abrirPestana).toHaveBeenCalledWith('Rotaciones')
    expect(m.globo.activarComparador.mock.calls).toEqual([[false], [true]])
  })
  it('Rotaciones lleva la unidad y omite el lote que no se conoce', () => {
    const m = montar()
    ejecutar(paso('3.2'), m)
    expect(m.ir).toHaveBeenCalledWith('rotaciones', { unidad: IPIALES })
  })
  it('con datos usa el valor entregado', () => {
    const m = montar()
    const resolver = (n: string) => ({ mes_inicio: '2001-01', lote_ipiales: 'DEMO-COL-01', unidad_ipiales: IPIALES })[n]
    ejecutar(paso('2.2'), { ...m, resolver })
    ejecutar(paso('3.2'), { ...m, resolver })
    expect(m.globo.cambiarMes).toHaveBeenCalledWith('2001-01')
    expect(m.ir).toHaveBeenCalledWith('rotaciones', { unidad: IPIALES, lote: 'DEMO-COL-01' })
  })
  it('si el globo falla el recorrido sigue', () => {
    const m = montar()
    m.globo.irAUnidad.mockImplementation(() => { throw new Error('unidad_id inválido') })
    expect(() => ejecutar(paso('3.1'), m)).not.toThrow()
    expect(m.globo.abrirPestana).toHaveBeenCalled()
  })
})

describe('estado del recorrido', () => {
  beforeEach(() => useRecorrido.getState().salir())
  it('avanza, retrocede sin pasar de los extremos y sale', () => {
    const s = () => useRecorrido.getState()
    expect(s().activo).toBe(false)
    s().iniciar()
    expect([s().activo, s().indice]).toEqual([true, 0])
    s().anterior()
    expect(s().indice).toBe(0)
    for (let i = 0; i < PASOS.length + 3; i++) s().siguiente()
    expect(s().indice).toBe(PASOS.length - 1)
    s().anterior()
    expect(s().indice).toBe(PASOS.length - 2)
    s().salir()
    expect(s().activo).toBe(false)
    s().iniciar()
    expect(s().indice).toBe(0)
  })
})

describe('panel del recorrido', () => {
  const props = { anterior: () => {}, siguiente: () => {}, salir: () => {} }
  it('inactivo no pinta nada', () => {
    expect(renderToStaticMarkup(createElement(Recorrido))).toBe('')
  })
  it('región con nombre, texto en aria-live y tres botones con nombre', () => {
    enAmbosIdiomas(() => {
      const html = renderToStaticMarkup(createElement(PanelRecorrido, { ...props, indice: 0 }))
      expect(html).toMatch(/<section[^>]*aria-label="[^"]+"/)
      expect(html).toMatch(/aria-live="polite"/)
      for (const k of ['recorrido.anterior', 'recorrido.siguiente', 'recorrido.salir'] as ClaveTexto[]) expect(html).toContain(t(k))
      expect((html.match(/<button/g) ?? []).length).toBe(3)
    })
  })
  it('en el último paso Siguiente pasa a Terminar y Anterior se marca aria-disabled solo en el primero', () => {
    const ultimo = renderToStaticMarkup(createElement(PanelRecorrido, { ...props, indice: PASOS.length - 1 }))
    expect(ultimo).toContain(t('recorrido.terminar'))
    expect(ultimo).not.toContain(t('recorrido.siguiente'))
    expect(ultimo).not.toContain('aria-disabled="true"')
    expect(renderToStaticMarkup(createElement(PanelRecorrido, { ...props, indice: 0 }))).toContain('aria-disabled="true"')
  })
})

// La portada de la fase 3 ya no arranca el recorrido: sus pruebas están en portada_entrada.test.ts
