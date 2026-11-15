// asistido por SI: Claude Code (Anthropic), panel del recorrido guiado: texto del paso, siguiente, anterior y salir
import { useEffect, useRef, type Ref } from 'react'
import { dato, fijarHuecos, useHuecos, type Resolver } from '../../textos/huecos'
import { t, useIdioma } from '../../textos/i18n'
import { cargarHuecos } from './cargarHuecos'
import { Relleno } from '../Relleno'
import { ejecutar } from './acciones'
import { useRecorrido } from './estado'
import { PASOS, type Paso } from './pasos'
import './recorrido.css'

/** Texto del paso con sus huecos; si falta algún dato del paso, dice aviso.sin_dato. */
export function TextoPaso({ paso, resolver = dato }: { paso: Paso; resolver?: Resolver }) {
  const falta = paso.datos.some((n) => resolver(n) === undefined)
  return (
    <div className="paso-texto" data-testid="paso-texto">
      <p><Relleno texto={t(paso.texto)} resolver={resolver} /></p>
      {falta && <p className="sin-dato">{t('aviso.sin_dato')}</p>}
    </div>
  )
}

interface PanelProps { indice: number; anterior: () => void; siguiente: () => void; salir: () => void; refSiguiente?: Ref<HTMLButtonElement> }

// Presentación sin estado propio: el panel solo sabe qué paso pintar y a quién avisar
export function PanelRecorrido({ indice, anterior, siguiente, salir, refSiguiente }: PanelProps) {
  const paso = PASOS[indice]
  const ultimo = indice === PASOS.length - 1
  return (
    <section className="recorrido" aria-label={t('recorrido.etiqueta')} onKeyDown={(e) => e.key === 'Escape' && salir()}>
      <div aria-live="polite" aria-atomic="true">
        <TextoPaso paso={paso} />
      </div>
      <div className="recorrido-pie">
        <span className="recorrido-progreso">{t('recorrido.progreso').replace('{n}', String(indice + 1)).replace('{total}', String(PASOS.length))}</span>
        <button type="button" aria-disabled={indice === 0} onClick={anterior}>{t('recorrido.anterior')}</button>
        <button type="button" ref={refSiguiente} onClick={ultimo ? salir : siguiente}>{ultimo ? t('recorrido.terminar') : t('recorrido.siguiente')}</button>
        <button type="button" onClick={salir}>{t('recorrido.salir')}</button>
      </div>
    </section>
  )
}

export function Recorrido() {
  const idioma = useIdioma()
  useHuecos((s) => s.valores)
  const { activo, indice, siguiente, anterior, salir } = useRecorrido()
  // Los datos del guion se leen al abrir el recorrido y otra vez si cambia el idioma (formato de números)
  useEffect(() => { if (activo) void cargarHuecos(idioma).then(fijarHuecos) }, [activo, idioma])
  const botonSiguiente = useRef<HTMLButtonElement>(null)
  const abridor = useRef<Element | null>(null)

  // Al abrir, el foco pasa a Siguiente; al cerrar, vuelve al botón que lo abrió si sigue en pantalla
  useEffect(() => {
    if (activo) { abridor.current = document.activeElement; botonSiguiente.current?.focus(); return }
    const o = abridor.current
    abridor.current = null
    if (o instanceof HTMLElement && o.isConnected) o.focus()
  }, [activo])

  // shortcut: el estado del globo no se restaura al salir; subir si Daniel expone un restablecer
  useEffect(() => { if (activo) ejecutar(PASOS[indice]) }, [activo, indice])

  return activo ? <PanelRecorrido indice={indice} anterior={anterior} siguiente={siguiente} salir={salir} refSiguiente={botonSiguiente} /> : null
}
