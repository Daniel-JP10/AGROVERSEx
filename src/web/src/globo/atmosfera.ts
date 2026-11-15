// asistido por SI: Claude Code (Anthropic), escritura y revisión de código; halo verde y aro del globo en fase 3 (plan v2 §3)
// Halo atmosférico en un canvas propio entre las estrellas y el mapa. Se dibuja solo al mover la cámara.
import type { Map } from 'maplibre-gl'

const CAL = 0.84 // calibrado contra el limbo real en captura (z1.6): el radio visible es 0,84 del teórico
const TAM = 512 // tamaño de tesela de MapLibre en la proyección Mercator

/** Radio aparente del globo en píxeles (esfera de circunferencia TAM·2^zoom; la latitud no lo cambia en vista globo). */
export function radioGlobo(zoom: number, _latCentro: number, altoCanvas: number): number {
  if (altoCanvas <= 0) return 0
  return (CAL * TAM * 2 ** zoom) / (2 * Math.PI)
}

/** Opacidad del halo: pleno hasta zoom 5, nulo desde 7 (igual que atmosphere-blend). */
export const opacidadHalo = (zoom: number) => Math.min(1, Math.max(0, (7 - zoom) / 2))

export function iniciarHalo(canvas: HTMLCanvasElement, map: Map): () => void {
  const ctx = canvas.getContext('2d')!
  let pendiente = 0
  const dibujar = () => {
    pendiente = 0
    const dpr = window.devicePixelRatio || 1
    const w = canvas.clientWidth, h = canvas.clientHeight
    if (canvas.width !== w * dpr || canvas.height !== h * dpr) { canvas.width = w * dpr; canvas.height = h * dpr }
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0)
    ctx.clearRect(0, 0, w, h)
    const z = map.getZoom(), a = opacidadHalo(z)
    if (a <= 0 || map.getProjection()?.type === 'mercator') return
    const r = radioGlobo(z, map.getCenter().lat, h)
    const cx = w / 2, cy = h / 2
    const g = ctx.createRadialGradient(cx, cy, r * 0.97, cx, cy, r * 1.3)
    // Brillo verde de la referencia de diseño, con un aro fino que contiene el globo
    g.addColorStop(0, `rgba(123,224,160,${0.7 * a})`)
    g.addColorStop(0.35, `rgba(76,175,110,${0.32 * a})`)
    g.addColorStop(1, 'rgba(10,40,25,0)')
    ctx.fillStyle = g
    ctx.fillRect(0, 0, w, h)
    ctx.strokeStyle = `rgba(160,240,190,${0.8 * a})`
    ctx.lineWidth = 1.5
    ctx.beginPath(); ctx.arc(cx, cy, r * 1.005, 0, 2 * Math.PI); ctx.stroke()
  }
  const pedir = () => { if (!pendiente) pendiente = requestAnimationFrame(dibujar) }
  map.on('move', pedir)
  window.addEventListener('resize', pedir)
  pedir()
  return () => { map.off('move', pedir); window.removeEventListener('resize', pedir); cancelAnimationFrame(pendiente) }
}
