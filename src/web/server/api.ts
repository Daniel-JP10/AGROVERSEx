// asistido por SI: Claude Code (Anthropic), escritura y revisión de código; base del prototipo migrada en el hackatón
/// <reference path="./node-sqlite.d.ts" />
import type { DatabaseSync } from 'node:sqlite'
import { existsSync } from 'node:fs'
import type { Plugin } from 'vite'
import { abrirDb } from './sqlite'
import { anual, enso, eventos, eventosGlobales, serie } from './rutas_serie'
import { rotaciones, rotacionesDeUnidad } from './rutas_rotaciones'
import { atributos } from './rutas_atributos'
import { lote, lotes } from './rutas_lotes'
import { ErrorEntrada, validarId, validarMes, validarNivel, validarVariable } from './validar'

export const SIN_DATO = -32768
const ROTULO_ESTATICO = 'media del producto agregado, sin intervalo'

export interface Respuesta { status: number; cabeceras: Record<string, string>; cuerpo: string | Buffer }
const json = (o: unknown, status = 200): Respuesta => ({ status, cabeceras: { 'Content-Type': 'application/json; charset=utf-8' }, cuerpo: JSON.stringify(o) })

const ordenes = new WeakMap<DatabaseSync, Map<number, string[]>>()
function orden(db: DatabaseSync, nivel: number): string[] {
  let m = ordenes.get(db)
  if (!m) ordenes.set(db, (m = new Map()))
  let ids = m.get(nivel)
  if (!ids) m.set(nivel, (ids = db.prepare('SELECT id FROM unidad WHERE nivel = ? ORDER BY id').all(nivel).map((r) => r.id as string)))
  return ids
}

// Sentencias preparadas por (base, variable); `col` ya pasó la lista blanca.
const preparadas = new WeakMap<DatabaseSync, Map<string, ReturnType<DatabaseSync['prepare']>>>()
function sentencia(db: DatabaseSync, col: string) {
  let m = preparadas.get(db)
  if (!m) preparadas.set(db, (m = new Map()))
  let s = m.get(col)
  if (!s) {
    const frac = db.prepare('PRAGMA table_info(mensual)').all().some((c) => c.name === `${col}_frac`) ? `m.${col}_frac` : 'NULL'
    s = db.prepare(`SELECT u.id AS id, m.${col} AS v, ${frac} AS f, m.bandera_motivo AS b FROM unidad u
      LEFT JOIN mensual m ON m.unidad_id = u.id AND m.mes_id = ? WHERE u.nivel = ? ORDER BY u.id`)
    m.set(col, s)
  }
  return s
}

type Fila = { id: string; v: number | null; f: number | null; b: number | null }
const filas = (db: DatabaseSync, col: string, nivel: number, mes: number) => sentencia(db, col).all(mes, nivel) as unknown as Fila[]

function variable(db: DatabaseSync, id: string) {
  return db.prepare('SELECT * FROM variable WHERE id = ?').get(id) as Record<string, number | string | null> | undefined
}

function mesesDe(q: URLSearchParams, a: string, b: string): [number, number] {
  const d = validarMes(q.get(a)), h = validarMes(q.get(b))
  if (h < d || h - d + 1 > 24) throw new ErrorEntrada('rango inválido: máximo 24 meses y desde <= hasta')
  return [d, h]
}

function binario(db: DatabaseSync, nivel: number, col: string, desde: number, hasta: number): Respuesta {
  const n = orden(db, nivel).length, nm = hasta - desde + 1
  const buf = Buffer.alloc(2 * n * nm)
  for (let k = 0; k < nm; k++) {
    filas(db, col, nivel, desde + k).forEach((r, i) => {
      const v = r.v === null || r.v <= SIN_DATO || r.v > 32767 ? SIN_DATO : r.v
      buf.writeInt16LE(v, 2 * (k * n + i))
    })
  }
  const v = variable(db, col)!
  return {
    status: 200,
    cuerpo: buf,
    cabeceras: {
      'Content-Type': 'application/octet-stream',
      'X-Escala': String(v.escala), 'X-Desplazamiento': String(v.desplazamiento ?? 0),
      'X-Rango': `${v.valido_min},${v.valido_max}`, // rango válido en unidades físicas
      'X-Sin-Dato': String(SIN_DATO), 'X-Meses': String(nm),
    },
  }
}

export function manejar(db: DatabaseSync, url: URL): Respuesta {
  try {
    const p = url.pathname, q = url.searchParams
    if (p === '/api/meta') {
      const niv = db.prepare('SELECT nivel, COUNT(*) n FROM unidad GROUP BY nivel').all()
      return json({
        variables: db.prepare('SELECT * FROM variable').all(),
        fuentes: db.prepare('SELECT * FROM fuente').all(),
        metadatos: db.prepare('SELECT * FROM metadatos').all(),
        meses: { min: 0, max: 322 },
        unidades_por_nivel: Object.fromEntries(niv.map((r) => [String(r.nivel), r.n])),
        rotulo_estatico: ROTULO_ESTATICO,
      })
    }
    if (p === '/api/orden') return json({ ids: orden(db, validarNivel(q.get('nivel'))) })
    if (p === '/api/coropleta' || p === '/api/coropleta.json') {
      const nivel = validarNivel(q.get('nivel')), col = validarVariable(db, q.get('var') ?? ''), mes = validarMes(q.get('mes'))
      if (p === '/api/coropleta') return binario(db, nivel, col, mes, mes)
      const v = variable(db, col)!, esc = Number(v.escala), des = Number(v.desplazamiento ?? 0)
      const fesc = Number(variable(db, `${col}_frac`)?.escala ?? 0.001)
      return json(Object.fromEntries(filas(db, col, nivel, mes).map((r) => [
        r.id, [r.v === null ? null : r.v * esc + des, r.f === null ? null : r.f * fesc, r.b]])))
    }
    if (p === '/api/coropleta_rango') {
      const nivel = validarNivel(q.get('nivel')), col = validarVariable(db, q.get('var') ?? '')
      const [d, h] = mesesDe(q, 'desde', 'hasta')
      return binario(db, nivel, col, d, h)
    }
    const m = /^\/api\/unidad\/([^/]+)$/.exec(p)
    if (m) {
      const id = validarId(db, decodeURIComponent(m[1]))
      const u = db.prepare('SELECT * FROM unidad WHERE id = ?').get(id) as Record<string, unknown>
      const estatico = db.prepare(`SELECT e.*, v.valido_min, v.valido_max, v.unidad_medida, v.etiqueta FROM estatico e
        LEFT JOIN variable v ON v.id = e.variable_id WHERE e.unidad_id = ?`).all(id).map((r) => ({ ...r, rotulo: ROTULO_ESTATICO }))
      return json({
        unidad: u,
        padre: u.padre_id ? db.prepare('SELECT id, nombre, nivel FROM unidad WHERE id = ?').get(u.padre_id) ?? null : null,
        estatico,
        clases: db.prepare('SELECT esquema, clase, fraccion FROM clase_fraccion WHERE unidad_id = ?').all(id),
        eventos: db.prepare(`SELECT ev.id, ev.tipo, ev.inicio, ev.fin, ev.etiqueta, eu.intensidad FROM evento_unidad eu
          JOIN evento ev ON ev.id = eu.evento_id WHERE eu.unidad_id = ?`).all(id),
      })
    }
    if (p === '/api/atributos') return json(atributos(db, q).cuerpo)
    if (p === '/api/eventos') return json(eventosGlobales(db).cuerpo)
    if (p === '/api/rotaciones') return json(rotacionesDeUnidad(db, q.get('unidad') ?? '').cuerpo)
    if (p === '/api/enso') return json(enso(db).cuerpo)
    const r = /^\/api\/(serie|anual|eventos|rotaciones|lotes|lote)\/([^/]+)$/.exec(p)
    if (r) {
      const id = decodeURIComponent(r[2])
      const f = { serie: () => serie(db, id, q), anual: () => anual(db, id), eventos: () => eventos(db, id),
        rotaciones: () => rotaciones(db, id, q), lotes: () => lotes(db, id), lote: () => lote(db, id) }[r[1] as 'serie']
      return json(f().cuerpo)
    }
    return json({ error: 'ruta desconocida' }, 404)
  } catch (e) {
    if (e instanceof ErrorEntrada) return json({ error: e.message }, e.status)
    console.error('[api]', e)
    return json({ error: 'error interno' }, 500)
  }
}

// La ruta de la base viene solo de la configuración, nunca de un parámetro de la petición.
export function apiLocal(opts: { rutaDb: string }): Plugin {
  return {
    name: 'api-local',
    configureServer(server) {
      const existe = existsSync(opts.rutaDb)
      if (!existe) console.warn(`[api] No existe la base ${opts.rutaDb}. Define AGROVERSEX_SQLITE con su ruta.`)
      const db = existe ? abrirDb(opts.rutaDb) : null
      server.middlewares.use((req, res, next) => {
        if (!req.url?.startsWith('/api/')) return next()
        const r = db ? manejar(db, new URL(req.url, 'http://localhost')) : json({ error: `base no encontrada (${opts.rutaDb}); define AGROVERSEX_SQLITE` }, 503)
        res.writeHead(r.status, r.cabeceras)
        res.end(r.cuerpo)
      })
    },
  }
}
