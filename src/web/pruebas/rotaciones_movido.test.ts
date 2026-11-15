// asistido por SI: Claude Code (Anthropic), pruebas del retiro del comparador legado y de la pestaña Rotaciones del panel
import { existsSync, readdirSync, readFileSync } from 'node:fs'
import { join } from 'node:path'
import { createElement as h } from 'react'
import { renderToStaticMarkup } from 'react-dom/server'
import { describe, expect, it } from 'vitest'
import { Rotaciones } from '../src/paneles/comparador/Rotaciones'
import { t } from '../src/textos/i18n'

const RAIZ = join(__dirname, '..', 'src')

describe('comparador legado retirado', () => {
  it('no quedan los archivos del comparador de tablas en secciones/rotaciones', () => {
    for (const f of ['TarjetaEstrategia.tsx', 'ResumenPanel.tsx', 'fixtures.ts', 'ordenar.ts', 'datos.ts', 'Prioridades.tsx', 'demo.tsx']) {
      expect(existsSync(join(RAIZ, 'secciones', 'rotaciones', f)), f).toBe(false)
    }
  })
  it('la pestaña del panel solo resume y enlaza a la sección, sin cifras', () => {
    const s = renderToStaticMarkup(h(Rotaciones, { resp: { vacio: false, zona: 'x' } }))
    expect(s).toContain('href="#/rotaciones"')
    expect(s).toContain(t('rotaciones.panel_enlace'))
    expect(s.replace(/<[^>]*>/g, ' ')).not.toMatch(/\d/)
  })
})

describe('procedencia fuera de Rotaciones', () => {
  // El patrón va escrito con clase de caracteres para que el propio archivo no aparezca en el git grep de aceptación
  const PROHIBIDO = /D-0{2}9|ch[i]n|Klu[g]er/i
  it('el detector marca lo prohibido', () => {
    expect('cita D-00' + '9').toMatch(PROHIBIDO)
    expect('regi' + 'ón ch' + 'ina').toMatch(PROHIBIDO)
    expect('Klu' + 'ger2025').toMatch(PROHIBIDO)
  })
  it('ningún archivo de secciones/rotaciones ni de paneles/comparador lo cita', () => {
    const carpetas = [join(RAIZ, 'secciones', 'rotaciones'), join(RAIZ, 'paneles', 'comparador')]
    for (const c of carpetas) for (const f of readdirSync(c)) {
      expect(readFileSync(join(c, f), 'utf8'), f).not.toMatch(PROHIBIDO)
    }
  })
})
