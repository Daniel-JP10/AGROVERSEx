// asistido por SI: Claude Code (Anthropic), escritura y revisión de código; base del prototipo migrada en el hackatón
export type Nivel = 0 | 1 | 2

export interface VariableMeta {
  id: string; nombre: string; escala: number | null; desplazamiento: number | null
  valido_min: number | null; valido_max: number | null; unidad_medida?: string | null; etiqueta?: string | null
}

export interface Meta {
  variables: VariableMeta[]
  fuentes: Record<string, unknown>[]
  metadatos: Record<string, unknown>[]
  meses: { min: number; max: number }
  unidades_por_nivel: Record<string, number>
  rotulo_estatico: string
}

export interface Coropleta {
  mes: number
  valores: Float32Array // en el orden de /api/orden, NaN = sin dato
  rango: [number, number] // rango válido en unidades físicas (X-Rango)
}

export interface Estatico {
  variable_id: string
  media: number | null // media del producto agregado, sin intervalo
  rotulo: string
  valido_min: number | null; valido_max: number | null; unidad_medida: string | null; etiqueta: string | null
}

export interface DetalleUnidad {
  unidad: Record<string, unknown>
  padre: { id: string; nombre: string; nivel: number } | null
  estatico: Estatico[]
  clases: { esquema: string; clase: string; fraccion: number }[]
  koppen?: string[] // clase_fraccion.clase es TEXT
  eventos: { id: string; tipo: string; inicio: string; fin: string; etiqueta: string; intensidad: number | null }[]
}
