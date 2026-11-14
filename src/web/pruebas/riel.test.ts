// asistido por SI: Claude Code (Anthropic), escritura y revisión de código; base del prototipo migrada en el hackatón
import { readFileSync } from 'node:fs'
import { createElement } from 'react'
import { renderToStaticMarkup } from 'react-dom/server'
import { describe, expect, it } from 'vitest'
import { HERRAMIENTAS, Riel } from '../src/app/Riel'
import { contraste } from '../src/app/contraste'

describe('riel', () => {
  const html = renderToStaticMarkup(createElement(Riel, { activa: 'capas', onElegir: () => {} }))
  const botones = [...html.matchAll(/<button[^>]*aria-label="([^"]*)"/g)].map((m) => m[1])

  it('cada herramienta es un button con nombre accesible no vacío y distinto', () => {
    expect(botones).toHaveLength(HERRAMIENTAS.length)
    expect(botones.every((n) => n.trim().length > 2)).toBe(true)
    expect(new Set(botones).size).toBe(botones.length)
  })
  it('marca la activa con aria-pressed y oculta los iconos a lectores', () => {
    expect(html.match(/aria-pressed="true"/g)).toHaveLength(1)
    expect(html.match(/<svg[^>]*aria-hidden="true"/g)).toHaveLength(HERRAMIENTAS.length)
  })
})

// Lee las variables hex de un bloque de tema.css
const css = readFileSync(new URL('../src/app/tema.css', import.meta.url), 'utf8')
const bloque = (txt: string) => Object.fromEntries([...txt.matchAll(/--([\w-]+):\s*(#[0-9a-f]{6})/gi)].map((m) => [m[1], m[2]]))
const oscuro = bloque(css)

it('el tema es único y oscuro, sin variante por prefers-color-scheme', () => {
  expect(css).not.toContain('prefers-color-scheme')
})

describe.each([['oscuro', oscuro]])('contraste AA modo %s', (_n, v) => {
  it('textos sobre panel y fondo ≥ 4,5:1', () => {
    for (const t of ['texto', 'suave', 'acento', 'agua']) {
      expect(contraste(v[t], v['panel-base']), `${t}/panel`).toBeGreaterThanOrEqual(4.5)
      expect(contraste(v[t], v.fondo), `${t}/fondo`).toBeGreaterThanOrEqual(4.5)
    }
    expect(contraste(v['banda-texto'], v['banda-fondo']), 'banda').toBeGreaterThanOrEqual(4.5)
  })
  it('foco (acento) sobre fondo y panel ≥ 3:1', () => {
    expect(contraste(v.acento, v.fondo)).toBeGreaterThanOrEqual(3)
    expect(contraste(v.acento, v['panel-base'])).toBeGreaterThanOrEqual(3)
  })
})
