// asistido por SI: Claude Code (Anthropic), prueba de que los textos no llevan escrito a mano el lugar de un lote demo
import { readFileSync } from 'node:fs'
import { describe, expect, it } from 'vitest'
import { en } from '../src/textos/en'
import { es } from '../src/textos/es'

const lotes = JSON.parse(readFileSync(new URL('../../../datos/lotes/lotes_demo.json', import.meta.url), 'utf8')).lotes as { nombre: string }[]
// parte de lugar: lo que va tras "Lote DEMO " y antes del paréntesis
const lugar = (n: string) => n.replace(/^Lote DEMO\s+/, '').replace(/\s*\(.*$/, '').trim()

describe('nombres de lote', () => {
  it('ningún texto contiene el lugar de un lote demo', () => {
    const lugares = lotes.map((l) => lugar(l.nombre))
    expect(lugares.length).toBeGreaterThan(1)
    for (const x of lugares) expect(x.length, x).toBeGreaterThan(2)
    for (const [idioma, d] of [['en', en], ['es', es]] as const)
      for (const [k, v] of Object.entries(d)) for (const x of lugares) expect(String(v), `${idioma} ${k} ${x}`).not.toContain(x)
  })
})
