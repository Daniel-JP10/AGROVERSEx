// asistido por SI: Claude Code (Anthropic), pruebas de la sección El gemelo del lote (T-W6)
import { readFileSync } from 'node:fs'
import { join } from 'node:path'
import { createElement } from 'react'
import { renderToStaticMarkup } from 'react-dom/server'
import { afterEach, describe, expect, it } from 'vitest'
import { Gemelo } from '../src/secciones/gemelo/Gemelo'
import { GemeloVista } from '../src/secciones/gemelo/GemeloVista'
import { VARIABLES, type Estrategia } from '../src/secciones/gemelo/tipos'
import { ESTRATEGIAS_EJEMPLO } from '../src/secciones/gemelo/ejemplo'
import { en } from '../src/textos/en'
import { es } from '../src/textos/es'
import { alternar, idioma } from '../src/textos/i18n'
import { useModo } from '../src/textos/modos'
import { enEspanol } from './idioma_es'
enEspanol()

const [BASE, ALT] = ESTRATEGIAS_EJEMPLO
const vista = (p: Parameters<typeof GemeloVista>[0]) => renderToStaticMarkup(createElement(GemeloVista, p))
const cuenta = (h: string, re: RegExp) => (h.match(re) ?? []).length

afterEach(() => { useModo.getState().set('agricultor'); if (idioma() === 'en') alternar() })

describe('gemelo: carga', () => {
  it('sin archivos ni ejemplo dice que no hay dato y no dibuja nada', () => {
    const h = renderToStaticMarkup(createElement(Gemelo))
    expect(h).toContain('Dato todavía no disponible.')
    expect(h).not.toContain('<svg')
    expect(vista({ origen: 'corrida' })).not.toContain('<svg')
  })
  it('con el ejemplo dibuja las cinco variables con las dos estrategias y rotula SIMULADO', () => {
    const h = vista({ origen: 'ejemplo', lote: 'L1', base: BASE, alternativa: ALT })
    expect(cuenta(h, /<svg[^>]*role="img"/g)).toBe(5)
    expect(cuenta(h, /<polygon/g)).toBe(10)
    expect(h).toContain('SIMULADO')
    expect(h).not.toContain('Simulación del modelo')
  })
  it('una corrida real se rotula simulación del modelo y no SIMULADO', () => {
    const h = vista({ origen: 'corrida', base: BASE, alternativa: ALT })
    expect(h).toContain('Simulación del modelo')
    expect(h).not.toContain('SIMULADO')
  })
  it('el ejemplo solo se importa de forma dinámica (la bandera lo deja fuera de la versión pública)', () => {
    for (const f of ['Gemelo.tsx', 'GemeloVista.tsx', 'Grafico.tsx']) {
      const src = readFileSync(join(__dirname, '../src/secciones/gemelo', f), 'utf8')
      expect(src, f).not.toMatch(/^import[^\n]*['"]\.\/ejemplo['"]/m)
    }
  })
})

describe('gemelo: ningún valor sin banda', () => {
  it('cada valor mostrado trae su rango p10 a p90', () => {
    const h = vista({ origen: 'ejemplo', base: BASE, alternativa: ALT })
    const valores = [...h.matchAll(/<[^>]*data-valor[^>]*>/g)].map((m) => m[0])
    expect(valores).toHaveLength(10)
    for (const v of valores) expect(v).toMatch(/data-p10="[^"]+"[^>]*data-p90="[^"]+"|data-p90="[^"]+"[^>]*data-p10="[^"]+"/)
  })
  it('una variable con solo la mediana no muestra valor ni línea', () => {
    const roto: Estrategia = { nombre: 'x', trayectoria_mensual: { ...BASE.trayectoria_mensual, W: { p50: BASE.trayectoria_mensual.W.p50 } as never } }
    const h = vista({ origen: 'ejemplo', base: roto })
    expect(cuenta(h, /<svg[^>]*role="img"/g)).toBe(4)
    expect(cuenta(h, /data-valor/g)).toBe(4)
    expect(h).toContain('No hay rango disponible para esta variable.')
  })
  it('una banda con valores no finitos se descarta entera', () => {
    const w = BASE.trayectoria_mensual.W
    const roto: Estrategia = { nombre: 'x', trayectoria_mensual: { ...BASE.trayectoria_mensual, W: { ...w, p90: w.p90.map((v, i) => (i === 3 ? null : v)) as never } } }
    expect(cuenta(vista({ origen: 'ejemplo', base: roto }), /data-valor/g)).toBe(4)
  })
})

describe('gemelo: ventanas de suelo desnudo y enlace', () => {
  it('marca ventanas con el cuerpo de la banda y las lista en texto', () => {
    const h = vista({ origen: 'ejemplo', base: BASE, alternativa: ALT })
    expect(h).toMatch(/data-ventana="firme"/)
    expect(h).toMatch(/Suelo desnudo|ventanas de suelo desnudo/i)
    expect(h).toMatch(/meses \d/)
  })
  it('sin la variable desnudo no inventa ventanas', () => {
    const { desnudo: _d, ...resto } = BASE.trayectoria_mensual
    const h = vista({ origen: 'ejemplo', base: { nombre: 'x', trayectoria_mensual: resto as never } })
    expect(h).not.toContain('data-ventana')
  })
  it('enlaza a rotaciones con el mismo lote', () => {
    const h = vista({ origen: 'ejemplo', lote: 'DEMO-COL-01', base: BASE })
    expect(h).toContain('href="#/rotaciones?lote=DEMO-COL-01"')
  })
})

describe('gemelo: textos por variable', () => {
  const claves = VARIABLES.flatMap((v) => [`gemelo.${v}_nombre`, `gemelo.${v}_agricultor`, `gemelo.${v}_tecnico`])
  it('las seis variables tienen nombre y frase de agricultor y de técnico, en inglés y español', () => {
    for (const k of claves) {
      expect((en as Record<string, string>)[k], k).toBeTruthy()
      expect((es as Record<string, string>)[k], k).toBeTruthy()
    }
    for (const v of VARIABLES) expect((en as Record<string, string>)[`gemelo.${v}_agricultor`]).not.toBe((en as Record<string, string>)[`gemelo.${v}_tecnico`])
  })
  it('el modo cambia la frase y el idioma también', () => {
    const base = { origen: 'ejemplo' as const, base: BASE }
    const agri = vista(base)
    useModo.getState().set('tecnico')
    const tec = vista(base)
    expect(tec).not.toBe(agri)
    expect(tec).toContain(es['gemelo.W_tecnico' as never] as string)
    alternar()
    expect(vista(base)).toContain((en as Record<string, string>)['gemelo.W_tecnico'])
  })
})
