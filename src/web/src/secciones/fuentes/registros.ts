// asistido por SI: Claude Code (Anthropic), filtro de los registros que publica Fuentes: solo filas "en uso", sin prosa
// Lo usan tablas.ts en el navegador y registrosPlugin.ts al compilar, para que lo excluido no llegue al JS publicado

const celdas = (linea: string) => linea.replace(/^\||\|\s*$/g, '').split('|').map((c) => c.trim())
const separador = (linea: string) => /^\|[-| :]+\|$/.test(linea)

/** Deja encabezados y, de cada tabla, la cabecera y solo las filas cuya columna Estado empieza por "en uso". */
export function soloEnUso(md: string): string {
  const out: string[] = []
  let estado = -1
  let enTabla = false
  for (const linea of md.split(/\r?\n/)) {
    if (/^#{1,6}\s/.test(linea)) { out.push(linea, ''); enTabla = false; continue }
    if (!linea.startsWith('|')) { enTabla = false; continue }
    if (separador(linea)) { out.push(linea); continue }
    if (!enTabla) { enTabla = true; estado = celdas(linea).indexOf('Estado'); out.push(linea); continue }
    if (estado >= 0 && /^en uso\b/i.test(celdas(linea)[estado] ?? '')) out.push(linea)
  }
  return out.join('\n')
}

/** De SI_USO.md solo hace falta contar archivos por herramienta: deja esas dos columnas. */
export function soloHerramientaArchivo(md: string): string {
  const out: string[] = []
  let cols: number[] = []
  for (const linea of md.split(/\r?\n/)) {
    if (/^#{1,6}\s/.test(linea)) { out.push(linea); cols = []; continue }
    if (!linea.startsWith('|') || separador(linea)) { if (separador(linea) && cols.length) out.push('|-|-|'); continue }
    const c = celdas(linea)
    if (!cols.length) cols = ['Herramienta', 'Archivo'].map((n) => c.indexOf(n))
    if (cols.some((i) => i < 0)) continue
    out.push(`| ${cols.map((i) => c[i]).join(' | ')} |`)
  }
  return out.join('\n')
}
