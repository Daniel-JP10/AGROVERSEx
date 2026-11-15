// asistido por SI: Claude Code (Anthropic), escritura y revisión de código; base del prototipo migrada en el hackatón
import { useEffect, useState } from 'react'
import type { Map as MapaGL } from 'maplibre-gl'
import './herramientas.css'
import { t } from '../textos/i18n'

// MapLibre cambia el globo por Mercator desde este zoom aunque el botón siga en 3D
export const ZOOM_MERCATOR = 12

export function debeAvisarZoom(zoom: number, proyeccion: 'globe' | 'mercator'): boolean {
  return proyeccion === 'globe' && zoom >= ZOOM_MERCATOR
}

// La proyección llega por prop para no arrastrar el store en las pruebas
export function AvisoZoom({ mapa, proyeccion }: { mapa: MapaGL; proyeccion: 'globe' | 'mercator' }) {
  const [zoom, setZoom] = useState(() => mapa.getZoom())
  useEffect(() => {
    const alZoom = () => setZoom(mapa.getZoom())
    mapa.on('zoom', alZoom)
    return () => { mapa.off('zoom', alZoom) }
  }, [mapa])
  if (!debeAvisarZoom(zoom, proyeccion)) return null
  return (
    <p role="status" className="aviso-zoom">
      {t('zoom.mercator').replace('{zoom}', String(ZOOM_MERCATOR))}
    </p>
  )
}
