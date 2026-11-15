// asistido por SI: Claude Code (Anthropic), escritura y revisión de código; base del prototipo migrada en el hackatón
import { useEffect, useRef } from 'react'
import * as maplibregl from 'maplibre-gl'
import type { Map as MapaGL } from 'maplibre-gl'
import { construirEstilo } from '../globo/config'
import { capaPorId } from '../datos/capas'
import { crearRecoloreo } from '../globo/recoloreo'
import { crearMotorCoropleta, SIN_DATO_REAL, type MotorCoropleta } from '../globo/coropleta'
import { registrarPatron } from '../globo/patron'
import { cargarCoropleta } from '../datos/estatico'
import type { Nivel } from '../datos/tipos'
import { useEstado } from '../app/estado'
import { etiquetaMes } from '../tiempo/valor'
import { sincronizarCamaras } from './sincronia'
import './comparar.css'
import { t } from '../textos/i18n'

// Segundo mapa solo mientras la herramienta está activa: se crea al montar y se destruye al salir.
// Mismo tamaño que el principal y recortado a la mitad derecha, así la misma cámara alinea ambos.
export function Dividida({ mapa, mesB, setMesB }: { mapa: MapaGL; mesB: number; setMesB: (m: number) => void }) {
  const caja = useRef<HTMLDivElement>(null)
  const pedir = useRef<(mes: number) => void>(() => undefined)
  const mesRef = useRef(mesB)
  mesRef.current = mesB
  const mesA = useEstado((s) => s.mes)
  const capa = useEstado((s) => s.capa)

  useEffect(() => {
    const m = new maplibregl.Map({
      container: caja.current!, style: construirEstilo(location.origin, navigator.onLine) as maplibregl.StyleSpecification,
      center: mapa.getCenter(), zoom: mapa.getZoom(), bearing: mapa.getBearing(), pitch: mapa.getPitch(),
      maxPitch: 70, minZoom: 0.8, attributionControl: false, canvasContextAttributes: { antialias: true },
    })
    ;(window as unknown as { __mapaB?: MapaGL }).__mapaB = m
    const motores: (MotorCoropleta | undefined)[] = []
    let version = 0
    const [aplicar, parar] = crearRecoloreo(m, (n, id) => motores[n] ? (motores[n]!.estado(id) ?? SIN_DATO_REAL) : undefined) // D-015: solo el nivel activo y cola en gestos
    const cargar = async (mes: number) => {
      const { filtro, capa: idCapa } = useEstado.getState(), c = capaPorId(idCapa)
      try {
        for (const n of [0, 1, 2] as Nivel[]) {
          const d = await cargarCoropleta(n, c.id, mes)
          if (mes !== mesRef.current || idCapa !== useEstado.getState().capa) return
          motores[n]?.destruir()
          const mo = crearMotorCoropleta(m, { nivel: n, rango: c.rango })
          mo.aplicar(d.valores, d.ids, filtro, d.frac, d)
          motores[n] = mo
        }
        aplicar(++version)
      } catch { useEstado.getState().setAviso(t('comparar.sinBase')) }
    }
    pedir.current = cargar
    let quitar: () => void = () => undefined
    m.on('load', () => { registrarPatron(m); m.setProjection({ type: useEstado.getState().proyeccion }); quitar = sincronizarCamaras(mapa, m); cargar(mesRef.current) })
    return () => { quitar(); parar(); motores.forEach((x) => x?.destruir()); m.remove(); delete (window as unknown as { __mapaB?: MapaGL }).__mapaB }
  }, [mapa])

  useEffect(() => { pedir.current(mesB) }, [mesB, capa])

  return (
    <>
      <div ref={caja} className="mapa-dividido" data-testid="mapa-b" />
      <div className="divisor" aria-hidden="true" />
      <span className="lado lado-a">A · {etiquetaMes(mesA)}</span>
      <span className="lado lado-b">B · {etiquetaMes(mesB)}</span>
      <div className="barra-dividida" role="group" aria-label={t('comparar.titulo')}>
        <span>A: {etiquetaMes(mesA)} {t('comparar.lineaTiempo')}</span>
        <label>B: {etiquetaMes(mesB)}
          <input type="range" min={0} max={322} value={mesB} aria-label={t('comparar.mesB')} aria-valuetext={etiquetaMes(mesB)} onChange={(e) => setMesB(Number(e.target.value))} />
        </label>
        <span>{t('comparar.nota')}</span>
      </div>
    </>
  )
}
