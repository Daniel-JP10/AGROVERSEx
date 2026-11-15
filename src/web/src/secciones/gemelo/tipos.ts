// asistido por SI: Claude Code (Anthropic), tipos locales de la v1 del contrato del gemelo que usa la sección
// Solo los campos de contratos/gemelo_api.md v1 que se leen; si secciones/rotaciones/gemelo.ts llega a web, se importan de allí
export const VARIABLES = ['W', 'N', 'C', 'B', 'V', 'desnudo'] as const
export type VariableGemelo = (typeof VARIABLES)[number]
// Las cinco que se dibujan; desnudo da las ventanas
export const DIBUJADAS = ['W', 'N', 'C', 'B', 'V'] as const satisfies readonly VariableGemelo[]

export type Banda = { p10: number[]; p50: number[]; p90: number[] }
export type TrayectoriaMensual = Record<VariableGemelo, Banda>
export type Estrategia = { nombre: string; trayectoria_mensual: TrayectoriaMensual }

// ejemplo: ficticio detrás de VITE_EJEMPLOS (SIMULADO); corrida: salida real del gemelo (simulación del modelo)
export type Origen = 'ejemplo' | 'corrida'
