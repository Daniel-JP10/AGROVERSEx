// asistido por SI: Claude Code (Anthropic), prueba de fugas de rutas locales en el texto de dist y en las filas que muestra Fuentes
import { readdirSync, readFileSync, statSync } from 'node:fs'
import { join, relative } from 'node:path'
import { describe, expect, it } from 'vitest'
import { CITAS, LICENCIAS } from '../src/secciones/fuentes/tablas'
import { rutaLocalEn } from '../src/secciones/fuentes/rutasLocales'

// Solo archivos de texto: los binarios (webp, woff2, pmtiles) no se revisan
const TEXTO = /\.(js|mjs|css|html|json|txt|svg|map|webmanifest|xml|csv|md)$/

function archivos(dir: string): string[] {
  return readdirSync(dir).flatMap((n) => {
    const p = join(dir, n)
    return statSync(p).isDirectory() ? archivos(p) : TEXTO.test(n) ? [p] : []
  })
}

describe('detector de rutas locales', () => {
  it('marca letras de unidad, carpetas de sistema, rutas UNC y la carpeta de despliegue', () => {
    for (const malo of [
      'C:/NASA/x', 'C:\\NASA\\x', 'X:/datos', 'd:\\a', '"C:/NASA/herramientas-despliegue"', 'ver (Z:/r)',
      '/mnt/c/datos', '/tmp/a.json', '/root/.cache', '/Users/ana/x', '\\\\servidor\\compartido', '"\\\\\\\\servidor\\\\c"',
      'herramientas-despliegue', '`E:\\\\carpeta`',
    ]) expect(rutaLocalEn(malo), malo).not.toBeNull()
  })
  it('deja pasar URLs, protocolos, código minificado y texto normal', () => {
    for (const bueno of [
      'https://earthdata.nasa.gov/x', 'http://localhost:5198/', 'data:image/svg+xml,%3Csvg', 'mailto:a@b.c',
      'a?b:c', 'x={a:1,b:2}', 'ratio 1:2', 'NASA POWER 2001-2024', 'Daniel-JP10/agroversex-teselas', 'ODbL 1.0',
      '/datos/manifiesto.json', 'users', 'tmp', 'C: drive', 'Users/', 'aria-live', '\\d+\\s',
    ]) expect(rutaLocalEn(bueno), bueno).toBeNull()
  })
})

describe('Fuentes no muestra rutas locales', () => {
  it('ninguna celda de LICENCIAS ni de CITAS que se publica lleva una ruta local', () => {
    const celdas = [...LICENCIAS, ...CITAS].flatMap((t) => [t.titulo, ...t.columnas, ...t.filas.flat()])
    expect(celdas.length).toBeGreaterThan(10)
    expect(celdas.filter((c) => rutaLocalEn(c) !== null)).toEqual([])
  })
})

// PROHIBIDOS_DIST=<carpeta del build> revisa todo el texto que se publicaría (T-W4)
describe.runIf(!!process.env.PROHIBIDOS_DIST)('dist sin rutas locales', () => {
  it('ningún archivo de texto de la compilación contiene una ruta local', () => {
    const dist = process.env.PROHIBIDOS_DIST!
    const lista = archivos(dist)
    expect(lista.length).toBeGreaterThan(3)
    const hallados = lista.flatMap((p) => {
      const t = readFileSync(p, 'utf8')
      const m = rutaLocalEn(t)
      return m ? [`${relative(dist, p)}: ${JSON.stringify(t.slice(Math.max(0, m.indice - 30), m.indice + 40))}`] : []
    })
    expect(hallados).toEqual([])
  })
})
