// asistido por SI: Claude Code (Anthropic), prueba de textos prohibidos en los textos visibles de Web y Datos y, con PROHIBIDOS_DIST, en una compilación; ampliada en la fase 3 (W1) con la lista del director y la prueba de insignias
import { readdirSync, readFileSync, statSync } from 'node:fs'
import { basename, join, relative, sep } from 'node:path'
import { describe, expect, it } from 'vitest'
import { en } from '../src/textos/en'
import { es } from '../src/textos/es'
import * as glosario from '../src/textos/glosario'
import * as avisos from '../src/textos/avisos'
import { prohibidosEn } from './prohibidos'
import { ATRIBUCION } from '../src/globo/config'
import { enTodo, esTodo } from '../src/textos/indice'

function archivos(dir: string, filtro: RegExp): string[] {
  return readdirSync(dir).flatMap((n) => {
    const p = join(dir, n)
    return statSync(p).isDirectory() ? archivos(p, filtro) : filtro.test(n) ? [p] : []
  })
}

const SRC = join(__dirname, '..', 'src')

// Fase 3 (F3_COMUN, director 13:27): ninguno puede verse en pantalla. Sin bandera i: cada variante va escrita.
// "live" solo como palabra suelta (aria-live no cuenta). SIMULADO se prohíbe en la cabecera (marco_cabecera y E2E), no en los rótulos por valor
const PROHIBIDOS_F3: [string, RegExp][] = [
  ['NASA logo', /NASA logo|logo de la NASA|logo NASA/],
  ['ERA5', /ERA5/],
  ['GAEZ', /\bGAEZ\b/],
  ['CDL', /\bCDL\b/],
  ['live', /(?<![-\w])[Ll]ive\b/],
  ['en vivo', /[Ee]n vivo/],
  ['Telemetr', /[Tt]elemetr/],
  ['Salud del lote', /[Ss]alud del lote/],
  ['Lot health', /[Ll]ot health/],
  ['Pred.', /\bPred\./],
  ['fps', /\bfps\b/],
]
const prohibidosF3En = (t: string) => PROHIBIDOS_F3.filter(([, re]) => re.test(t)).map(([n]) => n)

// Claves de en.ts/es.ts (del orquestador) que hoy nombran CDL y que ninguna pantalla de la fase 3 usa; su retiro se pide
// en el reporte de W1. Una prueba falla cuando ya no lleven CDL, para que esta lista no quede vieja.
const PENDIENTES_ORQUESTADOR: readonly string[] = ['ciencia.metrica_suelo_desnudo', 'ciencia.pi_d2']
const todo = { ...enTodo } as Record<string, string>
const todoEs = { ...esTodo } as Record<string, string | undefined>
const textosPendientes = PENDIENTES_ORQUESTADOR.flatMap((k) => [todo[k], todoEs[k]].filter((x): x is string => !!x && prohibidosF3En(x).length > 0))

// Frase de una librería (scheduler de React) que solo va a la consola, nunca a la pantalla
const DE_LIBRERIAS = ['forcing frame rates higher than 125 fps is not supported']

// Nombres de archivo de insignia (se comparan en minúsculas)
const esInsigniaPorNombre = (nombre: string) => /meatball|insignia|nasa[-_ ]?logo/.test(nombre.toLowerCase())
// Un SVG (archivo o incrustado) con el azul #0B3D91 y el rojo #FC3D21 de la insignia
function svgConInsignia(texto: string): boolean {
  const t = texto.toLowerCase()
  return t.includes('<svg') && t.includes('#0b3d91') && t.includes('#fc3d21')
}

describe('textos prohibidos', () => {
  it('el detector marca cada nombre, también escapado, y deja pasar texto limpio', () => {
    expect(prohibidosEn('Límites GADM 4.1')).toEqual(['GADM'])
    expect(prohibidosEn('EOX Sentinel-2 cloudless')).toEqual(['EOX', 'cloudless'])
    expect(prohibidosEn('WorldClim y GAEZ')).toEqual(['WorldClim', 'GAEZ'])
    expect(prohibidosEn('Köppen-Geiger (Beck et al. 2023)')).toEqual(['Köppen-Geiger 2023'])
    expect(prohibidosEn('"K\\u00f6ppen-Geiger 2023"')).toEqual(['Köppen-Geiger 2023'])
    expect(prohibidosEn('"K\\xf6ppen-Geiger 2023"')).toEqual(['Köppen-Geiger 2023'])
    expect(prohibidosEn('Simulated IMERG climatology')).toEqual(['climatología IMERG simulada'])
    expect(prohibidosEn('"Climatología IMERG simulada"')).toEqual(['climatología IMERG simulada'])
    expect(prohibidosEn('boxes, geoBoundaries CGAZ, NASA GIBS')).toEqual([])
  })
  it('ningún texto visible de Web los contiene: textos, glosario y avisos', () => {
    expect(prohibidosEn(JSON.stringify([en, es, glosario, avisos]))).toEqual([])
  })
  it('ningún archivo de las rutas de Web los contiene (app, secciones salvo tierra, textos, ejemplos, paneles/comparador)', () => {
    const rutas = ['app', 'secciones', 'textos', 'ejemplos', join('paneles', 'comparador')].flatMap((d) => archivos(join(SRC, d), /\.(ts|tsx|css|json|html)$/))
      .filter((p) => !relative(SRC, p).split(sep).join('/').startsWith('secciones/tierra/'))
    expect(rutas.length).toBeGreaterThan(10)
    for (const p of rutas) expect(prohibidosEn(readFileSync(p, 'utf8')), relative(SRC, p)).toEqual([])
  })
  // Rutas de Datos (de la prueba de los PR #3 y #5): atribución del globo y literales de todos los .tsx, sin comentarios
  it('la atribución del globo y los literales de los .tsx de Datos no los contienen', () => {
    const sinComentarios = (t: string) => t.replace(/\/\*[\s\S]*?\*\//g, '').replace(/(^|[^:'"`])\/\/.*$/gm, '$1')
    expect(prohibidosEn(ATRIBUCION)).toEqual([])
    for (const p of archivos(SRC, /\.tsx$/)) expect(prohibidosEn(sinComentarios(readFileSync(p, 'utf8'))), relative(SRC, p)).toEqual([])
  })
  it('detector de la fase 3: marca cada término y deja pasar aria-live, palabras parecidas y texto limpio', () => {
    expect(prohibidosF3En('NASA logo')).toEqual(['NASA logo'])
    expect(prohibidosF3En('ERA5 reanalysis')).toEqual(['ERA5'])
    expect(prohibidosF3En('CDL-NASS / GAEZ')).toEqual(['GAEZ', 'CDL'])
    expect(prohibidosF3En('Live data')).toEqual(['live'])
    expect(prohibidosF3En('datos en vivo')).toEqual(['en vivo'])
    expect(prohibidosF3En('Telemetría')).toEqual(['Telemetr'])
    expect(prohibidosF3En('Salud del lote 82/100')).toEqual(['Salud del lote'])
    expect(prohibidosF3En('Lot health')).toEqual(['Lot health'])
    expect(prohibidosF3En('Pred. 9.0')).toEqual(['Pred.'])
    expect(prohibidosF3En('60 fps')).toEqual(['fps'])
    for (const limpio of ['aria-live="polite"', 'deliver olive lives', 'Predicted range', 'Model simulation', 'NASA POWER', 'fpsx']) expect(prohibidosF3En(limpio), limpio).toEqual([])
  })
  it('ningún texto visible (todas las claves EN y ES, glosario y cabecera de avisos) contiene un término de la fase 3', () => {
    const valores = [...Object.entries(todo), ...Object.entries(todoEs)]
      .filter(([k]) => !PENDIENTES_ORQUESTADOR.includes(k))
      .map(([k, v]) => `${k}: ${v}`)
    const terminos = glosario.GLOSARIO.flatMap((g) => [g.es, g.en, g.tecnico, g.tecnico_en, g.fuente])
    expect([...valores, ...terminos, avisos.BANDA].filter((v) => prohibidosF3En(v).length)).toEqual([])
  })
  it('la lista de pendientes del orquestador sigue vigente (si falla, quítala: ya se retiraron)', () => {
    expect(textosPendientes.length).toBeGreaterThan(0)
  })
  it('los archivos de W1 (marco, portada, ciencia, datos abiertos, fuentes y sus textos) no contienen términos de la fase 3', () => {
    const rutas = [join('app', 'marco'), join('secciones', 'portada'), join('secciones', 'ciencia'), join('secciones', 'datos-abiertos'), join('secciones', 'fuentes')]
      .flatMap((d) => archivos(join(SRC, d), /\.(ts|tsx|css|json)$/))
    const textos = ['marco', 'portada', 'ciencia', 'datos', 'fuentes'].map((n) => join(SRC, 'textos', 'secciones', `${n}.ts`))
    expect(rutas.length).toBeGreaterThan(5)
    for (const p of [...rutas, ...textos]) expect(prohibidosF3En(readFileSync(p, 'utf8')), relative(SRC, p)).toEqual([])
  })
  it('detector de insignias: por nombre y por los colores del logo dentro de un SVG', () => {
    for (const n of ['meatball.svg', 'NASA_logo.png', 'nasa-logo.webp', 'insignia_nasa.svg', 'Nasa-Logo.svg']) expect(esInsigniaPorNombre(n), n).toBe(true)
    for (const n of ['globo.webp', 'bloque_DEMO-COL-01.webp', 'nasa_power.json']) expect(esInsigniaPorNombre(n), n).toBe(false)
    expect(svgConInsignia('<svg><circle fill="#0B3D91"/><path fill="#FC3D21"/></svg>')).toBe(true)
    expect(svgConInsignia('<svg><path fill="#7be0a0"/></svg>')).toBe(false)
  })
  // Compuerta de despliegue (T-W4): PROHIBIDOS_DIST=<carpeta del build> revisa todo lo que se publicaría
  it.runIf(!!process.env.PROHIBIDOS_DIST)('la compilación indicada en PROHIBIDOS_DIST no contiene ninguno', () => {
    const dist = process.env.PROHIBIDOS_DIST!
    const hallados = archivos(dist, /\.(js|css|html|json|txt|svg)$/).flatMap((p) => prohibidosEn(readFileSync(p, 'utf8')).map((n) => `${relative(dist, p)}: ${n}`))
    expect(hallados).toEqual([])
  })
  // El CSS no se revisa con la lista de la fase 3: sus nombres de clase no se ven (el texto renderizado lo cubre el E2E)
  it.runIf(!!process.env.PROHIBIDOS_DIST)('la compilación no contiene términos de la fase 3 en su texto (js, html, json, txt, svg)', () => {
    const dist = process.env.PROHIBIDOS_DIST!
    const limpiar = (t: string) => [...textosPendientes, ...DE_LIBRERIAS].reduce((a, x) => a.split(x).join(' '), t)
    const hallados = archivos(dist, /\.(js|mjs|html|json|txt|svg)$/).flatMap((p) => prohibidosF3En(limpiar(readFileSync(p, 'utf8'))).map((n) => `${relative(dist, p)}: ${n}`))
    expect(hallados).toEqual([])
  })
  it.runIf(!!process.env.PROHIBIDOS_DIST)('ningún asset de la compilación es una insignia de NASA (nombre o SVG con sus colores)', () => {
    const dist = process.env.PROHIBIDOS_DIST!
    expect(archivos(dist, /./).filter((p) => esInsigniaPorNombre(basename(p))).map((p) => relative(dist, p))).toEqual([])
    expect(archivos(dist, /\.(svg|js|mjs|html|css)$/).filter((p) => svgConInsignia(readFileSync(p, 'utf8'))).map((p) => relative(dist, p))).toEqual([])
  })
})
