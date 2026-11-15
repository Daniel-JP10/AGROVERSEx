// asistido por SI: Claude Code (Anthropic), prueba de lo que se publica en public/gemelo y public/lotes: archivos permitidos, sin rutas locales ni textos prohibidos
import { readdirSync, readFileSync, statSync } from 'node:fs'
import { join, relative } from 'node:path'
import { describe, expect, it } from 'vitest'

const PUB = join(__dirname, '..', 'public')
const todos = (d: string): string[] => readdirSync(d).flatMap((f) => (statSync(join(d, f)).isDirectory() ? todos(join(d, f)) : [join(d, f)]))
const archivos = [...todos(join(PUB, 'gemelo')), ...todos(join(PUB, 'lotes'))].map((f) => relative(PUB, f).split('\\').join('/'))

describe('paquetes publicados', () => {
  it('solo indice, textos, lote, 7 simulaciones y 4 optimizaciones por lote; nada de calibración ni personalizados', () => {
    const gemelo = archivos.filter((f) => f.startsWith('gemelo/'))
    expect(gemelo.filter((f) => /calibracion|personalizados/.test(f))).toEqual([])
    for (const l of ['DEMO-COL-01', 'DEMO-USA-01']) {
      expect(gemelo.filter((f) => f.startsWith(`gemelo/${l}/simulacion_`))).toHaveLength(7)
      expect(gemelo.filter((f) => f.startsWith(`gemelo/${l}/optimizacion_`))).toHaveLength(4)
      expect(gemelo).toContain(`gemelo/${l}/lote.json`)
    }
    expect(gemelo).toEqual(expect.arrayContaining(['gemelo/indice.json', 'gemelo/textos/en.json', 'gemelo/textos/es.json']))
  })
  it('ningún JSON publicado lleva rutas locales ni las palabras de la lista de prohibidos', () => {
    for (const f of archivos.filter((x) => x.endsWith('.json'))) {
      const s = readFileSync(join(PUB, f), 'utf8')
      expect(s, f).not.toMatch(/[A-Z]:[\\/]{1,2}(NASA|Users)|\/Users\//)
      expect(s, f).not.toMatch(/SIMULADO|Lot health|Salud del lote|ERA5|GAEZ|Telemetr|\bPred\./)
    }
  })
})
