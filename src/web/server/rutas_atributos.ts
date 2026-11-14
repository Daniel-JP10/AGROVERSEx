// asistido por SI: Claude Code (Anthropic), escritura y revisión de código; base del prototipo migrada en el hackatón
import type { DatabaseSync } from 'node:sqlite'
import { validarNivel } from './validar'
import type { Resp } from './rutas_serie'

// Atributos por unidad para filtrar: salen de las tablas, no de listas escritas a mano.
// El último año de `anual` da cobertura y condición; `zona_demo(unidad_id, zona)` es opcional (llega con la fase 2).
export function atributos(db: DatabaseSync, q: URLSearchParams): Resp {
  const nivel = validarNivel(q.get('nivel'))
  const tabla = (t: string) => !!db.prepare("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?").get(t)
  const zonas = tabla('zona_demo')
    ? new Map((db.prepare('SELECT unidad_id, MIN(zona) zona FROM zona_demo GROUP BY unidad_id').all() as { unidad_id: string; zona: string }[]).map((r) => [r.unidad_id, r.zona]))
    : new Map<string, string>()
  const est = new Map<string, Record<string, number | null>>()
  for (const r of db.prepare(`SELECT e.unidad_id, e.variable_id, e.media FROM estatico e JOIN unidad u ON u.id = e.unidad_id
      WHERE u.nivel = ? AND e.variable_id IN ('elev_min','elev_max','phh2o_0_30')`).all(nivel) as { unidad_id: string; variable_id: string; media: number | null }[]) {
    const o = est.get(r.unidad_id) ?? {}
    o[r.variable_id] = r.media
    est.set(r.unidad_id, o)
  }
  const kop = new Map((db.prepare(`SELECT c.unidad_id, c.clase FROM clase_fraccion c JOIN unidad u ON u.id = c.unidad_id
      WHERE u.nivel = ? AND c.esquema = 'koppen' ORDER BY c.fraccion ASC`).all(nivel) as { unidad_id: string; clase: string }[]).map((r) => [r.unidad_id, r.clase]))
  const anu = new Map((db.prepare(`SELECT a.unidad_id, a.cobertura_igbp, a.clase_condicion FROM anual a JOIN unidad u ON u.id = a.unidad_id
      WHERE u.nivel = ? ORDER BY a.anio ASC`).all(nivel) as { unidad_id: string; cobertura_igbp: number | null; clase_condicion: string | null }[]).map((r) => [r.unidad_id, r]))
  const conEv = new Set((db.prepare('SELECT DISTINCT eu.unidad_id FROM evento_unidad eu JOIN unidad u ON u.id = eu.unidad_id WHERE u.nivel = ?').all(nivel) as { unidad_id: string }[]).map((r) => r.unidad_id))
  const n = <T,>(x: T | null | undefined) => (x === null || x === undefined ? undefined : x)
  const filas = (db.prepare('SELECT id, punto_lat FROM unidad WHERE nivel = ? ORDER BY id').all(nivel) as { id: string; punto_lat: number | null }[]).map((u) => {
    const e = est.get(u.id), a = anu.get(u.id)
    return { id: u.id, lat: n(u.punto_lat), elevMin: n(e?.elev_min), elevMax: n(e?.elev_max), ph: n(e?.phh2o_0_30),
      koppen: kop.get(u.id), igbp: n(a?.cobertura_igbp), condicion: n(a?.clase_condicion), zona: zonas.get(u.id), eventos: conEv.has(u.id) }
  })
  return { cuerpo: { nivel, zona_demo: zonas.size > 0, unidades: filas } }
}
