// asistido por SI: Claude Code (Anthropic), paridad de los registros en inglés (D-043) y barrido de "pendiente" en Fuentes y la ayuda
import { readFileSync } from 'node:fs'
import { createElement } from 'react'
import { renderToStaticMarkup } from 'react-dom/server'
import { afterAll, describe, expect, it } from 'vitest'
import { Creditos, Glosario } from '../src/secciones/fuentes/Fuentes'
import { leerTablas } from '../src/secciones/fuentes/tablas'
import { GLOSARIO } from '../src/textos/glosario'
import { alternar, idioma, t } from '../src/textos/i18n'
import { enEspanol } from './idioma_es'
enEspanol()

const leer = (nombre: string) => readFileSync(new URL(`../../../${nombre}`, import.meta.url), 'utf8')
// D-043 regla 2: solo estas columnas descriptivas se traducen; el resto debe ser idéntico byte a byte
const TRADUCIBLES = new Set(['Estado', 'Verificación', 'Dónde se usa'])

/** Compara dos registros: mismas tablas, filas, claves y orden; columnas no traducibles idénticas. */
export function paridad(es: string, en: string): string[] {
  const errores: string[] = []
  const [a, b] = [leerTablas(es), leerTablas(en)]
  if (a.length !== b.length) return [`tablas ${a.length} frente a ${b.length}`]
  a.forEach((ta, i) => {
    const tb = b[i]
    if (ta.columnas.length !== tb.columnas.length) errores.push(`${ta.titulo}: columnas`)
    if (ta.filas.length !== tb.filas.length) errores.push(`${ta.titulo}: filas ${ta.filas.length} frente a ${tb.filas.length}`)
    ta.filas.forEach((fa, n) => {
      const fb = tb.filas[n] ?? []
      fa.forEach((celda, c) => {
        if (!TRADUCIBLES.has(ta.columnas[c]) && celda !== fb[c]) errores.push(`${ta.titulo} fila ${n + 1} (${fa[0]}) columna ${ta.columnas[c]}`)
      })
    })
  })
  return errores
}

describe('registros en inglés (D-043)', () => {
  for (const f of ['LICENCIAS_TERCEROS', 'CITAS']) {
    it(`${f}.en.md tiene paridad con ${f}.md`, () => {
      expect(paridad(leer(`${f}.md`), leer(`${f}.en.md`))).toEqual([])
    })
  }
  it('la paridad falla si se agrega, quita o reordena una fila en un solo archivo', () => {
    const es = '# T\n\n| Fuente | Versión | Estado |\n|-|-|-|\n| A | 1 | en uso |\n| B | 2 | en uso |\n'
    expect(paridad(es, es.replace(/en uso/g, 'in use'))).toEqual([])
    expect(paridad(es, es + '| C | 3 | in use |\n')).not.toEqual([])
    expect(paridad(es, es.replace('| B | 2 | en uso |\n', ''))).not.toEqual([])
    expect(paridad(es, es.replace('| A | 1 | en uso |\n| B | 2 | en uso |', '| B | 2 | in use |\n| A | 1 | in use |'))).not.toEqual([])
    expect(paridad(es, es.replace('| 2 |', '| 2.1 |'))).not.toEqual([])
  })
})

describe('Fuentes en modo EN', () => {
  afterAll(() => { if (idioma() === 'en') alternar() })
  it('encabezados y estado de los créditos en inglés', () => {
    if (idioma() !== 'en') alternar()
    const html = renderToStaticMarkup(createElement(Creditos))
    expect(html).toContain('>Product<')
    expect(html).toContain('>Version<')
    expect(html).toContain('>License<')
    expect(html).toContain('>in use<')
    expect(html).not.toMatch(/>(Producto|Versión|Licencia|Cómo se cita|Estado|en uso)</)
  })
})

// "pendiente" como pendiente del terreno (slope) no es un aviso de dato faltante
const PENDIENTE = /pending|pendiente(?!s? (métrica|RUSLE|`S`))/i

describe('nada pendiente a la vista del público', () => {
  afterAll(() => { if (idioma() !== 'es') alternar() })
  for (const lang of ['es', 'en'] as const) {
    it(`Fuentes y ayuda en ${lang}`, () => {
      if (idioma() !== lang) alternar()
      const textos = [
        renderToStaticMarkup(createElement(Creditos)),
        renderToStaticMarkup(createElement(Glosario, { modo: 'agricultor' })),
        renderToStaticMarkup(createElement(Glosario, { modo: 'tecnico' })),
        ...GLOSARIO.map((g) => lang === 'en' ? `${g.termino_en ?? g.termino} ${g.en} ${g.tecnico_en} ${g.fuente_en ?? g.fuente}` : `${g.termino} ${g.es} ${g.tecnico} ${g.fuente}`),
        t('ayuda.titulo'), t('ayuda.intro'),
      ]
      // El contexto del hallazgo sale en el mensaje de la falla
      for (const x of textos) { const plano = x.replace(/<[^>]*>/g, ' '); const m = PENDIENTE.exec(plano); expect(m && plano.slice(Math.max(0, m.index - 60), m.index + 40)).toBeNull() }
    })
  }
  it('la ayuda en inglés no deja términos ni etiquetas en español', () => {
    const c = GLOSARIO.find((g) => g.termino === 'Condición de la tierra')!
    expect(c.termino_en).toBe('Land condition')
    expect(c.fuente_en).not.toMatch(/Definición|INFERENCIA/)
  })
})
