// asistido por SI: Claude Code (Anthropic), pruebas de la sección Rotaciones: bandas, ejemplo, estructura de la tarjeta y estado sin lote
import { createElement as h } from 'react'
import { renderToStaticMarkup } from 'react-dom/server'
import { describe, expect, it } from 'vitest'
import ejemplo from '../src/secciones/rotaciones/ejemplo_gemelo.json'
import textosEjemplo from '../src/secciones/rotaciones/ejemplo_textos_gemelo.json'
import type { SalidaOptimizacion } from '../src/secciones/rotaciones/gemelo'
import { Banda } from '../src/secciones/rotaciones/Banda'
import { Avisos } from '../src/secciones/rotaciones/Avisos'
import { Compromisos } from '../src/secciones/rotaciones/Compromisos'
import { FrentePareto } from '../src/secciones/rotaciones/FrentePareto'
import { VistaRotaciones } from '../src/secciones/rotaciones/Rotaciones'
import { t } from '../src/textos/i18n'
import { useModo } from '../src/textos/modos'
import { enEspanol } from './idioma_es'
enEspanol()

const doc = ejemplo as unknown as SalidaOptimizacion
const vista = (fuente: Parameters<typeof VistaRotaciones>[0]['fuente']) => renderToStaticMarkup(h(VistaRotaciones, { fuente }))
const conEjemplo = () => vista({ estado: 'listo', origen: 'ejemplo', doc })
const conCatalogo = () => vista({ estado: 'listo', origen: 'ejemplo', doc, catalogo: textosEjemplo.es })
const cuenta = (html: string, re: RegExp) => (html.match(re) ?? []).length

// Texto visible sin las bandas ni los textos literales del gemelo; devuelve los números que quedan sueltos
function numerosSueltos(html: string): string[] {
  const texto = html
    .replace(/<(\w+) data-banda[^>]*>[^<]*<\/\1>/g, ' ')
    .replace(/<(\w+) data-texto-gemelo[^>]*>[^<]*<\/\1>/g, ' ')
    .replace(/<!--.*?-->/g, '')
    .replace(/<[^>]*>/g, ' ')
  return texto.match(/(?<![\w-])\d[\d.,]*/g) ?? []
}

describe('Banda', () => {
  it('muestra p50, rango p10 a p90 y unidad', () => {
    const s = renderToStaticMarkup(h(Banda, { p10: 5.1, p50: 7.3, p90: 9.8, unidad: 'mm/año' }))
    expect(s).toMatch(/7[.,]3/)
    expect(s).toMatch(/5[.,]1/)
    expect(s).toMatch(/9[.,]8/)
    expect(s).toContain('mm/año')
  })
  it('sin p10 o sin p90 no muestra el número', () => {
    for (const b of [{ p10: null, p50: 7.3, p90: 9.8 }, { p10: 5.1, p50: 7.3, p90: null }, { p10: 5.1, p50: null, p90: 9.8 }]) {
      const s = renderToStaticMarkup(h(Banda, { ...b, unidad: 'mm/año' }))
      expect(s).not.toMatch(/\d/)
      expect(s).toContain(t('rotaciones.dato_no_disponible'))
    }
  })
})

describe('ejemplo del contrato v1.1', () => {
  it('declara naturaleza simulado, es optimización v1.1 y usa solo los nombres nuevos de la erosión', () => {
    expect(doc.metadatos.naturaleza).toBe('simulado')
    expect(doc.metadatos.tipo).toBe('optimizacion')
    expect(doc.metadatos.version_contrato_completa).toBe('1.1')
    expect(doc.avisos.length).toBeGreaterThan(0)
    expect(doc.avisos_claves).toHaveLength(doc.avisos.length)
    expect(JSON.stringify(doc)).not.toContain('exposicion_erosiva')
    for (const e of [doc.linea_base, ...doc.frente]) expect(Object.keys(doc.tarjetas![e.id])).toEqual(expect.arrayContaining(['por_que', 'evidencia', 'beneficios', 'vacios', 'riesgos']))
  })
  it('la sección muestra la línea base y al menos tres estrategias del frente', () => {
    const s = conEjemplo()
    expect(cuenta(s, /data-testid="linea-base"/g)).toBe(1)
    expect(cuenta(s, /data-testid="estrategia"/g)).toBeGreaterThanOrEqual(4)
    expect(doc.frente.length).toBeGreaterThanOrEqual(3)
    for (const e of [doc.linea_base, ...doc.frente]) expect(s).toContain(e.secuencia.replace(/\s*->\s*/g, ' → '))
  })
  it('se rotula SIMULADO y una corrida del modelo se rotula simulación del modelo', () => {
    const s = conEjemplo()
    expect(s).toContain(t('aviso.simulado'))
    // El aviso del ejemplo dice SIMULADO a propósito; se cambia para medir solo el rótulo
    const real = vista({ estado: 'listo', origen: 'modelo', doc: { ...doc, avisos: ['Resultados simulados.'], metadatos: { ...doc.metadatos, rotulo: undefined } } })
    expect(real).toContain(t('etiqueta.simulacion_modelo'))
    expect(real).not.toContain(t('aviso.simulado'))
  })
  it('una corrida del modelo muestra el rótulo del gemelo en el idioma activo (v1.1 §1)', () => {
    const rot = { clave: 'label.model_simulation', en: 'Model simulation with NASA POWER and SoilGrids 2.0 data', es: 'Simulación del modelo con datos NASA POWER y SoilGrids 2.0' }
    const real = vista({ estado: 'listo', origen: 'modelo', doc: { ...doc, avisos: ['Resultados simulados.'], metadatos: { ...doc.metadatos, rotulo: rot } } })
    expect(real).toContain(rot.es)
    expect(real).not.toContain(t('aviso.simulado'))
    expect(numerosSueltos(real)).toEqual([])
  })
})

describe('números siempre con banda', () => {
  it('el detector encuentra un número suelto', () => {
    expect(numerosSueltos('<p>valor 5</p>')).toEqual(['5'])
    expect(numerosSueltos('<span data-banda>5 (4-6) mm</span>')).toEqual([])
  })
  it('ningún número del árbol renderizado queda fuera de una banda, con y sin catálogo', () => {
    expect(numerosSueltos(conEjemplo())).toEqual([])
    expect(numerosSueltos(conCatalogo())).toEqual([])
  })
})

describe('tarjeta de cinco secciones y partes que esperan al gemelo', () => {
  it('con el catálogo, cada sección de cada estrategia muestra entradas del gemelo y ninguna queda pendiente', () => {
    const s = conCatalogo()
    const n = doc.frente.length + 1
    for (const b of ['porque', 'evidencia', 'beneficios', 'vacios', 'riesgos']) expect(cuenta(s, new RegExp(`data-bloque="${b}"><h4>[^<]*</h4><ul><li data-texto-gemelo`, 'g'))).toBe(n)
    expect(s).toContain(textosEjemplo.es['card.risk.local_review'])
    expect(s).toContain(`Este es el manejo actual (${doc.linea_base.id})`)
    expect(cuenta(s, /<section data-bloque="[a-z]+"><h4>[^<]*<\/h4><p class="sin-dato">/g)).toBe(0)
  })
  it('sin catálogo cada estrategia trae las cinco secciones como estructura pendiente', () => {
    const s = conEjemplo()
    const n = doc.frente.length + 1
    for (const b of ['porque', 'evidencia', 'beneficios', 'vacios', 'riesgos']) expect(cuenta(s, new RegExp(`data-bloque="${b}"`, 'g'))).toBe(n)
    expect(cuenta(s, new RegExp(t('rotaciones.pendiente_gemelo'), 'g'))).toBeGreaterThanOrEqual(5 * n)
  })
  it('prioridades (con sus cuatro deslizadores) y alertas aparecen; la calibración local y los pendientes ya no', () => {
    const s = conEjemplo()
    for (const k of ['rotaciones.prioridades', 'rotaciones.alertas'] as const) expect(s).toContain(t(k))
    // plan fase 3 v2 §5: "Calibración local" queda excluida y los escenarios pasan al comparador del tablero
    expect(s).not.toContain(t('rotaciones.calibracion'))
    expect(cuenta(s, /type="range"/g)).toBe(4)
    expect(cuenta(s, /class="pendiente"/g)).toBe(0)
  })
  it('una estrategia sin algún objetivo de prioridad lo dice con «sin dato» y se marca incompleta, sin valor inventado', () => {
    const s = conEjemplo()
    const n = cuenta(s, /data-testid="estrategia"/g)
    // el ejemplo v1.1 trae carbono y erosión, pero no riego, déficit, fertilizante ni riesgo de producción
    expect(cuenta(s, /data-testid="incompleta"/g)).toBe(n)
    expect(cuenta(s, new RegExp(`<li[^>]*data-objetivo="riego"[^>]*>[^<]*<span[^>]*>${t('comun.sinDato')}`, 'g'))).toBe(n)
    expect(s).toContain(t('prioridades.incompleta'))
  })
  it('aviso de apoyo y revisión local junto a cada estrategia', () => {
    const s = conEjemplo()
    expect(s).toContain(t('aviso.apoyo'))
    expect(cuenta(s, new RegExp(t('aviso.juicio'), 'g'))).toBe(doc.frente.length + 1)
  })
})

describe('avisos, compromisos y Pareto', () => {
  it('el primer aviso del gemelo siempre se ve', () => {
    expect(renderToStaticMarkup(h(Avisos, { avisos: doc.avisos }))).toContain(doc.avisos[0])
  })
  it('compromisos: medias sin rango, solo en Technical; al agricultor solo la nota y ninguna cifra', () => {
    useModo.setState({ modo: 'agricultor' })
    const a = renderToStaticMarkup(h(Compromisos, { frente: doc.frente, compromisos: doc.compromisos }))
    expect(a).toContain(t('rotaciones.compromisos_tecnico'))
    expect(a.replace(/<[^>]+>/g, ' ')).not.toMatch(/\d/)
    useModo.setState({ modo: 'tecnico' })
  })
  it('compromisos presenta los textos del gemelo y nunca dice óptima (Technical)', () => {
    useModo.setState({ modo: 'tecnico' })
    const s = renderToStaticMarkup(h(Compromisos, { frente: doc.frente, compromisos: doc.compromisos }))
    expect(s).toContain(doc.compromisos.explicacion[0])
    expect(s).toContain(doc.frente[0].frente_a_linea_base!.gana[0].replace('>', '&gt;')) // el HTML escapa ">"
    expect(s).not.toMatch(/[oó]ptim[ao]|optimal|best/i)
  })
  it('el frente tiene selector de dos ejes, alternativa en texto y la línea base marcada', () => {
    const s = renderToStaticMarkup(h(FrentePareto, { objetivos: doc.objetivos, linea_base: doc.linea_base, frente: doc.frente }))
    expect(cuenta(s, /<select/g)).toBe(2)
    expect(s).toMatch(/role="img"[^>]*aria-label|aria-label[^>]*role="img"/)
    expect(s).toContain('data-testid="pareto-alternativa"')
    expect(s).toContain('data-testid="pareto-linea-base"')
  })
})

describe('sin lote', () => {
  it('explica que no hay lote DEMO y no muestra resultados ni números', () => {
    const s = vista({ estado: 'sin_lote' })
    expect(s).toContain(t('rotaciones.sin_lote'))
    expect(s).not.toContain('data-banda')
    expect(s).not.toContain('data-testid="estrategia"')
    expect(s).not.toContain('data-testid="linea-base"')
    expect(numerosSueltos(s)).toEqual([])
  })
  it('con lote pero sin dato del gemelo tampoco inventa nada', () => {
    const s = vista({ estado: 'sin_dato' })
    expect(s).toContain(t('aviso.sin_dato'))
    expect(s).not.toContain('data-testid="estrategia"')
  })
})

// H-F3-4: card.benefit.delta trae una diferencia de medianas con el p10 y p90 ABSOLUTOS de la estrategia
describe('beneficio frente a la línea base', () => {
  it('rotula el delta como diferencia de medianas y el rango como el de la estrategia sola', async () => {
    const { entradaTexto } = await import('../src/secciones/rotaciones/ComparadorEstrategias')
    const cat = { 'card.benefit.delta': '{indicador}: {delta:+.3g} {unidad} against the baseline (p50; p10 {p10:.3g}, p90 {p90:.3g})', 'ind.x': 'Relative yield', 'unit.x': 'dimensionless' }
    const s = entradaTexto(cat, { clave: 'card.benefit.delta', parametros: { indicador: { clave: 'ind.x' }, delta: 0.0163, unidad: { clave: 'unit.x' }, p10: 0.382, p90: 0.834 } })
    expect(s).toContain('diferencia entre las dos medianas')
    expect(s).toContain('va de p10 0.382 a p90 0.834')
    expect(s).not.toContain('(p50; p10')
  })
})
