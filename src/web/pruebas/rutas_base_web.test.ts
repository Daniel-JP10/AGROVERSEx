// asistido por SI: Claude Code (Anthropic), prueba de que las fuentes tipográficas de tema.css siguen a la base de la compilación
import { execSync } from 'node:child_process'
import { existsSync, mkdtempSync, readdirSync, readFileSync, rmSync } from 'node:fs'
import { tmpdir } from 'node:os'
import { join } from 'node:path'
import { describe, expect, it } from 'vitest'

const RAIZ = join(__dirname, '..')

describe('fuentes tipográficas relativas a la base', () => {
  it('con base ./ el CSS las pide relativas y los archivos existen en la salida', () => {
    const salida = mkdtempSync(join(tmpdir(), 'agro-base-'))
    try {
      const env = { ...process.env, NODE_ENV: 'production', VITE_CONFIG_NATIVE_IGNORE_WARNING: 'true' }
      execSync(`npx vite build --base=./ --logLevel silent --outDir "${salida}" --emptyOutDir`, { cwd: RAIZ, env, stdio: 'pipe' })
      const css = readdirSync(join(salida, 'assets')).filter((n) => n.endsWith('.css')).map((n) => readFileSync(join(salida, 'assets', n), 'utf8')).join('\n')
      const urls = [...css.matchAll(/url\(\s*["']?([^"')]*ibm-plex-sans[^"')]*)/g)].map((m) => m[1])
      expect(urls.length).toBeGreaterThanOrEqual(2)
      for (const u of urls) {
        expect(u, u).not.toMatch(/^\//)
        expect(existsSync(join(salida, 'assets', u)), u).toBe(true)
      }
    } finally { rmSync(salida, { recursive: true, force: true }) }
  }, 180_000)
})
