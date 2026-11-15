// asistido por SI: Claude Code (Anthropic), escritura y revisión de código; base del prototipo migrada en el hackatón
// Estrellas en un canvas propio detrás del mapa transparente. Giran con la cámara.
import type { Map } from 'maplibre-gl'

const N = 1800
// Direcciones fijas sobre la esfera celeste, con semilla determinista
const estrellas = (() => {
  let s = 12345
  const r = () => ((s = (Math.imul(s, 1664525) + 1013904223) >>> 0) / 4294967296)
  return Array.from({ length: N }, () => {
    const z = 2 * r() - 1
    const a = 2 * Math.PI * r()
    const q = Math.sqrt(1 - z * z)
    return { x: q * Math.cos(a), y: q * Math.sin(a), z, b: 0.3 + 0.7 * r() ** 2, t: ((u) => (u < 0.03 ? 2.4 : u < 0.15 ? 1.6 : 0.9))(r()) }
  })
})()

export function iniciarEstrellas(canvas: HTMLCanvasElement, map: Map): () => void {
  const ctx = canvas.getContext('2d')!
  let pendiente = 0
  const dibujar = () => {
    pendiente = 0
    const dpr = window.devicePixelRatio || 1
    const w = canvas.clientWidth, h = canvas.clientHeight
    if (canvas.width !== w * dpr || canvas.height !== h * dpr) { canvas.width = w * dpr; canvas.height = h * dpr }
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0)
    ctx.clearRect(0, 0, w, h)
    const c = map.getCenter()
    const lng = (c.lng * Math.PI) / 180, lat = (c.lat * Math.PI) / 180
    const rumbo = (-map.getBearing() * Math.PI) / 180
    const cl = Math.cos(lng), sl = Math.sin(lng), cp = Math.cos(lat), sp = Math.sin(lat)
    const cr = Math.cos(rumbo), sr = Math.sin(rumbo)
    const f = Math.max(w, h) * 0.9
    ctx.fillStyle = '#fff'
    for (const e of estrellas) {
      // girar por longitud (eje z), luego por latitud (eje y): el centro del mapa queda en +x
      const x1 = e.x * cl + e.y * sl, y1 = -e.x * sl + e.y * cl
      const x2 = x1 * cp + e.z * sp, z2 = -x1 * sp + e.z * cp
      if (x2 < 0.2) continue
      const sx = y1 / x2, sy = -z2 / x2 // plano de pantalla
      const rx = sx * cr - sy * sr, ry = sx * sr + sy * cr
      const px = w / 2 + rx * f, py = h / 2 + ry * f
      if (px < 0 || py < 0 || px > w || py > h) continue
      // centelleo mínimo: leve variación de brillo según la posición, sin estado por frame
      ctx.globalAlpha = e.b * (0.85 + 0.15 * Math.sin(px * 0.37 + py * 0.51))
      ctx.fillRect(px, py, e.t, e.t)
    }
  }
  const pedir = () => { if (!pendiente) pendiente = requestAnimationFrame(dibujar) }
  map.on('move', pedir)
  window.addEventListener('resize', pedir)
  pedir()
  return () => { map.off('move', pedir); window.removeEventListener('resize', pedir); cancelAnimationFrame(pendiente) }
}
