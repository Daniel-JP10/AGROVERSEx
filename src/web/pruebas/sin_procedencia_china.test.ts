// asistido por SI: Claude Code (Anthropic), prueba de cumplimiento §5.1 y D-021
import { readdirSync, readFileSync, statSync } from 'node:fs'
import { join } from 'node:path'
import { describe, expect, it } from 'vitest'

// Recorre server/ y src/paneles/ sin entrar en comparador/ (es de Web).
function archivos(dir: string): string[] {
  return readdirSync(dir).flatMap((n) => {
    const p = join(dir, n)
    if (statSync(p).isDirectory()) return n === 'comparador' ? [] : archivos(p)
    return /\.(ts|tsx)$/.test(n) ? [p] : []
  })
}

describe('sin procedencia china en server ni paneles (fuera de comparador)', () => {
  const todos = [...archivos('server'), ...archivos('src/paneles')]
  it('hay archivos que revisar', () => expect(todos.length).toBeGreaterThan(0))
  for (const f of todos) {
    it(f, () => {
      const txt = readFileSync(f, 'utf8').toLowerCase()
      expect(txt).not.toMatch(/china|chino|chin[ao]s?\b|d-009/)
    })
  }
})
