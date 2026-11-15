// asistido por SI: Claude Code (Anthropic), lee en compilación LICENCIAS_TERCEROS.md, CITAS.md y SI_USO.md y los parsea a filas
import citasMd from '../../../../../CITAS.md?raw'
import licenciasMd from '../../../../../LICENCIAS_TERCEROS.md?raw'
import usoSiMd from '../../../../../SI_USO.md?raw'
import { soloEnUso } from './registros'

export interface Tabla { titulo: string; columnas: string[]; filas: string[][] }

/** Cada tabla de markdown con el último encabezado que la precede. */
export function leerTablas(md: string): Tabla[] {
  const tablas: Tabla[] = []
  let titulo = ''
  let actual: Tabla | null = null
  for (const linea of md.split(/\r?\n/)) {
    const h = /^#{1,6}\s+(.*)$/.exec(linea)
    if (h) { titulo = h[1].trim(); actual = null; continue }
    if (!linea.startsWith('|')) { actual = null; continue }
    if (/^\|[-| :]+\|$/.test(linea)) continue
    const celdas = linea.replace(/^\||\|\s*$/g, '').split('|').map((c) => c.trim())
    if (actual) actual.filas.push(celdas)
    else { actual = { titulo, columnas: celdas, filas: [] }; tablas.push(actual) }
  }
  return tablas
}

/** Archivos distintos por herramienta, en el orden en que aparecen en SI_USO.md. */
export function resumenSI(md: string): { herramienta: string; archivos: number }[] {
  const porHerramienta = new Map<string, Set<string>>()
  for (const tabla of leerTablas(md)) {
    const [h, a] = ['Herramienta', 'Archivo'].map((c) => tabla.columnas.indexOf(c))
    if (h < 0 || a < 0) continue // otras tablas se ignoran
    for (const f of tabla.filas) porHerramienta.set(f[h], (porHerramienta.get(f[h]) ?? new Set()).add(f[a]))
  }
  return [...porHerramienta].map(([herramienta, archivos]) => ({ herramienta, archivos: archivos.size }))
}

// Créditos: solo filas en uso; el filtro corre también al compilar si vite.config registra registrosPlugin
export const LICENCIAS = leerTablas(soloEnUso(licenciasMd))
export const CITAS = leerTablas(soloEnUso(citasMd))
export const USO_SI = resumenSI(usoSiMd)
