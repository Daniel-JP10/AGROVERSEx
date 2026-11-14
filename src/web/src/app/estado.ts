// asistido por SI: Claude Code (Anthropic), escritura y revisión de código; base del prototipo migrada en el hackatón
import { create } from 'zustand'
import { N_MESES } from '../tiempo/valor'
import { leerOpacidad, guardarOpacidad, type FiltroUnidad } from '../globo/coropleta'
import { claveUnidad, porClave, type Unidad } from '../datos/indice'
import { CAPA_INICIAL } from '../datos/capas'

interface Estado {
  mes: number
  reproduciendo: boolean
  /** Hay un mes pendiente de pintar (gesto de cámara en curso o rebanadas sin terminar) */
  pintando: boolean
  setPintando: (p: boolean) => void
  /** Variable pintada en el mapa (datos/capas.ts) */
  capa: string
  setCapa: (c: string) => void
  opacidad: number
  setOpacidad: (n: number) => void
  filtro: FiltroUnidad
  setFiltro: (f: FiltroUnidad) => void
  proyeccion: 'globe' | 'mercator'
  seleccion: Unidad | null
  /** Aviso breve (p. ej. no se pudo centrar la unidad) */
  aviso: string | null
  setAviso: (a: string | null) => void
  setMes: (m: number) => void
  setReproduciendo: (r: boolean) => void
  setProyeccion: (p: 'globe' | 'mercator') => void
  /** Selecciona una unidad; el globo reacciona (resalta y hace fly-to). */
  seleccionar: (u: Unidad | null) => void
  seleccionarPorId: (nivel: number, id: number | string) => void
}

export const useEstado = create<Estado>((set) => ({
  mes: 0,
  reproduciendo: false,
  pintando: false,
  setPintando: (pintando) => set({ pintando }),
  capa: CAPA_INICIAL,
  setCapa: (capa) => set({ capa }),
  opacidad: leerOpacidad(),
  setOpacidad: (opacidad) => { guardarOpacidad(opacidad); set({ opacidad }) },
  filtro: {},
  setFiltro: (filtro) => set({ filtro }),
  proyeccion: 'globe',
  seleccion: null,
  aviso: null,
  setAviso: (aviso) => set({ aviso }),
  setMes: (mes) => set({ mes: Math.min(N_MESES - 1, Math.max(0, mes)) }),
  setReproduciendo: (reproduciendo) => set({ reproduciendo }),
  setProyeccion: (proyeccion) => set({ proyeccion }),
  seleccionar: (seleccion) => set({ seleccion, aviso: null }),
  seleccionarPorId: (nivel, id) => {
    const u = porClave.get(claveUnidad(nivel, id))
    if (u) set({ seleccion: u })
  },
}))
