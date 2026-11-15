// asistido por SI: Claude Code (Anthropic), escritura y revisión de código; fase 3 sin lectura de coordenadas en vivo (plan v2 §3)
import { useEffect, useState } from 'react'
import type { Map as MapaGL } from 'maplibre-gl'
import { useEstado } from '../app/estado'
import { t } from '../textos/i18n'

/** Longitud "redonda" de barra de escala (m) que cabe en ~100 px. */
function escala(mapa: MapaGL): { px: number; texto: string } {
  const lat = mapa.getCenter().lat
  const mPorPx = (40075016.686 * Math.cos((lat * Math.PI) / 180)) / (512 * 2 ** mapa.getZoom())
  const crudo = mPorPx * 100
  const pot = 10 ** Math.floor(Math.log10(crudo))
  const m = [1, 2, 5, 10].map((k) => k * pot).filter((v) => v <= crudo).at(-1)!
  return { px: m / mPorPx, texto: m >= 1000 ? `${m / 1000} km` : `${m} m` }
}

export function Controles({ mapa }: { mapa: MapaGL }) {
  const proyeccion = useEstado((s) => s.proyeccion)
  const setProyeccion = useEstado((s) => s.setProyeccion)
  const [rumbo, setRumbo] = useState(0)
  const [esc, setEsc] = useState(() => escala(mapa))

  useEffect(() => {
    let r = 0
    const al = () => { cancelAnimationFrame(r); r = requestAnimationFrame(() => { setRumbo(mapa.getBearing()); setEsc(escala(mapa)) }) }
    mapa.on('move', al)
    return () => { mapa.off('move', al); cancelAnimationFrame(r) }
  }, [mapa])

  return (
    <>
      <div className="controles">
        <button aria-label={t('globo.norte')} title={t('globo.norte')} onClick={() => mapa.easeTo({ bearing: 0, pitch: 0 })}>
          <svg viewBox="0 0 24 24" width="20" height="20" style={{ transform: `rotate(${-rumbo}deg)` }}>
            <path d="M12 3l4 9h-8z" fill="#ff8a5c" /><path d="M12 21l-4-9h8z" fill="#8aa0b4" />
          </svg>
        </button>
        <button onClick={() => setProyeccion(proyeccion === 'globe' ? 'mercator' : 'globe')} aria-label={t('globo.vista')}>
          {proyeccion === 'globe' ? '2D' : '3D'}
        </button>
        <button aria-label={t('globo.acercar')} onClick={() => mapa.zoomIn()}>+</button>
        <button aria-label={t('globo.alejar')} onClick={() => mapa.zoomOut()}>−</button>
      </div>
      <div className="barra-inferior">
        <span className="escala" style={{ width: esc.px }} />
        <span>{esc.texto}</span>
      </div>
    </>
  )
}
