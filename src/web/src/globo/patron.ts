// asistido por SI: Claude Code (Anthropic), escritura y revisión de código; base del prototipo migrada en el hackatón
import type { Map as MapaGL } from 'maplibre-gl'

export const ID_PATRON = 'sin-dato'
export const COLOR_TRAMA = '#d7dde6'

// Trama de rayas sobre fondo casi transparente: "sin dato del producto" (no es 0 ni un color de la escala)
function tramaHueco(): ImageData {
  const c = document.createElement('canvas')
  c.width = c.height = 10
  const g = c.getContext('2d')!
  g.fillStyle = 'rgba(20,26,36,0.55)'; g.fillRect(0, 0, 10, 10)
  g.strokeStyle = COLOR_TRAMA; g.lineWidth = 1.5
  g.beginPath(); g.moveTo(-1, 11); g.lineTo(11, -1); g.stroke()
  return g.getImageData(0, 0, 10, 10)
}

export function registrarPatron(map: Pick<MapaGL, 'hasImage' | 'addImage'>) {
  if (!map.hasImage(ID_PATRON)) map.addImage(ID_PATRON, tramaHueco())
}
