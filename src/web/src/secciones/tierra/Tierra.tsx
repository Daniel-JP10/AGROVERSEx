// asistido por SI: Claude Code (Anthropic), sección Tierra: globo en círculo, hojas de búsqueda, leyenda y tiempo, y llamada a los lotes (plan v2 §3)
import { useEffect, useState } from 'react'
import type { Map as MapaGL } from 'maplibre-gl'
import { Globo } from '../../globo/Globo'
import { useEstado } from '../../app/estado'
import { Medir } from '../../herramientas/Medir'
import { AvisoZoom } from '../../herramientas/AvisoZoom'
import { Busqueda } from '../../paneles/Busqueda'
import { PanelRegion } from '../../paneles/PanelRegion'
import { LineaTiempo } from '../../tiempo/LineaTiempo'
import { PanelCapas } from '../../paneles/PanelCapas'
import { SeleccionLote } from './SeleccionLote'
import './tierra.css'
import { Riel } from './Riel'
import { Dividida } from '../../comparar/Dividida'
import { Escenario } from '../../comparar/Escenario'
import { useIdioma } from '../../textos/i18n'
import { useRuta } from '../../app/ruta'
import { aplicarParams } from './aplicarRuta'

export function Tierra() {
  useIdioma() // repinta el globo al cambiar de idioma
  // Herramienta activa del riel, en el almacén para que la interfaz pueda abrir el comparador
  const activa = useEstado((s) => s.herramienta)
  const setActiva = useEstado((s) => s.setHerramienta)
  const [mapa, setMapa] = useState<MapaGL | null>(null)
  const proyeccion = useEstado((s) => s.proyeccion)
  const [mesB, setMesB] = useState(120)
  const sel = useEstado((s) => s.seleccion)
  // La ruta manda al abrir y al cambiar el hash; espera al mapa para que la selección encuentre las teselas
  const { params } = useRuta()
  useEffect(() => { if (mapa) void aplicarParams(params) }, [mapa, params.unidad, params.variable, params.mes]) // eslint-disable-line react-hooks/exhaustive-deps
  return (
    <>
      <div className="centro tierra">
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
          {/* La llamada cede su sitio al panel de unidad, que ocupa la derecha */}
          {mapa && !sel && <SeleccionLote mapa={mapa} />}
          <div className="hoja hoja-tiempo"><LineaTiempo /></div>
        </main>
      </div>
    </>
  )
}
