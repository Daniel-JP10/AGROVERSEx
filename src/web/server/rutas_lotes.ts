// asistido por SI: Claude Code (Anthropic), escritura y revisión de código; base del prototipo migrada en el hackatón
import type { DatabaseSync } from 'node:sqlite'
import { ErrorEntrada, validarId } from './validar'
import type { Resp } from './rutas_serie'

// Lotes sintéticos (sin persona asociada) de la unidad o de sus descendientes hasta 2 niveles.
export function lotes(db: DatabaseSync, id: string): Resp {
  validarId(db, id)
  const filas = db.prepare(`SELECT l.* FROM lote l JOIN unidad u ON u.id = l.unidad_id
    LEFT JOIN unidad p ON p.id = u.padre_id WHERE u.id = ?1 OR u.padre_id = ?1 OR p.padre_id = ?1 ORDER BY l.id`).all(id)
  if (!filas.length) return { cuerpo: { vacio: true, motivo: 'sin lotes de demostración en esta región' } }
  return { cuerpo: { vacio: false, sintetico: true, lotes: filas } }
}

export function lote(db: DatabaseSync, id: string): Resp {
  const l = id.length <= 64 ? db.prepare('SELECT * FROM lote WHERE id = ?').get(id) : undefined
  if (!l) throw new ErrorEntrada('lote inexistente', 404)
  const esc = (c: string) => db.prepare('SELECT escala, desplazamiento FROM variable WHERE id = ?').get(c) as { escala: number | null; desplazamiento: number | null } | undefined
  // sm_sensor comparte unidades con sm_verdad.
  const m = { ndvi: esc('ndvi'), nbr2: esc('nbr2'), sm_verdad: esc('sm_verdad'), sm_sensor: esc('sm_verdad') }
  const f = (c: keyof typeof m, v: number | null) => (v === null ? null : v * Number(m[c]?.escala ?? 1) + Number(m[c]?.desplazamiento ?? 0))
  const diario = db.prepare('SELECT * FROM lote_diario WHERE lote_id = ? ORDER BY dia_id').all(id).map((r) => ({
    dia_id: r.dia_id, nube: r.nube,
    ndvi: f('ndvi', r.ndvi as number | null), nbr2: f('nbr2', r.nbr2 as number | null),
    sm_verdad: f('sm_verdad', r.sm_verdad as number | null), sm_sensor: f('sm_sensor', r.sm_sensor as number | null),
  }))
  // Huecos = null, sin interpolar.
  return { cuerpo: { lote: l, sintetico: true, diario, ventanas: db.prepare('SELECT * FROM lote_ventana WHERE lote_id = ? ORDER BY temporada').all(id) } }
}
