// asistido por SI: Claude Code (Anthropic), prueba del índice de textos por sección (plan fase 3 v2 §10)
import { describe, expect, it } from 'vitest'
import { PARTES } from '../src/textos/indice'

describe('índice de textos por sección', () => {
  it('ninguna clave aparece en dos partes', () => {
    const vistas = new Map<string, string>()
    const choques: string[] = []
    for (const [parte, { en }] of Object.entries(PARTES)) {
      for (const k of Object.keys(en)) {
        if (vistas.has(k)) choques.push(`${k}: ${vistas.get(k)} y ${parte}`)
        vistas.set(k, parte)
      }
    }
    expect(choques).toEqual([])
  })
  it('cada sección usa solo claves con su prefijo', () => {
    const fuera: string[] = []
    for (const [parte, { en }] of Object.entries(PARTES)) {
      if (parte === 'base') continue
      for (const k of Object.keys(en)) if (!k.startsWith(`${parte}.`)) fuera.push(`${parte}: ${k}`)
    }
    expect(fuera).toEqual([])
  })
  it('el español de cada sección tiene las mismas claves que el inglés', () => {
    for (const [parte, { en, es }] of Object.entries(PARTES)) {
      if (parte === 'base') continue
      expect(Object.keys(es).sort(), parte).toEqual(Object.keys(en).sort())
    }
  })
})
