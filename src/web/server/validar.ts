// asistido por SI: Claude Code (Anthropic), escritura y revisión de código; base del prototipo migrada en el hackatón
import type { DatabaseSync } from 'node:sqlite'

export class ErrorEntrada extends Error {
  constructor(msg: string, public status = 400) { super(msg) }
}

export function validarMes(m: unknown): number {
  const n = typeof m === 'string' && /^\d{1,3}$/.test(m) ? Number(m) : typeof m === 'number' ? m : NaN
  if (!Number.isInteger(n) || n < 0 || n > 322) throw new ErrorEntrada('mes fuera de 0..322')
  return n
}

export function validarNivel(n: unknown): 0 | 1 | 2 {
  if (n === '0' || n === '1' || n === '2') return Number(n) as 0 | 1 | 2
  throw new ErrorEntrada('nivel debe ser 0, 1 o 2')
}

const listas = new WeakMap<DatabaseSync, Set<string>>()
// Lista blanca: ids de `variable` que además son columna de `mensual` (el único lugar donde se interpola).
function variablesMensuales(db: DatabaseSync): Set<string> {
  let s = listas.get(db)
  if (!s) {
    const cols = new Set(db.prepare('PRAGMA table_info(mensual)').all().map((c) => c.name as string))
    s = new Set(db.prepare('SELECT id FROM variable').all().map((r) => r.id as string).filter((id) => cols.has(id)))
    listas.set(db, s)
  }
  return s
}

export function validarVariable(db: DatabaseSync, v: string): string {
  if (!variablesMensuales(db).has(v)) throw new ErrorEntrada('variable fuera de la lista')
  return v
}

export function validarId(db: DatabaseSync, id: string): string {
  if (id.length > 64 || !db.prepare('SELECT 1 FROM unidad WHERE id = ?').get(id)) throw new ErrorEntrada('unidad inexistente', 404)
  return id
}
