// asistido por SI: Claude Code (Anthropic), escritura y revisión de código; base del prototipo migrada en el hackatón
import { useEffect } from 'react'
import { Tierra } from '../secciones/tierra/Tierra'
import { Portada } from '../secciones/portada/Portada'
import { Gemelo } from '../secciones/gemelo/Gemelo'
import { Rotaciones } from '../secciones/rotaciones/Rotaciones'
import { Ciencia } from '../secciones/ciencia/Ciencia'
import { DatosAbiertosSeccion } from '../secciones/datos-abiertos/DatosAbiertos'
import { Fuentes } from '../secciones/fuentes/Fuentes'
import { Cabecera } from './Cabecera'
import { Recorrido } from './recorrido/Recorrido'
import { cargarEjemplos } from './ejemplos'
import { useRuta, type Seccion } from './ruta'
import { t, useIdioma } from '../textos/i18n'

// Fuera de #/tierra el globo se desmonta; el estado de Daniel vive en su almacén y sobrevive
const SECCION: Record<Seccion, () => React.JSX.Element> = {
  portada: Portada, tierra: Tierra, gemelo: Gemelo, rotaciones: Rotaciones, ciencia: Ciencia, datos: DatosAbiertosSeccion, fuentes: Fuentes,
}

export function App() {
  const idioma = useIdioma()
  const { seccion } = useRuta()
  useEffect(() => { void cargarEjemplos() }, [])
  // El lector de pantalla elige la voz por el idioma del documento
  useEffect(() => { document.documentElement.lang = idioma }, [idioma])
  const Actual = SECCION[seccion]
  return (
    <div className="app">
      <Cabecera />
      <Actual />
      <footer className="pie">{t('aviso.apoyo')}</footer>
      <Recorrido />
    </div>
  )
}
