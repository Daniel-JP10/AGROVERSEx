// asistido por SI: Claude Code (Anthropic), tipos de la salida de optimización del gemelo según contratos/gemelo_api.md v1.1
// Campos de la v1 más los aditivos de la v1.1 que usa Web, todos opcionales. Los números pueden venir null (el gemelo los sirve así si no son finitos).
import type { Catalogo } from './textosGemelo'
import type { AlertaHeladaGemelo } from './AlertaHelada'
export interface Indicador {
  p10: number | null
  p50: number | null
  p90: number | null
  unidad: string
  definicion: string
  explicacion: string
  nombre_clave?: string
  explicacion_clave?: string
}

export interface Trayectoria { [variable: string]: { p10: (number | null)[]; p50: (number | null)[]; p90: (number | null)[] } }

export interface FrenteALineaBase { gana: string[]; cede: string[]; similar: string[] }

export interface EstrategiaGemelo {
  id: string
  nombre: string
  etiqueta: string
  secuencia: string
  indicadores: Record<string, Indicador>
  trayectoria_mensual?: Trayectoria
  // Solo en optimización: valor de cada objetivo en unidades naturales (sin banda)
  objetivos?: Record<string, number | null>
  // Paquete del gemelo v1.2 §4: valor natural de todos los objetivos, con exposicion_erosiva (y el alias obsoleto)
  metricas?: Record<string, number | null>
  frente_a_linea_base?: FrenteALineaBase
}

export interface Objetivo { id: string; indicador: string; sentido: 'max' | 'min'; texto: string; texto_clave?: string }

// v1.1 §2 y §3: entrada de texto por clave con su plantilla
export interface EntradaTexto { clave: string; parametros?: Record<string, unknown>; valores?: Record<string, unknown>; referencias?: string[] }
export const SECCIONES_TARJETA = ['por_que', 'evidencia', 'beneficios', 'vacios', 'riesgos'] as const
export type SeccionTarjeta = (typeof SECCIONES_TARJETA)[number]
export type Tarjeta = Record<SeccionTarjeta, EntradaTexto[]> & { referencia?: string; secciones_claves?: Record<SeccionTarjeta, string> }
export interface Rotulo { clave: string; parametros?: Record<string, unknown>; en?: string; es?: string }

export interface Compromisos {
  mejor_por_objetivo: Record<string, string>
  compromiso_equilibrado: string
  explicacion: string[]
  explicacion_claves?: EntradaTexto[]
}

export interface SalidaOptimizacion {
  metadatos: { naturaleza: string; version_contrato: number; version_contrato_completa?: string; tipo: 'simulacion' | 'optimizacion'; rotulo?: Rotulo }
  avisos: string[]
  avisos_claves?: EntradaTexto[]
  tarjetas?: Record<string, Tarjeta>
  alertas?: { helada_etapa_sensible?: AlertaHeladaGemelo }
  objetivos: Objetivo[]
  linea_base: EstrategiaGemelo
  frente: EstrategiaGemelo[]
  compromisos: Compromisos
}

// De dónde vienen los datos decide el rótulo (no metadatos.naturaleza, que en el gemelo siempre es simulado)
export type Origen = 'ejemplo' | 'modelo'

export type Fuente =
  | { estado: 'sin_lote' }
  | { estado: 'cargando' }
  | { estado: 'sin_dato' }
  | { estado: 'listo'; origen: Origen; doc: SalidaOptimizacion; catalogo?: Catalogo }
