// asistido por SI: Claude Code (Anthropic), traducción de las claves de texto del gemelo v1.1 (§3) con su catálogo en.json o es.json
import { aIngles } from './correccionEn'
export type Catalogo = Record<string, string>

// Formato de Python que usa el catálogo: {x}, {x:g}, {x:.3g}, {x:+.3g}; '%g' pasa a exponente si exp < -4 o exp >= precisión
export function formatoG(v: number, spec: string): string {
  const m = /^(\+)?(?:\.(\d+))?g$/.exec(spec)
  if (!m) return String(v)
  const p = Math.max(1, m[2] ? Number(m[2]) : 6)
  const exp = v === 0 ? 0 : Math.floor(Math.log10(Math.abs(Number(v.toPrecision(p)))))
  let s: string
  if (exp < -4 || exp >= p) {
    const [man, e] = v.toExponential(p - 1).split('e')
    const n = Number(e)
    s = `${man.includes('.') ? man.replace(/\.?0+$/, '') : man}e${n < 0 ? '-' : '+'}${String(Math.abs(n)).padStart(2, '0')}`
  } else s = String(Number(v.toPrecision(p)))
  return m[1] && v >= 0 ? `+${s}` : s
}

// Además de g: {x:.2f}, {x:+.2f} y {x:.0%} (porcentaje con N decimales)
export function formatoNum(v: number, spec: string): string {
  const m = /^(\+)?\.(\d+)([f%])$/.exec(spec)
  if (!m) return formatoG(v, spec)
  const s = (m[3] === '%' ? v * 100 : v).toFixed(Number(m[2])) + (m[3] === '%' ? '%' : '')
  return m[1] && v >= 0 ? `+${s}` : s
}

const esClave = (x: unknown): x is { clave: string } => typeof x === 'object' && x !== null && typeof (x as { clave?: unknown }).clave === 'string'

// Una clave sin texto en el catálogo se muestra tal cual: nunca se inventa un texto
export function traducir(cat: Catalogo, clave: string, parametros: Record<string, unknown> = {}): string {
  const plantilla = cat[clave]
  if (plantilla === undefined) return clave
  return plantilla.replace(/\{(\w+)(?::([^}]*))?\}/g, (todo, nombre: string, spec?: string) => {
    if (!(nombre in parametros)) return todo
    const v = parametros[nombre]
    if (esClave(v)) return traducir(cat, v.clave)
    if (Array.isArray(v)) {
      // Lista de claves source.*: se une con joiner.and
      const xs = v.map((x) => (typeof x === 'string' && x in cat ? cat[x] : String(x)))
      const y = cat['joiner.and'] ?? 'and'
      return xs.length <= 2 ? xs.join(` ${y} `) : `${xs.slice(0, -1).join(', ')} ${y} ${xs[xs.length - 1]}`
    }
    if (typeof v === 'number' && spec) return formatoNum(v, spec)
    if (v === null || v === undefined) return todo
    return cat.__en && typeof v === 'string' ? aIngles(v) : String(v)
  })
}
