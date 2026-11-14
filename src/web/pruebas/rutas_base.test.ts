// asistido por SI: Claude Code (Anthropic), prueba de que teselas e índice respetan la base de publicación (BASE_URL)
import { execSync } from 'node:child_process'
import { mkdtempSync, readdirSync, readFileSync, rmSync } from 'node:fs'
import { tmpdir } from 'node:os'
import { join } from 'node:path'
import { describe, expect, it } from 'vitest'

const RAIZ = join(__dirname, '..')
const BASE = '/base-de-prueba/'
// Una ruta de teselas absoluta, sin la base delante, dentro de una cadena del bundle
const ABSOLUTA = /[`'"]\/teselas\//

// Compila de verdad con una base de publicación y devuelve el JS de la salida
function compilarConBase(): string {
  const salida = mkdtempSync(join(tmpdir(), 'agro-base-'))
  try {
    const env = { ...process.env, NODE_ENV: 'production', VITE_CONFIG_NATIVE_IGNORE_WARNING: 'true' }
    execSync(`npx vite build --logLevel silent --base=${BASE} --outDir "${salida}" --emptyOutDir`, { cwd: RAIZ, env, stdio: 'pipe' })
    const leer = (d: string): string => readdirSync(d, { withFileTypes: true })
      .map((e) => (e.isDirectory() ? leer(join(d, e.name)) : /\.(js|mjs)$/.test(e.name) ? readFileSync(join(d, e.name), 'utf8') : '')).join('\n')
    return leer(salida)
  } finally { rmSync(salida, { recursive: true, force: true }) }
}

describe('rutas de teselas e índice con BASE_URL', () => {
  it('el detector marca una ruta absoluta y deja pasar una con base', () => {
    expect('archivo:`/teselas/adm0.pmtiles`').toMatch(ABSOLUTA)
    expect(`archivo:\`${BASE}teselas/adm0.pmtiles\``).not.toMatch(ABSOLUTA)
  })
  it('compilado con otra base, ninguna ruta de teselas ni del índice queda absoluta', () => {
    const js = compilarConBase()
    expect(js).not.toMatch(ABSOLUTA)
    // El minificador puede dejar el prefijo en una constante y unirlo con plantilla: se comprueban por separado
    expect(js).toContain(`${BASE}teselas/`)
    for (const f of ['adm0.pmtiles', 'adm1.pmtiles', 'adm2.pmtiles', 'indice_busqueda.json.gz']) expect(js).toContain(f)
  }, 180_000)
})
