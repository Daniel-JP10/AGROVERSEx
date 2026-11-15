// asistido por SI: Claude Code (Anthropic), llamada "Select a lot" con línea fina a cada lote DEMO y vuelo al lote (plan v2 §3)
import { useEffect, useRef, useState } from 'react'
import type { Map as MapaGL } from 'maplibre-gl'
import { rutaPublica } from '../../comun/rutas'
import { idioma, t, useIdioma } from '../../textos/i18n'

export type LoteDemo = { lote_id: string; nombre: string; nombre_en?: string; lat: number; lon: number }

// Zoom del vuelo: un lote de unas 75 ha ocupa la vista central
export const ZOOM_LOTE = 13
export const hashLote = (id: string) => `#/lote?lote=${encodeURIComponent(id)}`
export const reducirMovimiento = () => typeof matchMedia === 'function' && matchMedia('(prefers-reduced-motion: reduce)').matches

/** Vuela (o salta con reduced-motion) al punto real del lote y al terminar abre #/lote. */
export function irALote(mapa: MapaGL, l: LoteDemo, abrir: (hash: string) => void = (h) => { window.location.hash = h }) {
  mapa.once('moveend', () => abrir(hashLote(l.lote_id)))
  const destino = { center: [l.lon, l.lat] as [number, number], zoom: ZOOM_LOTE }
  if (reducirMovimiento()) mapa.jumpTo(destino)
  else mapa.flyTo({ ...destino, duration: 2400, essential: true })
}

export function SeleccionLote({ mapa }: { mapa: MapaGL }) {
  useIdioma()
  const [lotes, setLotes] = useState<LoteDemo[] | null>(null)
  const [error, setError] = useState(false)
  const caja = useRef<HTMLDivElement>(null)
  const [lineas, setLineas] = useState<{ id: string; x1: number; y1: number; x2: number; y2: number }[]>([])

  useEffect(() => {
    fetch(rutaPublica('datos/lotes_demo.json'))
      .then((r) => { if (!r.ok) throw new Error(String(r.status)); return r.json() as Promise<{ lotes: LoteDemo[] }> })
      .then((d) => setLotes(d.lotes))
      .catch(() => setError(true))
  }, [])

  // Las líneas siguen a la cámara: del borde de la llamada al punto proyectado del lote
  useEffect(() => {
    if (!lotes) return
    const medir = () => {
      const c = mapa.getContainer().getBoundingClientRect(), b = caja.current?.getBoundingClientRect()
      if (!b) return
      // shortcut: no se oculta la línea si el lote queda en la cara oculta del globo; los dos lotes se ven en la vista inicial
      setLineas(lotes.map((l) => {
        const p = mapa.project([l.lon, l.lat])
        return { id: l.lote_id, x1: b.left - c.left, y1: b.top - c.top + b.height / 2, x2: p.x, y2: p.y }
      }).filter((l) => l.x2 >= 0 && l.y2 >= 0 && l.x2 <= c.width && l.y2 <= c.height))
    }
    medir()
    mapa.on('move', medir)
    addEventListener('resize', medir)
    return () => { mapa.off('move', medir); removeEventListener('resize', medir) }
  }, [mapa, lotes])

  return (
    <>
      <svg className="lotes-lineas" aria-hidden="true" focusable="false">
        {lineas.map((l) => (
          <g key={l.id}>
            <line x1={l.x1} y1={l.y1} x2={l.x2} y2={l.y2} />
            <circle cx={l.x2} cy={l.y2} r={4} />
          </g>
        ))}
      </svg>
      <div ref={caja} className="hoja hoja-lotes" role="group" aria-labelledby="titulo-lotes">
        <h2 id="titulo-lotes">{t('tierra.lotes.titulo')}</h2>
        <p className="hueco">{t('tierra.lotes.ayuda')}</p>
        {error && <p role="alert">{t('tierra.lotes.error')}</p>}
        {lotes?.map((l) => (
          <button key={l.lote_id} data-lote={l.lote_id} onClick={() => irALote(mapa, l)}>
            {idioma() === 'en' ? (l.nombre_en ?? l.nombre) : l.nombre}
          </button>
        ))}
      </div>
    </>
  )
}
