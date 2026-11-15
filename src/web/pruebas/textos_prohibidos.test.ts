// asistido por SI: Claude Code (Anthropic), prueba de textos prohibidos en los textos visibles de Web y Datos y, con PROHIBIDOS_DIST, en una compilación
import { readdirSync, readFileSync, statSync } from 'node:fs'
import { join, relative, sep } from 'node:path'
import { describe, expect, it } from 'vitest'
import { en } from '../src/textos/en'
import { es } from '../src/textos/es'
import * as glosario from '../src/textos/glosario'
import * as avisos from '../src/textos/avisos'
import { prohibidosEn } from './prohibidos'
import { ATRIBUCION } from '../src/globo/config'

function archivos(dir: string, filtro: RegExp): string[] {
  return readdirSync(dir).flatMap((n) => {
    const p = join(dir, n)
    return statSync(p).isDirectory() ? archivos(p, filtro) : filtro.test(n) ? [p] : []
  })
}

const SRC = join(__dirname, '..', 'src')

describe('textos prohibidos', () => {
  it('el detector marca cada nombre, también escapado, y deja pasar texto limpio', () => {
    expect(prohibidosEn('Límites GADM 4.1')).toEqual(['GADM'])
    expect(prohibidosEn('EOX Sentinel-2 cloudless')).toEqual(['EOX', 'cloudless'])
    expect(prohibidosEn('WorldClim y GAEZ')).toEqual(['WorldClim', 'GAEZ'])
    expect(prohibidosEn('Köppen-Geiger (Beck et al. 2023)')).toEqual(['Köppen-Geiger 2023'])
    expect(prohibidosEn('"K\\u00f6ppen-Geiger 2023"')).toEqual(['Köppen-Geiger 2023'])
    expect(prohibidosEn('"K\\xf6ppen-Geiger 2023"')).toEqual(['Köppen-Geiger 2023'])
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
  // Compuerta de despliegue (T-W4): PROHIBIDOS_DIST=<carpeta del build> revisa todo lo que se publicaría
  it.runIf(!!process.env.PROHIBIDOS_DIST)('la compilación indicada en PROHIBIDOS_DIST no contiene ninguno', () => {
    const dist = process.env.PROHIBIDOS_DIST!
    const hallados = archivos(dist, /\.(js|css|html|json|txt|svg)$/).flatMap((p) => prohibidosEn(readFileSync(p, 'utf8')).map((n) => `${relative(dist, p)}: ${n}`))
    expect(hallados).toEqual([])
  })
})
