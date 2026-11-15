// asistido por SI: Claude Code (Anthropic), escritura y revisión de código; marco común y carga diferida de secciones (fase 3)
import { lazy, Suspense, useEffect, type ComponentType } from 'react'
import { Portada } from '../secciones/portada/Portada'
import { CabeceraHoja } from './marco/CabeceraHoja'
import { Decoracion } from './marco/Decoracion'
import { Pie } from './marco/Pie'
import { CargandoSeccion, MarcadorLote } from './marco/Marcador'
import { Recorrido } from './recorrido/Recorrido'
import { cargarEjemplos } from './ejemplos'
import { aHash, esRedireccion, useRuta, type Seccion } from './ruta'
import { useIdioma } from '../textos/i18n'
import './marco/marco.css'

// Import dinámico: MapLibre y las secciones pesadas no se bajan en #/ (presupuesto de 600 KB)
const Tierra = lazy(() => import('../secciones/tierra/Tierra').then((m) => ({ default: m.Tierra })))
const Rotaciones = lazy(() => import('../secciones/rotaciones/Rotaciones').then((m) => ({ default: m.Rotaciones })))
const Ciencia = lazy(() => import('../secciones/ciencia/Ciencia').then((m) => ({ default: m.Ciencia })))
const Datos = lazy(() => import('../secciones/datos-abiertos/DatosAbiertos').then((m) => ({ default: m.DatosAbiertosSeccion })))
const Fuentes = lazy(() => import('../secciones/fuentes/Fuentes').then((m) => ({ default: m.Fuentes })))
// #/lote es de W3 (secciones/lote/index.tsx, export default); mientras no exista va el marcador
const LOTE = import.meta.glob<{ default: ComponentType }>('../secciones/lote/index.tsx')
const cargarLote = LOTE['../secciones/lote/index.tsx']
const Lote: ComponentType = cargarLote ? lazy(cargarLote) : MarcadorLote

const SECCION: Record<Seccion, ComponentType> = {
  portada: Portada, tierra: Tierra, lote: Lote, rotaciones: Rotaciones, ciencia: Ciencia, datos: Datos, fuentes: Fuentes,
}

export function App() {
  const idioma = useIdioma()
  const ruta = useRuta()
  useEffect(() => { void cargarEjemplos() }, [])
  // El lector de pantalla elige la voz por el idioma del documento
  useEffect(() => { document.documentElement.lang = idioma }, [idioma])
  // #/gemelo se reescribe a #/lote sin dejar la ruta vieja en el historial
  useEffect(() => { if (esRedireccion(window.location.hash)) window.location.replace(aHash(ruta)) }, [ruta])
  const Actual = SECCION[ruta.seccion]
  return (
    <div className={`app seccion-${ruta.seccion}`}>
      <Decoracion />
      <CabeceraHoja />
      <Suspense fallback={<CargandoSeccion />}><Actual /></Suspense>
      <Pie />
      <Recorrido />
    </div>
  )
}
