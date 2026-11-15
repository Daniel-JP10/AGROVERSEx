// asistido por SI: Claude Code (Anthropic), pruebas del filtro de registros de Fuentes y del plugin que lo aplica al compilar
import { readFileSync } from 'node:fs'
import { join } from 'node:path'
import { describe, expect, it } from 'vitest'
import { soloEnUso, soloHerramientaArchivo } from '../src/secciones/fuentes/registros'
import { registrosEnUso } from '../src/secciones/fuentes/registrosPlugin'
import { prohibidosEn } from './prohibidos'

const RAIZ = join(__dirname, '..', '..', '..')
const MD = '# Datos\n\nFuera por licencia: GADM.\n\n| Producto | Licencia | Estado |\n|-|-|-|\n| A | CC0 | en uso |\n| B | NC | excluido |\n| C | CC BY | En uso (VERIFICADO) |\n\n## Sin estado\n\n| X |\n|-|\n| y |\n'

describe('filtro de registros', () => {
  it('deja encabezados y solo las filas en uso; quita la prosa y las tablas sin Estado', () => {
    const s = soloEnUso(MD)
    expect(s).toContain('| A | CC0 | en uso |')
    expect(s).toContain('| C | CC BY | En uso (VERIFICADO) |')
    expect(s).not.toContain('| B |')
    expect(s).not.toContain('GADM')
    expect(s).not.toContain('| y |')
  })
  it('de SI_USO solo quedan herramienta y archivo', () => {
    const s = soloHerramientaArchivo('# Uso\n\n| Herramienta | Archivo | Propósito | Fecha |\n|-|-|-|-|\n| T | `a.py` | límites GADM | d |\n')
    expect(s).toContain('| T | `a.py` |')
    expect(s).not.toContain('GADM')
  })
  it('el plugin entrega los tres registros reales filtrados y sin textos prohibidos', () => {
    const load = registrosEnUso().load as (id: string) => string | null
    expect(load('/x/otra.md?raw')).toBeNull()
    for (const f of ['LICENCIAS_TERCEROS.md', 'CITAS.md', 'SI_USO.md']) {
      const salida = load(join(RAIZ, f) + '?raw')!
      expect(salida, f).toMatch(/^export default "/)
      expect(prohibidosEn(salida), f).toEqual([])
    }
    expect(prohibidosEn(readFileSync(join(RAIZ, 'LICENCIAS_TERCEROS.md'), 'utf8')).length).toBeGreaterThan(0)
  })
})
