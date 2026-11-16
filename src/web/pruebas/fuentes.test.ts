// asistido por SI: Claude Code (Anthropic), pruebas de la sección Fuentes: glosario, modos, créditos y declaración de SI; sin fuente pendiente (cierre)
import { readFileSync } from 'node:fs'
import { createElement } from 'react'
import { renderToStaticMarkup } from 'react-dom/server'
import { sinRutaLocal } from '../src/secciones/fuentes/rutasLocales'
import { describe, expect, it } from 'vitest'
import { Creditos, DeclaracionSI, Fuentes, Glosario } from '../src/secciones/fuentes/Fuentes'
import { leerTablas, resumenSI } from '../src/secciones/fuentes/tablas'
import { TERMINOS } from '../src/textos/glosario'
import { en, type ClaveTexto } from '../src/textos/en'
import { es } from '../src/textos/es'
import { alternar, idioma, t } from '../src/textos/i18n'
import { enEspanol } from './idioma_es'
enEspanol()

const leer = (nombre: string) => readFileSync(new URL(`../../../${nombre}`, import.meta.url), 'utf8')
const escapar = (s: string) => s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;').replace(/'/g, '&#x27;')
const sinEtiquetas = (h: string) => h.replace(/<[^>]*>/g, '')
// Número suelto: no cuenta el que forma parte de un nombre como ET0, FAO-56 o p10
const NUMERO = /(?<![\w-])\d+(?:[.,]\d+)?(?![\w-])/g
const numeros = (h: string) => sinEtiquetas(h).match(NUMERO) ?? []

describe('tablas de markdown', () => {
  const md = '# Título\n\n| A | B |\n|-|-|\n| 1 | dos |\n| tres | |\n\n## Otra\n\n| X |\n|-|\n| y |\n'
  it('lee título, columnas y filas, también con celdas vacías', () => {
    expect(leerTablas(md)).toEqual([
      { titulo: 'Título', columnas: ['A', 'B'], filas: [['1', 'dos'], ['tres', '']] },
      { titulo: 'Otra', columnas: ['X'], filas: [['y']] },
    ])
  })
  it('las filas reales de los tres archivos tienen tantas celdas como su encabezado', () => {
    for (const f of ['LICENCIAS_TERCEROS.md', 'CITAS.md', 'SI_USO.md']) {
      const tablas = leerTablas(leer(f))
      expect(tablas.length, f).toBeGreaterThan(0)
      for (const tb of tablas) for (const fila of tb.filas) expect(fila.length, `${f} ${tb.titulo} ${fila[0]}`).toBe(tb.columnas.length)
    }
  })
  it('resumenSI cuenta archivos distintos por herramienta', () => {
    const si = '| Herramienta | Archivo | Propósito | Fecha |\n|-|-|-|-|\n| A | `x.ts` | p | d |\n| A | `x.ts` | p | d |\n| A | `y.ts` | p | d |\n| B | `z.ts` | p | d |\n'
    expect(resumenSI(si)).toEqual([{ herramienta: 'A', archivos: 2 }, { herramienta: 'B', archivos: 1 }])
  })
  it('resumenSI recorre todas las tablas con Herramienta y Archivo e ignora las demás', () => {
    const enc = '| Herramienta | Archivo | Propósito | Fecha |\n|-|-|-|-|\n'
    const si = `# Uno\n\n${enc}| A | \`x.ts\` | p | d |\n\n## Otra\n\n| Nota |\n|-|\n| Z |\n\n## Dos\n\n${enc}| A | \`y.ts\` | p | d |\n| B | \`z.ts\` | p | d |\n`
    expect(resumenSI(si)).toEqual([{ herramienta: 'A', archivos: 2 }, { herramienta: 'B', archivos: 1 }])
  })
  it('resumenSI sobre el SI_USO.md real cuenta los pares herramienta+archivo de todas las tablas', () => {
    // Conteo independiente: recorre las líneas y filtra por encabezado, sin leerTablas
    const pares = new Set<string>()
    const primera = new Set<string>()
    let cols: string[] | null = null
    let n = 0
    for (const l of leer('SI_USO.md').split(/\r?\n/)) {
      if (!l.startsWith('|')) { cols = null; continue }
      if (/^\|[-| :]+\|$/.test(l)) continue
      const c = l.replace(/^\||\|\s*$/g, '').split('|').map((x) => x.trim())
      if (cols === null) { cols = c; n++; continue }
      const [h, a] = [cols.indexOf('Herramienta'), cols.indexOf('Archivo')]
      if (h < 0 || a < 0) continue
      pares.add(`${c[h]}\u0000${c[a]}`)
      if (n === 1) primera.add(`${c[h]}\u0000${c[a]}`)
    }
    const total = resumenSI(leer('SI_USO.md')).reduce((s, r) => s + r.archivos, 0)
    expect(total).toBe(pares.size)
    expect(total).toBeGreaterThan(primera.size)
  })
})

describe('créditos: solo las filas en uso de LICENCIAS_TERCEROS.md y de CITAS.md', () => {
  // Cuenta independiente del parser: filas cuya columna Estado empieza por "en uso"
  const enUso = (md: string) => {
    let col = -1
    const nombres: string[] = []
    for (const l of md.split(/\r?\n/)) {
      if (!l.startsWith('|')) { col = -1; continue }
      if (/^\|[-| :]+\|$/.test(l)) continue
      const c = l.replace(/^\||\|\s*$/g, '').split('|').map((x) => x.trim())
      if (col === -1) { col = c.indexOf('Estado'); if (col === -1) col = -2; continue }
      if (col >= 0 && /^en uso\b/i.test(c[col] ?? '')) nombres.push(c[0])
    }
    return nombres
  }
  const filas = [...enUso(leer('LICENCIAS_TERCEROS.md')), ...enUso(leer('CITAS.md'))]

  it('pinta exactamente las filas en uso, cada una por nombre', () => {
    const html = renderToStaticMarkup(createElement(Creditos))
    expect((html.match(/<tr data-fila/g) ?? []).length).toBe(filas.length)
    // Una celda con ruta local se publica vacía (rutasLocales.ts); el resto de nombres aparece tal cual
    for (const n of filas.filter(sinRutaLocal)) expect(html, n).toContain(escapar(n))
  })
})

describe('declaración de uso de SI generada desde SI_USO.md', () => {
  it('lista cada herramienta con el número de archivos contado del archivo', () => {
    const filas = leerTablas(leer('SI_USO.md')).filter((t) => t.columnas[0] === 'Herramienta' && t.columnas[1] === 'Archivo').flatMap((t) => t.filas)
    const porHerramienta = new Map<string, Set<string>>()
    for (const [h, a] of filas) porHerramienta.set(h, (porHerramienta.get(h) ?? new Set()).add(a))
    expect(porHerramienta.size).toBeGreaterThan(0)
    const texto = sinEtiquetas(renderToStaticMarkup(createElement(DeclaracionSI)))
    for (const [h, archivos] of porHerramienta) expect(texto).toMatch(new RegExp(`${escapar(h).replace(/[()]/g, '\\$&')}[^0-9]*${archivos.size}(?![0-9])`))
  })
})

describe('glosario de ocho términos', () => {
  const claves = (id: string, campos: string[]) => campos.map((c) => `glosario.${id}.${c}` as ClaveTexto)
  it('son ocho, y cada uno tiene nombre y texto de agricultor y técnico en los dos idiomas', () => {
    expect(TERMINOS.map((x) => x.id)).toEqual(['et', 'humedad', 'ndvi', 'helada', 'balance', 'incertidumbre', 'confianza'])
    for (const { id } of TERMINOS) for (const k of claves(id, ['nombre', 'agricultor', 'tecnico'])) {
      expect(en[k], k).toBeTruthy()
      expect(es[k], k).toBeTruthy()
    }
  })
  it('ningún texto del glosario lleva un número suelto escrito a mano', () => {
    for (const { id } of TERMINOS) for (const k of claves(id, ['nombre', 'agricultor', 'tecnico'])) {
      expect(en[k], k).not.toMatch(NUMERO)
      expect(es[k] ?? '', k).not.toMatch(NUMERO)
    }
  })
  it('cada término cita su fuente y ninguno queda como "Source pending" (orden del director, cierre)', () => {
    alternar()
    try {
      expect(idioma()).toBe('en')
      const html = renderToStaticMarkup(createElement(Glosario))
      expect(html).not.toContain('Source pending')
      for (const x of TERMINOS) expect(html).toContain(escapar(en[x.fuente]))
    } finally { alternar() }
  })
  it('cada fuente con url enlaza a su fuente primaria por https', () => {
    const html = renderToStaticMarkup(createElement(Glosario))
    const conUrl = TERMINOS.filter((x) => x.url)
    expect(conUrl.length).toBeGreaterThan(0)
    for (const x of conUrl) {
      expect(x.url).toMatch(/^https:\/\//)
      expect(html).toContain(`href="${escapar(x.url!)}"`)
    }
  })
  it('en español no dice "Fuente pendiente"', () => {
    expect(renderToStaticMarkup(createElement(Glosario))).not.toContain('Fuente pendiente')
  })
})

describe('el modo cambia el texto, nunca los datos', () => {
  const resolver = (n: string) => ({ unidad_et: '12', producto_et: 'PROD', periodo_base: '34' })[n]
  const glosario = (modo: 'agricultor' | 'tecnico') => renderToStaticMarkup(createElement(Glosario, { resolver, modo }))

  it('los números del modo agricultor están todos en el modo técnico y el técnico solo agrega los de los datos', () => {
    const a = numeros(glosario('agricultor'))
    const b = numeros(glosario('tecnico'))
    for (const n of a) expect(b).toContain(n)
    expect(b.length).toBeGreaterThan(a.length)
    expect([...new Set(b)].sort()).toEqual(['12', '34'])
  })
  it('el texto de agricultor es el comienzo del técnico', () => {
    expect(sinEtiquetas(glosario('tecnico')).length).toBeGreaterThan(sinEtiquetas(glosario('agricultor')).length)
    for (const { id } of TERMINOS) expect(glosario('tecnico')).toContain(escapar(es[`glosario.${id}.agricultor` as ClaveTexto]!))
  })
  it('sin fuentes de datos no hay ningún número suelto en ninguno de los dos modos', () => {
    for (const m of ['agricultor', 'tecnico'] as const) expect(numeros(renderToStaticMarkup(createElement(Glosario, { modo: m }))), m).toEqual([])
  })
  it('el modo técnico marca los huecos sin dato y el agricultor no muestra ninguno', () => {
    expect(renderToStaticMarkup(createElement(Glosario, { modo: 'tecnico' }))).toContain(t('aviso.sin_dato'))
    expect(renderToStaticMarkup(createElement(Glosario, { modo: 'agricultor' }))).not.toContain(t('aviso.sin_dato'))
  })
  it('la sección tiene su h1 y las tres columnas: fuentes, glosario y créditos (el modo va en la cabecera)', () => {
    const html = renderToStaticMarkup(createElement(Fuentes))
    expect(html).toContain('<h1>Fuentes, glosario y créditos</h1>')
    expect((html.match(/<section class="tarjeta-hoja"/g) ?? []).length).toBe(3)
    for (const marca of ['class="glosario"', 'id="creditos"', 'data-testid="declaracion-si"', 'data-credito=""']) expect(html).toContain(marca)
  })
  it('créditos: director, diseño y gemelo (director 21:35), y el diseño a mano declarado', () => {
    const html = renderToStaticMarkup(createElement(Fuentes))
    for (const c of ['Director: Daniel Andres Jimenez Povea', 'Diseño: Jostin Andres Colon Ramos', 'Gemelo digital: Emmanuel Ascendra Perez']) expect(html).toContain(c)
    expect(html).not.toContain('Dirección visual')
    expect(html).toContain('El diseño visual lo dibujó a mano el equipo')
  })
})
