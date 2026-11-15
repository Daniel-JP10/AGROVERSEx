// asistido por SI: Claude Code (Anthropic), escritura y revisión de código; base del prototipo migrada en el hackatón
import { N_MESES } from './valor'

interface Opts {
  /** Meses por segundo */
  velocidad: number
  /** Pinta el mes y resuelve cuando terminó */
  siguiente: (m: number) => Promise<void>
  precargar: (desde: number, hasta: number) => void
}

const ULTIMO = N_MESES - 1

export function crearReproductor({ velocidad, siguiente, precargar }: Opts) {
  let mes = 0, gen = 0
  const pausa = () => { gen++ }
  const play = () => {
    const mi = ++gen
    void (async () => {
      // No avanza hasta que `siguiente` resolvió Y pasó el tiempo mínimo: a lo sumo 1 en vuelo
      while (gen === mi && mes < ULTIMO) {
        mes++
        if (mes < ULTIMO) precargar(mes + 1, Math.min(mes + 12, ULTIMO))
        await Promise.all([siguiente(mes), new Promise((f) => setTimeout(f, 1000 / velocidad))])
      }
    })()
  }
  return { play, pausa, irA: (m: number) => { mes = Math.min(ULTIMO, Math.max(0, m)) } }
}
