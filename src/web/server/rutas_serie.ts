// asistido por SI: Claude Code (Anthropic), escritura y revisión de código; base del prototipo migrada en el hackatón
import type { DatabaseSync } from 'node:sqlite'
import { ErrorEntrada, validarId, validarMes, validarVariable } from './validar'

type Fila = Record<string, number | string | null>
export type Resp = { cuerpo: unknown }

const MAX_VARS = 12

// Valor físico = entero * escala + desplazamiento; null si hueco, relleno o fuera del rango válido.
function desescalar(v: Fila, e: number | null): number | null {
  if (e === null || e === undefined) return null
  if (v.relleno !== null && e === v.relleno) return null
  const x = e * Number(v.escala ?? 1) + Number(v.desplazamiento ?? 0)
  return x < Number(v.valido_min) || x > Number(v.valido_max) ? null : x
}

// Lluvia: mm/h en la base (contrato INICIAR 5.2); la conversión para mostrar es de la UI.
export function serie(db: DatabaseSync, id: string, q: URLSearchParams): Resp {
  validarId(db, id)
  const lista = (q.get('vars') ?? '').split(',').filter(Boolean)
  if (!lista.length) throw new ErrorEntrada('falta vars')
  if (lista.length > MAX_VARS) throw new ErrorEntrada(`máximo ${MAX_VARS} variables`)
  const desde = q.has('desde') ? validarMes(q.get('desde')) : 0
  const hasta = q.has('hasta') ? validarMes(q.get('hasta')) : 322
  if (desde > hasta) throw new ErrorEntrada('desde > hasta')
  const cols = new Set(db.prepare('PRAGMA table_info(mensual)').all().map((c) => c.name as string))
  const vars = [...new Set(lista.map((v) => validarVariable(db, v)))]
  const meses = Array.from({ length: hasta - desde + 1 }, (_, i) => desde + i)
  const series: Record<string, unknown> = {}
  for (const v of vars) {
    const par = ['p10', 'p90'].filter((s) => cols.has(`${v}_${s}`))
    // Los nombres de columna ya pasaron la lista blanca; los valores van como parámetros.
    const sel = [v, ...par.map((s) => `${v}_${s}`)].map((c) => `m.${c}`).join(', ')
    const filas = db.prepare(`SELECT m.mes_id AS mes, ${sel}, m.bandera_motivo AS b FROM mensual m
      WHERE m.unidad_id = ? AND m.mes_id BETWEEN ? AND ? ORDER BY m.mes_id`).all(id, desde, hasta) as Fila[]
    const por = new Map(filas.map((f) => [f.mes as number, f]))
    const meta = db.prepare('SELECT * FROM variable WHERE id = ?').get(v) as Fila
    const col = (c: string) => meses.map((m) => desescalar(meta, (por.get(m)?.[c] as number | null) ?? null))
    const s: Record<string, unknown> = {
      valor: col(v),
      // -1 = no hay fila para ese mes (distinto de 0 = sin motivo de hueco); nunca se interpola.
      bandera: meses.map((m) => (por.has(m) ? ((por.get(m)!.b as number | null) ?? 0) : -1)),
      unidad_medida: meta.unidad_medida, rango: [meta.valido_min, meta.valido_max], etiqueta: meta.etiqueta, nivel_dato: meta.nivel_dato,
    }
    for (const p of par) s[p] = col(`${v}_${p}`)
    series[v] = s
  }
  return { cuerpo: { meses, series } }
}

export function anual(db: DatabaseSync, id: string): Resp {
  validarId(db, id)
  return { cuerpo: { filas: db.prepare('SELECT * FROM anual WHERE unidad_id = ? ORDER BY anio').all(id) } }
}

// Dato real NOAA CPC.
export function enso(db: DatabaseSync): Resp {
  return { cuerpo: db.prepare('SELECT mes_id, oni, roni FROM enso ORDER BY mes_id').all() }
}

export function eventos(db: DatabaseSync, id: string): Resp {
  validarId(db, id)
  return { cuerpo: db.prepare(`SELECT ev.*, eu.intensidad FROM evento_unidad eu JOIN evento ev ON ev.id = eu.evento_id
    WHERE eu.unidad_id = ? ORDER BY ev.inicio, ev.id`).all(id) }
}

// Eventos globales para los marcadores de la línea de tiempo (sin unidad).
export function eventosGlobales(db: DatabaseSync): Resp {
  return { cuerpo: db.prepare('SELECT id, tipo, inicio, fin, region_texto, magnitud_texto, etiqueta FROM evento ORDER BY inicio, id').all() }
}
