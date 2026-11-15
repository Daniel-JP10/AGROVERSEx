// asistido por SI: Claude Code (Anthropic), prueba de que ejemplo_gemelo.json solo entra a la compilación con VITE_EJEMPLOS=1
import { execSync } from 'node:child_process'
import { mkdtempSync, readdirSync, readFileSync, rmSync } from 'node:fs'
import { tmpdir } from 'node:os'
import { join } from 'node:path'
import { describe, expect, it } from 'vitest'
import ejemplo from '../src/secciones/rotaciones/ejemplo_gemelo.json'
import textos from '../src/secciones/rotaciones/ejemplo_textos_gemelo.json'

const RAIZ = join(__dirname, '..')
const MARCA = ejemplo.metadatos.archivo_entrada
const TEXTO_EJEMPLO = textos.en['warning.example_simulated']

function compilar(flag: string | undefined): string {
  const salida = mkdtempSync(join(tmpdir(), 'agro-rot-'))
  try {
    const env: Record<string, string | undefined> = { ...process.env, NODE_ENV: 'production', VITE_CONFIG_NATIVE_IGNORE_WARNING: 'true' }
    if (flag === undefined) delete env.VITE_EJEMPLOS; else env.VITE_EJEMPLOS = flag
    execSync(`npx vite build --logLevel silent --outDir "${salida}" --emptyOutDir`, { cwd: RAIZ, env: env as NodeJS.ProcessEnv, stdio: 'pipe' })
    const leer = (d: string): string => readdirSync(d, { withFileTypes: true })
      .map((e) => (e.isDirectory() ? leer(join(d, e.name)) : /\.(js|css|html|json)$/.test(e.name) ? readFileSync(join(d, e.name), 'utf8') : '')).join('\n')
    return leer(salida)
  } finally { rmSync(salida, { recursive: true, force: true }) }
}

describe('ejemplo del gemelo y la bandera', () => {
  it('la marca del ejemplo es distinguible', () => {
    expect(MARCA).toMatch(/AGROVERSEX_EJEMPLO_GEMELO/)
  })
  it('sin la bandera la versión pública no contiene el ejemplo ni su catálogo de textos', () => {
    const s = compilar(undefined)
    expect(s).not.toContain(MARCA)
    expect(s).not.toContain(TEXTO_EJEMPLO)
  }, 180_000)
  it('con VITE_EJEMPLOS=1 el ejemplo y su catálogo sí están (la comprobación puede detectarlo)', () => {
    const s = compilar('1')
    expect(s).toContain(MARCA)
    expect(s).toContain(TEXTO_EJEMPLO)
  }, 180_000)
})
