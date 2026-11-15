// asistido por SI: Claude Code (Anthropic), estado del recorrido guiado: activo y paso actual
import { create } from 'zustand'
import { PASOS } from './pasos'

interface Recorrido { activo: boolean; indice: number; iniciar: () => void; siguiente: () => void; anterior: () => void; salir: () => void }

export const useRecorrido = create<Recorrido>((set) => ({
  activo: false,
  indice: 0,
  iniciar: () => set({ activo: true, indice: 0 }),
  siguiente: () => set((s) => ({ indice: Math.min(s.indice + 1, PASOS.length - 1) })),
  anterior: () => set((s) => ({ indice: Math.max(s.indice - 1, 0) })),
  salir: () => set({ activo: false, indice: 0 }),
}))
