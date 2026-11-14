// asistido por SI: Claude Code (Anthropic), escritura y revisión de código; base del prototipo migrada en el hackatón
import type { Map as MapaGL } from 'maplibre-gl'

// Cámaras gemelas: lo que mueve a uno lo copia el otro; el indicador evita el eco (jumpTo dispara 'move').
export function sincronizarCamaras(a: MapaGL, b: MapaGL): () => void {
  let copiando = false
  const enlace = (de: MapaGL, a: MapaGL) => () => {
    if (copiando) return
    copiando = true
    try { a.jumpTo({ center: de.getCenter(), zoom: de.getZoom(), bearing: de.getBearing(), pitch: de.getPitch() }) } finally { copiando = false }
  }
  const ab = enlace(a, b), ba = enlace(b, a)
  a.on('move', ab); b.on('move', ba)
  return () => { a.off('move', ab); b.off('move', ba) }
}

export interface Escenario { valor: number; bloqueado: boolean; motivo?: string }

// El escenario nunca sale de p25-p75 de la unidad: fuera se recorta y se explica.
export function limitarEscenario(valor: number, p25: number, p75: number): Escenario {
  if (valor >= p25 && valor <= p75) return { valor, bloqueado: false }
  return {
    valor: Math.min(p75, Math.max(p25, valor)), bloqueado: true,
    motivo: 'El escenario se limita al rango p25-p75 de esta unidad: fuera de él no hay respaldo en sus datos.',
  }
}

// Percentil con interpolación lineal (q en 0..1), ignorando huecos; null si no hay datos.
export function percentil(v: (number | null)[], q: number): number | null {
  const s = v.filter((x): x is number => x !== null).sort((x, y) => x - y)
  if (!s.length) return null
  const p = (s.length - 1) * q, i = Math.floor(p)
  return s[i] + (s[Math.min(i + 1, s.length - 1)] - s[i]) * (p - i)
}
