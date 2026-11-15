// asistido por SI: Claude Code, bloqueo de publicación: ningún texto visible nombra GADM, EOX ni cloudless
import { describe, expect, it } from 'vitest'
import { readdirSync, readFileSync, statSync } from 'node:fs'
import { join, sep } from 'node:path'
import { ATRIBUCION } from '../src/globo/config'

const PROHIBIDO = /gadm|eox|cloudless|worldclim|gaez|k[öo]ppen|köppen-geiger 2023/i  // Köppen: D-025
const quitarComentarios = (s: string) => s.replace(/\/\*[\s\S]*?\*\//g, '').replace(/(^|[^:'"`])\/\/.*$/gm, '$1')
const archivos = (d: string): string[] => readdirSync(d).flatMap((n) => {
  const r = join(d, n)
  return statSync(r).isDirectory() ? archivos(r) : [r]
})

describe('textos visibles sin fuentes excluidas', () => {
  it('la atribución no las nombra', () => expect(ATRIBUCION).not.toMatch(PROHIBIDO))
  it('textos/*.ts y literales de los .tsx no las nombran', () => {
    const malos: string[] = []
    for (const f of archivos('src')) {
      const esTexto = f.split(sep).join('/').includes('src/textos/') && f.endsWith('.ts')
      if (!esTexto && !f.endsWith('.tsx')) continue
      const m = quitarComentarios(readFileSync(f, 'utf8')).match(PROHIBIDO)
      if (m) malos.push(f)
    }
    expect(malos).toEqual([])
  })
})
