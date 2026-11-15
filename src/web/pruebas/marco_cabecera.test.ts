// asistido por SI: Claude Code (Anthropic), pruebas del marco común de la fase 3: cabecera hoja, decoración, pie, tokens y respaldo de #/lote
import { readFileSync } from 'node:fs'
import { createElement } from 'react'
import { renderToStaticMarkup } from 'react-dom/server'
import { afterEach, describe, expect, it } from 'vitest'
import { CabeceraHoja } from '../src/app/marco/CabeceraHoja'
import { Decoracion } from '../src/app/marco/Decoracion'
import { MarcadorLote } from '../src/app/marco/Marcador'
import { contraste } from '../src/app/contraste'
import { alternar, idioma, t } from '../src/textos/i18n'
import { useModo } from '../src/textos/modos'
import * as marco from '../src/textos/secciones/marco'

afterEach(() => { useModo.getState().set('agricultor'); if (idioma() !== 'en') alternar() })

const cabecera = () => renderToStaticMarkup(createElement(CabeceraHoja))
const tema = readFileSync(new URL('../src/app/tema.css', import.meta.url), 'utf8')
const color = (n: string) => new RegExp(`--${n}:\\s*(#[0-9a-f]{6})`, 'i').exec(tema)![1]

describe('cabecera hoja', () => {
  it('lleva AGROVERSEx sin SIMULADO ni DEMO, en los dos idiomas', () => {
    for (const _ of [0, 1]) {
      const h = cabecera()
      expect(h).toContain('>AGROVERSEx</a>')
      expect(h).not.toMatch(/SIMULADO|SIMULATED|DEMO/)
      alternar()
    }
  })
  it('navega a las seis secciones en orden, sin el gemelo aparte', () => {
    const hrefs = [...cabecera().matchAll(/<nav[^>]*>(.*?)<\/nav>/g)][0][1].match(/href="([^"]+)"/g)
    expect(hrefs).toEqual(['#/tierra', '#/lote', '#/rotaciones', '#/ciencia', '#/datos', '#/fuentes'].map((h) => `href="${h}"`))
    const h = cabecera()
    for (const n of ['Earth', 'Your field', 'Rotations', 'Science and validation', 'Open data', 'Sources']) expect(h).toContain(`>${n}</a>`)
    expect(h).not.toContain('#/gemelo')
  })
  it('selector de modo Farmer/Technical con aria-pressed y selector de idioma EN/ES', () => {
    // El render de servidor no ve los cambios del almacén: el cambio a Technical lo prueba el E2E
    const h = cabecera()
    expect(h).toMatch(/<button[^>]*aria-pressed="true"[^>]*>Farmer<\/button>/)
    expect(h).toMatch(/<button[^>]*aria-pressed="false"[^>]*>Technical<\/button>/)
    expect(h).toMatch(/<button[^>]*aria-label="Language[^"]*"[^>]*>.*EN.*ES.*<\/button>/)
  })
  it('sin ícono de usuario', () => {
    expect(cabecera()).not.toMatch(/user|usuario|account|cuenta|perfil|profile/i)
  })
  it('el contorno de hoja es decoración: aria-hidden y sin foco', () => {
    expect(cabecera()).toMatch(/<svg class="cabecera-contorno"[^>]*aria-hidden="true"[^>]*focusable="false"/)
  })
})

describe('decoración y pie', () => {
  it('las hojas de esquina están ocultas a lectores, sin tabindex', () => {
    const h = renderToStaticMarkup(createElement(Decoracion))
    expect(h).toMatch(/^<div class="decoracion" aria-hidden="true">/)
    expect((h.match(/<svg/g) ?? []).length).toBe(2)
    expect(h).not.toContain('tabindex')
  })
  it('las decoraciones no reciben eventos de puntero (CSS)', () => {
    const css = readFileSync(new URL('../src/app/marco/marco.css', import.meta.url), 'utf8')
    expect(css).toMatch(/\.decoracion \{[^}]*pointer-events: none/)
    expect(css).toMatch(/\.cabecera-contorno \{[^}]*pointer-events: none/)
  })
  it('el pie lleva el aviso de herramienta de apoyo', async () => {
    // El pie llega al estado del globo por la interfaz de tierra, que lee localStorage al cargar
    const g = globalThis as { localStorage?: Pick<Storage, 'getItem' | 'setItem'> }
    g.localStorage ??= { getItem: () => null, setItem: () => {} }
    const { Pie } = await import('../src/app/marco/Pie')
    expect(renderToStaticMarkup(createElement(Pie))).toContain(t('aviso.apoyo'))
  })
  it('el respaldo de #/lote dice que aún no está disponible, sin cifras', () => {
    const h = renderToStaticMarkup(createElement(MarcadorLote))
    expect(h).toContain(t('marco.lote.pronto'))
    expect(h.replace(/<[^>]+>/g, '')).not.toMatch(/\d/)
  })
})

describe('tokens de la fase 3 (plan v1 §e)', () => {
  it('se retira el café y quedan los tokens de hoja', () => {
    expect(color('fondo')).toBe('#03100b')
    expect(color('hoja')).toBe('#0f2a1d')
    expect(color('acento')).toBe('#7be0a0')
    expect(color('agua')).toBe('#4fd1c5')
    expect(tema).not.toMatch(/#3a2a10|#ffb84d|#ffc870/i)
  })
  it('contraste AA de los textos sobre fondo y hoja', () => {
    for (const fg of ['texto', 'suave', 'acento', 'agua']) for (const bg of ['fondo', 'hoja', 'realce']) {
      expect(contraste(color(fg), color(bg)), `${fg}/${bg}`).toBeGreaterThanOrEqual(4.5)
    }
  })
})

describe('textos del marco', () => {
  it('EN y ES con las mismas claves y prefijo marco.', () => {
    expect(Object.keys(marco.es).sort()).toEqual(Object.keys(marco.en).sort())
    for (const k of Object.keys(marco.en)) expect(k.startsWith('marco.'), k).toBe(true)
  })
})
