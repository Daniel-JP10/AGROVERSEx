// asistido por SI: Claude Code (Anthropic), escritura y revisión de código; base del prototipo migrada en el hackatón
import type { Clave, Estrategia } from './ordenar'

// Forma de GET /api/rotaciones/:id?region= (filas tal cual de las tablas)
export interface RespRotaciones {
  vacio: boolean
  motivo?: string
  regiones_disponibles?: string[]
  sistemas?: { id: string; region: string; habitual: string; alternativa_1: string; alternativa_2: string; fuente_id: string; etiqueta: string }[]
  antecesor?: Antecesor[]
  cultivos?: { id: string; nombre: string; familia: string; fija_n: number; ndfa_media: number | null; etiqueta: string }[]
  sucesion?: { cultivo_o_familia: string; enfermedad: string; intervalo_min: number; intervalo_max: number; clima: string; fuente_id: string }[]
}
export interface Antecesor { pais: string; antecesor: string; cultivo: string; efecto2: number; eff_div: number | null; beta_lluvia: number | null; beta_t: number | null; significativo: number | null; fuente_id: string }

export interface Adaptado {
  vacio: boolean; motivo: string; region: string; etiqueta: string; chino: boolean
  estrategias: Estrategia[]; pendientes: string[]; antecesor: Antecesor[]; fuentes: string[]
}

const norm = (s: string) => s.normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase()
// Abreviaturas de efecto_antecesor con significado confirmado (INV-ROT §3.3: C maíz, S soya, SW trigo primavera, WW trigo invierno).
// Las demás (UW, WB, R, P, ...) siguen PENDIENTES: no se unen. Un nombre completo se acepta tal cual.
const CODIGOS: Record<string, string> = { C: 'maíz', S: 'soya', SW: 'trigo primavera', WW: 'trigo invierno' }
const nombreCultivo = (x: string) => { const c = CODIGOS[x]; return c ? norm(c) : x.length > 3 ? norm(x) : undefined }
const pendiente = (t: string) => !t || /pendiente/i.test(t)
// D-009: las filas de China dependen de un mapa de un grupo chino
const esChina = (r: string) => /china/i.test(r)

export function adaptar(r: RespRotaciones): Adaptado {
  const base: Adaptado = { vacio: true, motivo: r.motivo ?? 'sin sistema de rotación documentado', region: '', etiqueta: 'PENDIENTE', chino: false, estrategias: [], pendientes: [], antecesor: [], fuentes: [] }
  const s = r.sistemas?.[0]
  if (r.vacio || !s) return base
  const cult = r.cultivos ?? []
  const ante = r.antecesor ?? []
  const pendientes: string[] = []
  const estrategias: Estrategia[] = []
  const filas: [string, string][] = [['habitual', s.habitual], ['alternativa 1', s.alternativa_1], ['alternativa 2', s.alternativa_2]]
  filas.forEach(([rol, txt], i) => {
    if (pendiente(txt)) { pendientes.push(rol); return }
    const t = norm(txt)
    const cs = cult.filter((c) => t.includes(norm(c.nombre)))
    const ndfa = cs.map((c) => c.ndfa_media).filter((x): x is number => x != null)
    const a = i === 0 ? undefined : ante.find((x) => {
      const an = nombreCultivo(x.antecesor), cn = nombreCultivo(x.cultivo)
      return an !== undefined && t.includes(an) && (cn === undefined || t.includes(cn))
    })
    const nulos = { agua: null, forraje: null, mercado: null, erosion: null, materiaOrganica: null } as Record<Clave, null>
    estrategias.push({
      id: `${s.id}-${i}`, nombre: txt, cultivos: cs.map((c) => c.id), aguaMm: null, efecto2: a?.efecto2 ?? null,
      exige: { siembraDirecta: false, cosechaForraje: false }, // SUPUESTO: sin tabla de equipos aún
      beneficios: { ...nulos, nitrogeno: ndfa.length ? { v: Math.max(...ndfa) } : null },
    })
  })
  return { vacio: false, motivo: '', region: s.region, etiqueta: s.etiqueta, chino: esChina(s.region), estrategias, pendientes, antecesor: ante, fuentes: [s.fuente_id] }
}

// La región sale de la zona DEMO de la unidad (tabla zona_demo) en el servidor.
export async function pedirRotaciones(unidad: string, f: typeof fetch = fetch): Promise<RespRotaciones & { zona?: string }> {
  const r = await f(`/api/rotaciones?unidad=${encodeURIComponent(unidad)}`)
  if (!r.ok) throw new Error(`HTTP ${r.status}`)
  return r.json()
}
