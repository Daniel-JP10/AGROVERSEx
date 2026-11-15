// asistido por SI: Claude Code (Anthropic), prueba de que los restos en español del gemelo salen en inglés (H-F3-6)
import { readFileSync, readdirSync } from 'node:fs'
import { join } from 'node:path'
import { describe, expect, it } from 'vitest'
import { aIngles, corregirCatalogoEn } from '../src/secciones/rotaciones/correccionEn'

const GEMELO = join(__dirname, '..', 'public', 'gemelo')
const ES = /[áéíóúñ]|\b(año|semestre|papa|avena|frijol|maiz|soya|celda|diario|estimado|candidata|SUPUESTO|FUENTE|INFERENCIA|PENDIENTE)\b/

describe('restos en español del gemelo en la interfaz inglesa', () => {
  it('catálogo inglés sin etiquetas de evidencia en español y con la unidad índice en inglés', () => {
    const cat = corregirCatalogoEn(JSON.parse(readFileSync(join(GEMELO, 'textos', 'en.json'), 'utf8')))
    const restos = Object.entries(cat).filter(([k, v]) => k !== 'unit.índice' && !k.startsWith('unit.') && /\b(SUPUESTO|FUENTE|INFERENCIA|PENDIENTE)\b/.test(v))
    expect(restos).toEqual([])
    expect(cat['unit.índice']).toBe('index')
  })
  it('cada etiqueta, parámetro plano y nombre de secuencia de los paquetes sale en inglés', () => {
    const planos = new Set<string>()
    for (const lote of readdirSync(GEMELO).filter((d) => d.startsWith('DEMO-'))) {
      for (const f of readdirSync(join(GEMELO, lote)).filter((n) => /^(optimizacion|simulacion)_.*\.json$/.test(n))) {
        const o = JSON.parse(readFileSync(join(GEMELO, lote, f), 'utf8'))
        for (const e of [...(o.frente ?? []), ...(o.estrategias ?? []), o.linea_base ?? {}]) { if (e.etiqueta) planos.add(e.etiqueta); if (e.nombre) planos.add(e.nombre) }
        JSON.stringify(o, (k, v) => { if (k === 'parametros' && v && typeof v === 'object') for (const x of Object.values(v)) if (typeof x === 'string') planos.add(x); return v })
      }
    }
    expect(planos.size).toBeGreaterThan(5)
    expect([...planos].map(aIngles).filter((s) => ES.test(s))).toEqual([])
  })
  it('lo que no reconoce queda igual: no inventa texto', () => {
    expect(aIngles('NASA POWER')).toBe('NASA POWER')
  })
})
