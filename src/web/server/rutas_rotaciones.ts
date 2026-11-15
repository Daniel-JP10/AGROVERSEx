// asistido por SI: Claude Code (Anthropic), escritura y revisión de código; base del prototipo migrada en el hackatón
import type { DatabaseSync } from 'node:sqlite'
import { ErrorEntrada, validarId } from './validar'
import type { Resp } from './rutas_serie'

const norm = (s: unknown) => String(s ?? '').normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase()

// Sin región documentada: vacio, no 404. Región = ?region= (lista blanca) o el nombre de la unidad o de un ancestro.
// El servidor no pondera ni combina nada: Efecto2 y betas viajan por separado (el orden vive en el cliente).
export function rotaciones(db: DatabaseSync, id: string, q: URLSearchParams): Resp {
  validarId(db, id)
  const sistemas = db.prepare('SELECT * FROM sistema_rotacion ORDER BY id').all() as Record<string, unknown>[]
  const regiones = sistemas.map((s) => s.region as string)
  const pedida = q.get('region')
  if (pedida !== null && !regiones.includes(pedida)) throw new ErrorEntrada('región fuera de la lista')
  const nombres: string[] = []
  for (let cur: string | null = id; cur; ) {
    const u = db.prepare('SELECT nombre, nombre_es, nombre_en, padre_id FROM unidad WHERE id = ?').get(cur) as Record<string, string | null> | undefined
    if (!u) break
    nombres.push(norm(u.nombre), norm(u.nombre_es), norm(u.nombre_en))
    cur = u.padre_id
  }
  const casa = (txt: unknown) => { const t = norm(txt); return t.length > 2 && nombres.some((n) => n.length > 2 && (t.includes(n) || n.includes(t))) }
  const sis = sistemas.filter((s) => (pedida !== null ? s.region === pedida : casa(s.region)))
  const ante = (db.prepare('SELECT * FROM efecto_antecesor').all() as Record<string, unknown>[]).filter((a) => casa(a.pais))
  if (!sis.length && !ante.length) {
    return { cuerpo: { vacio: true, motivo: 'sin sistema de rotación documentado', regiones_disponibles: regiones } }
  }
  return {
    cuerpo: {
      vacio: false,
      sistemas: sis, // etiqueta FUENTE, INFERENCIA o PENDIENTE tal cual; las PENDIENTE no se ocultan
      antecesor: ante, // efecto2, eff_div, beta_lluvia, beta_t por separado; toda combinación es propia, no del artículo
      cultivos: db.prepare('SELECT * FROM cultivo ORDER BY id').all(),
      sucesion: db.prepare('SELECT * FROM regla_sucesion ORDER BY cultivo_o_familia, enfermedad').all(),
    },
  }
}

// Zona DEMO (tabla zona_demo) -> región de sistema_rotacion y país de efecto_antecesor, por prefijo normalizado.
const ZONA_REGION: Record<string, [string, string?]> = {
  corn_belt: ['corn belt', 'ee. uu.'], pampa: ['pampa'], cerrado: ['cerrado'], llanos: ['llanos'], andina_colombia: ['andina colombia'],
  indo_gangetica: ['indo-gangetica'], sahel: ['sahel'], africa_oriental: ['africa oriental'], francia: ['europa (francia)', 'francia'],
  australia: ['australia'],
}

/** /api/rotaciones?unidad=<id>: la zona sale de zona_demo; sin zona, vacío con motivo. */
export function rotacionesDeUnidad(db: DatabaseSync, id: string): Resp {
  validarId(db, id)
  const hay = db.prepare("SELECT 1 FROM sqlite_master WHERE name = 'zona_demo'").get()
  const zona = hay ? (db.prepare('SELECT MIN(zona) z FROM zona_demo WHERE unidad_id = ?').get(id) as { z: string | null }).z : null
  const regiones = (db.prepare('SELECT region FROM sistema_rotacion ORDER BY id').all() as { region: string }[]).map((r) => r.region)
  const vacio = (motivo: string) => ({ cuerpo: { vacio: true, motivo, regiones_disponibles: regiones } })
  if (!zona) return vacio('la unidad no está en una zona DEMO')
  const [reg, pais] = ZONA_REGION[zona] ?? []
  const region = regiones.find((r) => reg && norm(r).startsWith(reg))
  if (!region) return vacio(`sin sistema de rotación documentado para la zona ${zona}`)
  const r = rotaciones(db, id, new URLSearchParams({ region }))
  const c = r.cuerpo as { sistemas?: unknown[]; antecesor?: unknown[] }
  // El antecesor se une por país de la zona, no por coincidencia de nombres de la unidad.
  const ante = (db.prepare('SELECT * FROM efecto_antecesor').all() as Record<string, unknown>[]).filter((a) => !!pais && norm(a.pais).startsWith(pais))
  return { cuerpo: { ...c, vacio: false, zona, antecesor: ante } }
}
