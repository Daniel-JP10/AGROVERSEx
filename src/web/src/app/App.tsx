// asistido por SI: Claude Code (Anthropic), escritura y revisión de código; base del prototipo migrada en el hackatón
import { useState } from 'react'
import type { Map as MapaGL } from 'maplibre-gl'
import { Globo } from '../globo/Globo'
import { useEstado } from './estado'
import { Medir } from '../herramientas/Medir'
import { AvisoZoom } from '../herramientas/AvisoZoom'
import { Busqueda } from '../paneles/Busqueda'
import { PanelRegion } from '../paneles/PanelRegion'
import { LineaTiempo } from '../tiempo/LineaTiempo'
import { PanelCapas } from '../paneles/PanelCapas'
import { Fps } from './Fps'
import { Riel } from './Riel'
import { Cabecera } from './Cabecera'
import { Dividida } from '../comparar/Dividida'
import { Escenario } from '../comparar/Escenario'
import { AVISO_PIE } from '../textos/avisos'

export function App() {
  // Herramienta activa del riel: aún sin función (se conectan en tareas siguientes)
  const [activa, setActiva] = useState('')
  const [mapa, setMapa] = useState<MapaGL | null>(null)
  const proyeccion = useEstado((s) => s.proyeccion)
  const [mesB, setMesB] = useState(120)
  return (
    <div className="app">
      <Cabecera />
      <div className="centro">
        <main className="zona-mapa">
          <Globo onMapa={setMapa} />
          <Busqueda />
          <Riel activa={activa} onElegir={(id) => setActiva(activa === id ? '' : id)} />
          <PanelCapas herramienta={activa} />
          {mapa && activa === 'comparar' && <Dividida mapa={mapa} mesB={mesB} setMesB={setMesB} />}
          {activa === 'escenario' && <Escenario />}
          {mapa && activa === 'medir' && <Medir mapa={mapa} />}
          {mapa && <AvisoZoom mapa={mapa} proyeccion={proyeccion} />}
          <PanelRegion />
          {import.meta.env.DEV && <Fps />}
        </main>
      </div>
      <LineaTiempo />
      <footer className="pie">{AVISO_PIE}</footer>
    </div>
  )
}
