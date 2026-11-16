// asistido por SI: Claude Code (Anthropic), el título de la pestaña va en inglés, como toda la entrega (AGENTS §5.3)
import { readFileSync } from 'node:fs'
import { describe, expect, it } from 'vitest'

describe('título de la página', () => {
  it('es AGROVERSEx, sin texto en español', () => {
    const html = readFileSync(new URL('../index.html', import.meta.url), 'utf8')
    expect(/<title>([^<]*)<\/title>/.exec(html)?.[1]).toBe('AGROVERSEx')
  })
})
