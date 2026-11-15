// asistido por SI: Claude Code (Anthropic), los pasos del recorrido guiado escritos como datos
import type { ClaveTexto } from '../../textos/en'
import type { Seccion } from '../ruta'

/** Un valor fijo o el nombre de un dato que llena una fuente (textos/huecos.ts). */
export type Valor = string | { dato: string }
export type Accion =
  | { fn: 'irAUnidad'; unidad: Valor }
  | { fn: 'cambiarVariable'; variable: Valor }
  | { fn: 'cambiarMes'; mes: Valor }
  | { fn: 'activarComparador'; activo: boolean }
  | { fn: 'abrirPestana'; nombre: string }

export interface Paso {
  id: string
  ruta: Seccion
  params?: Record<string, Valor>
  acciones?: Accion[]
  texto: ClaveTexto
  /** Todo dato que el paso necesita; si alguno falta, el paso muestra aviso.sin_dato. */
  datos: string[]
}

const IPIALES: Valor = { dato: 'unidad_ipiales' }

// Fuente: Docu/web/T-W1_guion_recorrido.md; cada hueco lo llena cargarHuecos.ts. Ningún número va escrito aquí.
// shortcut: 2.2 solo fija mes_inicio en el globo; mes_fin se muestra en el texto pero no se anima
export const PASOS: readonly Paso[] = [
  { id: '1.1', ruta: 'portada', texto: 'recorrido.paso_1_1', datos: [] },
  { id: '1.2', ruta: 'tierra', acciones: [{ fn: 'irAUnidad', unidad: { dato: 'unidad_lote_eeuu' } }], texto: 'recorrido.paso_1_2', datos: ['unidad_lote_eeuu'] },
  { id: '1.3', ruta: 'ciencia', texto: 'recorrido.paso_1_3', datos: ['acierto_suelo_desnudo', 'acierto_p10', 'acierto_p90'] },
  { id: '1.4', ruta: 'ciencia', texto: 'recorrido.paso_1_4', datos: ['error_imerg_estaciones'] },
  { id: '2.1', ruta: 'tierra', acciones: [{ fn: 'cambiarVariable', variable: { dato: 'variable_confianza' } }], texto: 'recorrido.paso_2_1', datos: ['variable_confianza'] },
  { id: '2.2', ruta: 'tierra', acciones: [{ fn: 'cambiarMes', mes: { dato: 'mes_inicio' } }], texto: 'recorrido.paso_2_2', datos: ['mes_inicio', 'mes_fin'] },
  { id: '2.3', ruta: 'tierra', acciones: [{ fn: 'activarComparador', activo: true }], texto: 'recorrido.paso_2_3', datos: [] },
  { id: '2.4', ruta: 'tierra', texto: 'recorrido.paso_2_4', datos: ['fraccion_unidades_confianza_alta'] },
  {
    id: '3.1', ruta: 'tierra',
    acciones: [{ fn: 'irAUnidad', unidad: IPIALES }, { fn: 'abrirPestana', nombre: 'Rotaciones' }, { fn: 'activarComparador', activo: false }],
    texto: 'recorrido.paso_3_1', datos: ['unidad_ipiales', 'hls_validos_ipiales', 'hls_ipiales_min', 'hls_ipiales_max', 'hls_validos_saunders', 'nombre_lote_col', 'nombre_lote_eeuu'],
  },
  { id: '3.2', ruta: 'rotaciones', params: { unidad: IPIALES, lote: { dato: 'lote_ipiales' } }, texto: 'recorrido.paso_3_2', datos: ['unidad_ipiales', 'lote_ipiales', 'n_alternativas'] },
  { id: '3.3', ruta: 'rotaciones', texto: 'recorrido.paso_3_3', datos: ['tarjeta'] },
  { id: '3.4', ruta: 'rotaciones', texto: 'recorrido.paso_3_4', datos: ['campos_no_medidos'] },
  { id: '3.5', ruta: 'rotaciones', texto: 'recorrido.paso_3_5', datos: ['indicador_calibrado', 'banda_antes', 'banda_despues'] },
  { id: '3.6', ruta: 'rotaciones', texto: 'recorrido.paso_3_6', datos: [] },
  { id: '4.1', ruta: 'datos', texto: 'recorrido.paso_4_1', datos: [] },
  { id: '4.2', ruta: 'fuentes', texto: 'recorrido.paso_4_2', datos: [] },
]
