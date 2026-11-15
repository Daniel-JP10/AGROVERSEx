// asistido por SI: Claude Code (Anthropic), prueba: el póster del globo coincide con su manifiesto y cabe en 400 px (plan v1 §a)
import { createHash } from 'node:crypto'
import { readFileSync } from 'node:fs'
import { describe, expect, it } from 'vitest'

const leer = (f: string) => readFileSync(new URL(`../public/portada/${f}`, import.meta.url))

describe('póster del globo', () => {
  it('es WebP de 400 px o menos y su SHA-256 es el del manifiesto', () => {
    const img = leer('globo.webp')
    const man = JSON.parse(leer('globo.manifiesto.json').toString('utf-8'))
    expect(img.subarray(0, 4).toString()).toBe('RIFF')
    expect(img.subarray(8, 12).toString()).toBe('WEBP')
    expect(createHash('sha256').update(img).digest('hex')).toBe(man.sha256)
    expect(img.length).toBe(man.bytes)
    expect(Math.max(man.ancho, man.alto)).toBeLessThanOrEqual(400)
    // ancho y alto reales de la cabecera VP8/VP8L/VP8X
    const tipo = img.subarray(12, 16).toString()
    const [w, h] = tipo === 'VP8X' ? [img.readUIntLE(24, 3) + 1, img.readUIntLE(27, 3) + 1]
      : tipo === 'VP8L' ? [(img.readUInt32LE(21) & 0x3fff) + 1, ((img.readUInt32LE(21) >> 14) & 0x3fff) + 1]
      : [img.readUInt16LE(26) & 0x3fff, img.readUInt16LE(28) & 0x3fff]
    expect([w, h]).toEqual([man.ancho, man.alto])
  })
})
