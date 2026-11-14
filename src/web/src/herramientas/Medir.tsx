// asistido por SI: Claude Code (Anthropic), escritura y revisión de código; base del prototipo migrada en el hackatón
import { useEffect, useState } from 'react'
import type { Map as MapaGL, MapMouseEvent } from 'maplibre-gl'
import { areaKm2, distanciaKm } from './geodesia'
import './herramientas.css'

export type Modo = 'distancia' | 'area'

// Resultado en texto: la cifra siempre lleva su método (línea recta o área esférica)
export function resumen(modo: Modo, puntos: [number, number][]): string {
  if (modo === 'distancia') {
    if (puntos.length < 2) return 'Añade al menos 2 puntos'
    let total = 0
    for (let i = 1; i < puntos.length; i++) total += distanciaKm(puntos[i - 1], puntos[i])
    return `${total.toFixed(1)} km (línea recta, geodésica)`
  }
  if (puntos.length < 3) return 'Añade al menos 3 puntos'
  return `${areaKm2(puntos).toFixed(1)} km² (área esférica)`
}

export function Medir({ mapa }: { mapa: MapaGL }) {
  const [modo, setModo] = useState<Modo>('distancia')
  const [puntos, setPuntos] = useState<[number, number][]>([])

  // Clic en el mapa añade un punto; el botón de centro sirve también con teclado
  useEffect(() => {
    const alClic = (e: MapMouseEvent) => setPuntos((p) => [...p, [e.lngLat.lng, e.lngLat.lat]])
    mapa.on('click', alClic)
    return () => { mapa.off('click', alClic) }
  }, [mapa])

  const elegir = (m: Modo) => { setModo(m); setPuntos([]) }
  const alCentro = () => { const c = mapa.getCenter(); setPuntos((p) => [...p, [c.lng, c.lat]]) }

  return (
    <aside className="panel medir" aria-label="Medir">
      <h2>Medir</h2>
      <div role="group" aria-label="Tipo de medición" className="medir-modo">
        <button type="button" aria-pressed={modo === 'distancia'} onClick={() => elegir('distancia')}>Distancia</button>
        <button type="button" aria-pressed={modo === 'area'} onClick={() => elegir('area')}>Área</button>
      </div>
      <p className="etiqueta">Haz clic en el mapa para poner puntos, o usa el botón:</p>
      <div className="medir-acciones">
        <button type="button" onClick={alCentro}>Añadir punto en el centro</button>
        <button type="button" onClick={() => setPuntos((p) => p.slice(0, -1))} disabled={!puntos.length}>Deshacer último punto</button>
        <button type="button" onClick={() => setPuntos([])}>Borrar</button>
      </div>
      <p role="status" aria-live="polite" className="medir-resultado">
        {resumen(modo, puntos)} · {puntos.length} puntos
      </p>
      <p className="etiqueta">Esfera de radio medio: error frente al elipsoide de hasta ~0,5 %. No es una medición oficial.</p>
    </aside>
  )
}
