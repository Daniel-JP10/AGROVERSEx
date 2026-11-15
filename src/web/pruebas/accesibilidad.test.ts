// asistido por SI: Claude Code (Anthropic), pruebas de accesibilidad: movimiento reducido, foco visible y contraste del recorrido
import { readFileSync } from 'node:fs'
import { describe, expect, it } from 'vitest'
import { contraste } from '../src/app/contraste'

const leer = (ruta: string) => readFileSync(new URL(ruta, import.meta.url), 'utf8')
const tema = leer('../src/app/tema.css')
const variable = (n: string) => new RegExp(`--${n}:\\s*(#[0-9a-f]{6})`, 'i').exec(tema)![1]
const recorrido = leer('../src/app/recorrido/recorrido.css')
const estilos = leer('../src/estilos.css')

describe('accesibilidad del recorrido y la sección Fuentes', () => {
  it('respeta prefers-reduced-motion: sin animaciones ni transiciones del panel', () => {
    const m = /@media \(prefers-reduced-motion: reduce\)\s*\{([^}]*\{[^}]*\}[^}]*)\}/.exec(recorrido)
    expect(m, 'falta el bloque de movimiento reducido').not.toBeNull()
    expect(m![1]).toMatch(/animation:\s*none/)
    expect(m![1]).toMatch(/transition:\s*none/)
  })
  it('el foco visible no se apaga en ningún estilo del recorrido ni de la sección', () => {
    expect(recorrido).not.toMatch(/outline:\s*(none|0)/)
    expect(estilos).not.toMatch(/outline:\s*(none|0)/)
    expect(estilos).toMatch(/:focus-visible\s*\{\s*outline:\s*2px solid var\(--acento\)/)
  })
  it('el aro de foco y el texto del panel cumplen el contraste de WCAG 2.1 AA sobre el panel', () => {
    expect(contraste(variable('acento'), variable('panel-base'))).toBeGreaterThanOrEqual(3)
    expect(contraste(variable('agua'), variable('panel-base'))).toBeGreaterThanOrEqual(3)
    for (const n of ['texto', 'suave']) expect(contraste(variable(n), variable('panel-base')), n).toBeGreaterThanOrEqual(4.5)
  })
  it('los colores del recorrido salen de los tokens, sin colores escritos a mano', () => {
    expect(recorrido).not.toMatch(/#[0-9a-f]{3,6}\b/i)
  })
})
