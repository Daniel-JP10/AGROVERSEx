// asistido por SI: Claude Code (Anthropic), escritura y revisión de código; base del prototipo migrada en el hackatón
import { decodificarCoropleta } from './binario'
import type { Coropleta, DetalleUnidad, Meta, Nivel } from './tipos'

export type Fetcher = (url: string) => Promise<Response>

export interface Cliente {
  meta(): Promise<Meta>
  orden(nivel: Nivel): Promise<string[]>
  coropleta(nivel: Nivel, variable: string, mes: number): Promise<Coropleta>
  unidad(id: string): Promise<DetalleUnidad>
}

// Un reintento y luego el error sube (la interfaz lo muestra y conserva el último mes bueno).
async function pedir(f: Fetcher, url: string): Promise<Response> {
  for (let intento = 0; ; intento++) {
    try {
      const r = await f(url)
      if (!r.ok) throw new Error(`${url}: HTTP ${r.status}`)
      return r
    } catch (e) {
      if (intento >= 1) throw e
    }
  }
}

export function crearCliente(f: Fetcher = (u) => fetch(u)): Cliente {
  const json = async <T>(u: string) => (await pedir(f, u)).json() as Promise<T>
  return {
    meta: () => json<Meta>('/api/meta'),
    orden: async (n) => (await json<{ ids: string[] }>(`/api/orden?nivel=${n}`)).ids,
    async coropleta(nivel, variable, mes) {
      const r = await pedir(f, `/api/coropleta?nivel=${nivel}&var=${encodeURIComponent(variable)}&mes=${mes}`)
      const esc = Number(r.headers.get('X-Escala')), des = Number(r.headers.get('X-Desplazamiento') ?? 0)
      const [a, b] = (r.headers.get('X-Rango') ?? 'NaN,NaN').split(',').map(Number)
      return { mes, valores: decodificarCoropleta(await r.arrayBuffer(), esc, des), rango: [a, b] }
    },
    async unidad(id) {
      const d = await json<DetalleUnidad>(`/api/unidad/${encodeURIComponent(id)}`)
      return { ...d, koppen: d.clases.filter((c) => c.esquema === 'koppen').map((c) => c.clase) }
    },
  }
}
