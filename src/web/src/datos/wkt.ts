// asistido por SI: Claude Code (Anthropic), escritura y revisión de código; base del prototipo migrada en el hackatón
export interface Poligono { type: "Polygon"; coordinates: number[][][] }
// POLYGON de anillo simple; todo lo demás lanza error controlado.
export function parsearWkt(wkt: string): Poligono {
  const m = /^\s*POLYGON\s*\(\(([^()]+)\)\)\s*$/i.exec(wkt ?? '')
  if (!m) throw new Error('WKT inválido: solo POLYGON de anillo simple')
  const anillo = m[1].split(',').map((p) => p.trim().split(/\s+/).map(Number))
  if (anillo.length < 4 || anillo.some((c) => c.length !== 2 || c.some((x) => !Number.isFinite(x)))) throw new Error('WKT inválido: coordenadas')
  const [a, b] = [anillo[0], anillo[anillo.length - 1]]
  if (a[0] !== b[0] || a[1] !== b[1]) throw new Error('WKT inválido: anillo abierto')
  return { type: 'Polygon', coordinates: [anillo] }
}
