// asistido por SI: Claude Code (Anthropic), prueba de la bandera VITE_EJEMPLOS (contrato web_componentes §9)
import { execSync } from 'node:child_process'
import { mkdtempSync, readdirSync, readFileSync, rmSync } from 'node:fs'
import { tmpdir } from 'node:os'
import { join } from 'node:path'
import { describe, expect, it } from 'vitest'
import { MARCADOR_EJEMPLOS } from '../src/ejemplos'

const RAIZ = join(__dirname, '..')

// Compila de verdad y devuelve todo el texto de la salida
function compilar(flag: string | undefined): string {
  const salida = mkdtempSync(join(tmpdir(), 'agro-build-'))
  try {
    const env: Record<string, string | undefined> = { ...process.env, NODE_ENV: 'production', VITE_CONFIG_NATIVE_IGNORE_WARNING: 'true' }
    if (flag === undefined) delete env.VITE_EJEMPLOS; else env.VITE_EJEMPLOS = flag
    execSync(`npx vite build --logLevel silent --outDir "${salida}" --emptyOutDir`, { cwd: RAIZ, env: env as NodeJS.ProcessEnv, stdio: 'pipe' })
    const leer = (d: string): string => readdirSync(d, { withFileTypes: true })
      .map((e) => (e.isDirectory() ? leer(join(d, e.name)) : /\.(js|css|html)$/.test(e.name) ? readFileSync(join(d, e.name), 'utf8') : '')).join('\n')
    return leer(salida)
  } finally { rmSync(salida, { recursive: true, force: true }) }
}

describe('bandera VITE_EJEMPLOS', () => {
  it('sin la bandera la versión pública no contiene el marcador de los ejemplos', () => {
    expect(compilar(undefined)).not.toContain(MARCADOR_EJEMPLOS)
  }, 180_000)
  it('con VITE_EJEMPLOS=1 el marcador sí está (la comprobación puede detectarlo)', () => {
    expect(compilar('1')).toContain(MARCADOR_EJEMPLOS)
  }, 180_000)
})
