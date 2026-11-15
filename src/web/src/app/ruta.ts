// asistido por SI: Claude Code (Anthropic), rutas por hash del universo (contrato web_componentes §3)
import { useSyncExternalStore } from 'react'

export const SECCIONES = ['portada', 'tierra', 'gemelo', 'rotaciones', 'ciencia', 'datos', 'fuentes'] as const
export type Seccion = (typeof SECCIONES)[number]
export type Ruta = { seccion: Seccion; params: Record<string, string> }

const SEGMENTO: Record<Seccion, string> = { portada: '', tierra: 'tierra', gemelo: 'gemelo', rotaciones: 'rotaciones', ciencia: 'ciencia', datos: 'datos', fuentes: 'fuentes' }
// Parámetros que admite cada sección, en el orden en que se escriben
const PARAMS: Record<Seccion, string[]> = {
  portada: [], tierra: ['unidad', 'variable', 'mes'], gemelo: ['lote'], rotaciones: ['unidad', 'lote'], ciencia: [], datos: [], fuentes: [],
}

/** Lee `#/seccion?param=valor`; lo desconocido va a la portada y los parámetros no admitidos se descartan. */
export function leerRuta(hash: string): Ruta {
  const [camino, consulta = ''] = hash.replace(/^#/, '').split('?')
  const seccion = SECCIONES.find((s) => `/${SEGMENTO[s]}` === camino.replace(/\/+$/, '') || (s === 'portada' && camino === '/')) ?? 'portada'
  const q = new URLSearchParams(consulta)
  const params: Record<string, string> = {}
  for (const p of PARAMS[seccion]) { const v = q.get(p); if (v) params[p] = v }
  return { seccion, params }
}

export function aHash({ seccion, params }: Ruta): string {
  const q = new URLSearchParams()
  for (const p of PARAMS[seccion]) if (params[p]) q.set(p, params[p])
  const s = q.toString()
  return `#/${SEGMENTO[seccion]}${s ? `?${s}` : ''}`
}

export const irA = (seccion: Seccion, params: Record<string, string> = {}) => { window.location.hash = aHash({ seccion, params }) }

const suscribir = (fn: () => void) => { window.addEventListener('hashchange', fn); return () => window.removeEventListener('hashchange', fn) }

/** Ruta actual; se repinta al cambiar el hash. */
export function useRuta(): Ruta {
  const hash = useSyncExternalStore(suscribir, () => window.location.hash, () => '')
  return leerRuta(hash)
}
