// asistido por SI: Claude Code (Anthropic), huecos {nombre_del_dato} de los textos y su fuente de datos
export type Resolver = (nombre: string) => string | undefined
export type Parte = { t: 'texto' | 'valor' | 'hueco'; v: string }

import { create } from 'zustand'

// De partida solo el unidad_id de Ipiales (contratos/unidades.md v0, un identificador, no una cifra).
// El resto lo llena app/recorrido/cargarHuecos.ts desde los archivos públicos; nunca se escribe en los textos
export const useHuecos = create<{ valores: Record<string, string> }>(() => ({ valores: { unidad_ipiales: 'COL-ADM2-7082276B52108893597118' } }))
export const fijarHuecos = (v: Record<string, string>) => useHuecos.setState((s) => ({ valores: { ...s.valores, ...v } }))
export const dato: Resolver = (nombre) => useHuecos.getState().valores[nombre]

/** Parte el texto en tramos fijos, valores entregados y huecos; `faltan` lista los nombres sin dato. */
export function rellenar(texto: string, resolver: Resolver = dato): { partes: Parte[]; faltan: string[] } {
  const partes: Parte[] = []
  const faltan: string[] = []
  texto.split(/\{(\w+)\}/).forEach((tramo, i) => {
    if (i % 2 === 0) { if (tramo) partes.push({ t: 'texto', v: tramo }); return }
    const valor = resolver(tramo)
    if (valor === undefined) { partes.push({ t: 'hueco', v: tramo }); if (!faltan.includes(tramo)) faltan.push(tramo) } else partes.push({ t: 'valor', v: valor })
  })
  return { partes, faltan }
}
