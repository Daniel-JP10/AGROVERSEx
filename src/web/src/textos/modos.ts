// asistido por SI: Claude Code (Anthropic), escritura y revisión de código; base del prototipo migrada en el hackatón
import { create } from 'zustand'

export type Modo = 'agricultor' | 'tecnico'
export const useModo = create<{ modo: Modo; set: (m: Modo) => void }>((set) => ({ modo: 'agricultor', set: (modo) => set({ modo }) }))

// El técnico ve el texto base más el detalle; los datos son los mismos
export const detalle = (modo: Modo, base: string, extra: string) => (modo === 'tecnico' ? `${base} ${extra}` : base)
