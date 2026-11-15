// asistido por SI: Claude Code (Anthropic), índice que une los textos por sección (plan fase 3 v2 §10)
import { en as base } from './en'
import { es as baseEs } from './es'
import * as marco from './secciones/marco'
import * as portada from './secciones/portada'
import * as ciencia from './secciones/ciencia'
import * as datos from './secciones/datos'
import * as fuentes from './secciones/fuentes'
import * as tierra from './secciones/tierra'
import * as lote from './secciones/lote'
import * as rotaciones from './secciones/rotaciones'

// Cada parte por separado, para que la prueba compruebe que no se pisan claves
export const PARTES: Record<string, { en: object; es: object }> = {
  base: { en: base, es: baseEs }, marco, portada, ciencia, datos, fuentes, tierra, lote, rotaciones,
}

export const enTodo = {
  ...base, ...marco.en, ...portada.en, ...ciencia.en, ...datos.en, ...fuentes.en,
  ...tierra.en, ...lote.en, ...rotaciones.en,
}
export type ClaveTodo = keyof typeof enTodo
export const esTodo: Partial<Record<ClaveTodo, string>> = {
  ...baseEs, ...marco.es, ...portada.es, ...ciencia.es, ...datos.es, ...fuentes.es,
  ...tierra.es, ...lote.es, ...rotaciones.es,
}
