// asistido por SI: Claude Code (Anthropic), prueba de la frontera entre el código de Web y el de Daniel
import { readdirSync, readFileSync, statSync } from 'node:fs'
import { join, relative, sep } from 'node:path'
import { describe, expect, it } from 'vitest'

const SRC = join(__dirname, '..', 'src')
// destino sale resuelto desde src/, así que el anclaje es la raíz: secciones/rotaciones/datos es de Web
const PROHIBIDOS = /^(globo|paneles|datos|tiempo|comparar|herramientas)(\/|$)|^app\/estado$/

// Archivos de Web: src/app salvo estado.ts, src/secciones/* salvo tierra, src/textos y src/ejemplos
function archivosDeWeb(): string[] {
  const salida: string[] = []
  const rec = (d: string) => {
    for (const n of readdirSync(d)) {
      const p = join(d, n)
      if (statSync(p).isDirectory()) { rec(p); continue }
      const r = relative(SRC, p).split(sep).join('/')
      if (!/\.(ts|tsx)$/.test(r) || r === 'app/estado.ts' || r.startsWith('secciones/tierra/')) continue
      salida.push(r)
    }
  }
  for (const d of ['app', 'secciones', 'textos', 'ejemplos']) rec(join(SRC, d))
  return salida
}

// Especificadores relativos (import, import() y export from) que cruzan la frontera
function importsProhibidos(archivo: string, fuente: string): string[] {
  const dir = archivo.split('/').slice(0, -1)
  const malos: string[] = []
  for (const m of fuente.matchAll(/(?:from|import)\s*\(?\s*['"]([^'"]+)['"]/g)) {
    if (!m[1].startsWith('.')) continue
    const partes = [...dir]
    let fuera = false // sube más allá de src/: es un archivo del repo (datos/ de la raíz), no una carpeta de src
    for (const s of m[1].split('/')) { if (s === '..') { if (!partes.length) fuera = true; partes.pop() } else if (s !== '.') partes.push(s) }
    if (fuera) continue
    const destino = partes.join('/')
    const otraDeTierra = destino.startsWith('secciones/tierra/') && !/^secciones\/tierra\/(Tierra|interfaz)$/.test(destino)
    if (PROHIBIDOS.test(destino) || otraDeTierra) malos.push(m[1])
  }
  return malos
}

describe('frontera con las carpetas de Daniel', () => {
  it('el detector marca los cruces y deja pasar lo permitido', () => {
    expect(importsProhibidos('app/X.tsx', `import { u } from './estado'`)).toHaveLength(1)
    expect(importsProhibidos('secciones/gemelo/G.tsx', `import { u } from '../../app/estado'`)).toHaveLength(1)
    expect(importsProhibidos('app/X.tsx', `const m = await import('../globo/Globo')`)).toHaveLength(1)
    expect(importsProhibidos('secciones/ciencia/d.ts', `import x from '../../../../../datos/lotes/a.json'`)).toHaveLength(0)
    expect(importsProhibidos('secciones/ciencia/d.ts', `import x from '../../datos/series'`)).toHaveLength(1)
    expect(importsProhibidos('secciones/gemelo/G.tsx', `export { a } from '../../datos/series'`)).toHaveLength(1)
    expect(importsProhibidos('secciones/gemelo/G.tsx', `import { a } from '../tierra/Riel'`)).toHaveLength(1)
    expect(importsProhibidos('app/App.tsx', `import { Tierra } from '../secciones/tierra/Tierra'\nimport { t } from '../textos/i18n'\nimport { n } from './ruta'`)).toHaveLength(0)
    expect(importsProhibidos('app/X.tsx', `import { i } from '../secciones/tierra/interfaz'`)).toHaveLength(0)
  })
  it('ningún archivo de Web importa de globo, paneles, datos, tiempo, comparar, herramientas ni app/estado', () => {
    const archivos = archivosDeWeb()
    expect(archivos.length).toBeGreaterThan(10)
    for (const a of archivos) expect(importsProhibidos(a, readFileSync(join(SRC, a), 'utf8')), a).toEqual([])
  })
})
