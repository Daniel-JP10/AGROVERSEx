// asistido por SI: Claude Code (Anthropic), escritura y revisión de código; base del prototipo migrada en el hackatón
// Búsqueda sobre el índice real (indice_busqueda.json.gz): MiniSearch sin tildes, prefijo y difuso.
import MiniSearch from 'minisearch'
import { INDICE_BUSQUEDA } from '../globo/config'

export interface FilaIndice { id: string; nivel: number; n: string; a: string; es?: string; en?: string; ctx: string; d?: number }
export interface UnidadMiga { padre_id: string | null; iso3: string; nombre: string; nivel: number }
export interface Paso { id: string; nombre: string; nivel: number }

const quitarTildes = (t: string) => t.normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase()

export function cargarIndice(): Promise<FilaIndice[]> {
  return fetch(INDICE_BUSQUEDA).then((r) => new Response(r.body!.pipeThrough(new DecompressionStream('gzip'))).json())
}

export function crearBuscador(filas: FilaIndice[]) {
  const ms = new MiniSearch<FilaIndice>({
    fields: ['n', 'a', 'es', 'en'],
    storeFields: ['id', 'nivel', 'n', 'a', 'es', 'en', 'ctx', 'd'],
    processTerm: quitarTildes,
    searchOptions: {
      prefix: true, fuzzy: 0.2, combineWith: 'AND',
      // El menor nivel pesa más: país > departamento > municipio
      boostDocument: (_id, _t, d) => 1 + 0.5 * (2 - Math.min(Number(d?.nivel ?? 2), 2)),
    },
  })
  ms.addAll(filas)
  return { buscar: (texto: string, max = 8) => ms.search(texto).slice(0, max) as unknown as FilaIndice[] }
}

/** Camino País › Departamento › Unidad. Sin padre_id (260 ADM2) sube al país por iso3 y omite el departamento. */
export function migaDe(id: string, un: Map<string, UnidadMiga>): Paso[] {
  const out: Paso[] = []
  let k: string | undefined = id
  for (let i = 0; k && i < 4; i++) {
    const u = un.get(k)
    if (!u) break
    out.unshift({ id: k, nombre: u.nombre, nivel: u.nivel })
    if (u.nivel === 0) break
    const sig: string | undefined = u.padre_id && un.has(u.padre_id) ? u.padre_id : u.iso3
    k = sig === k ? undefined : sig
  }
  return out
}
