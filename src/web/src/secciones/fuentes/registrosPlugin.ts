// asistido por SI: Claude Code (Anthropic), plugin de Vite que filtra los registros al compilar; lo registra el integrador en vite.config.ts
import { readFileSync } from 'node:fs'
import { soloEnUso, soloHerramientaArchivo } from './registros'

// Intercepta los ?raw de los tres registros que importa tablas.ts y entrega solo lo que Fuentes publica
// Tipo escrito a mano: importar Plugin de vite cambia la resolución de tipos de server/ (de Daniel) y rompe tsc
export function registrosEnUso(): { name: string; enforce: 'pre'; load(id: string): string | null } {
  return {
    name: 'agroversex-registros-en-uso',
    enforce: 'pre',
    load(id: string) {
      const m = /[\\/](LICENCIAS_TERCEROS|CITAS|SI_USO)\.md\?raw$/.exec(id)
      if (!m) return null
      const md = readFileSync(id.slice(0, -'?raw'.length), 'utf8')
      return `export default ${JSON.stringify(m[1] === 'SI_USO' ? soloHerramientaArchivo(md) : soloEnUso(md))}`
    },
  }
}
