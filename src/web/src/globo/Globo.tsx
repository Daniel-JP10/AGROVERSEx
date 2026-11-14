// asistido por SI: Claude Code (Anthropic), escritura y revisión de código; base del prototipo migrada en el hackatón
import { useEffect, useRef, useState } from 'react'
import * as maplibregl from 'maplibre-gl'
import type { Map as MapaGL } from 'maplibre-gl'
import workerUrl from 'maplibre-gl/dist/maplibre-gl-worker.mjs?url'
import { Protocol } from 'pmtiles'
import 'maplibre-gl/dist/maplibre-gl.css'
import { NIVELES, construirEstilo, nivelParaZoom, capasInteractivas, OPACIDAD, opacidadRelleno, ATRIBUCION, avisoDisputa } from './config'
import { crearRecoloreo } from './recoloreo'
import { iniciarEstrellas } from './estrellas'
import { iniciarHalo } from './atmosfera'
import { avisoSinRed } from './fondos'
import './globo.css'
import { cargarIndice, claveUnidad, porClave, type Unidad } from '../datos/indice'
import { useEstado } from '../app/estado'
import { crearMotorCoropleta, SIN_DATO, textoValor, type MotorCoropleta } from './coropleta'
import { Leyenda } from './leyenda'
import { registrarPatron } from './patron'
import { clienteDefecto } from '../datos/consultas'
import { capaPorId, valoresCapa } from '../datos/capas'
import type { Nivel } from '../datos/tipos'
import { Controles } from './Controles'
import { t } from '../textos/i18n'

// MapLibre 6 trae el worker como módulo aparte; Vite debe darle su URL
maplibregl.setWorkerUrl(workerUrl)
let protocoloRegistrado = false
const ref = (nivel: number, id: number | string) => {
  const c = NIVELES[nivel]
  return { source: c.fuente, sourceLayer: c.capaFuente, id }
}

// Trama de rayas para las zonas en disputa (nivel 9 dentro de adm0)
function trama(): ImageData {
  const c = document.createElement('canvas')
  c.width = c.height = 12
  const g = c.getContext('2d')!
  g.fillStyle = '#1b2433'; g.fillRect(0, 0, 12, 12)
  g.strokeStyle = '#e8d9a8'; g.lineWidth = 2
  g.beginPath(); g.moveTo(-2, 14); g.lineTo(14, -2); g.stroke()
  return g.getImageData(0, 0, 12, 12)
}

export function Globo({ onMapa }: { onMapa?: (m: MapaGL) => void }) {
  const contenedor = useRef<HTMLDivElement>(null)
  const lienzo = useRef<HTMLCanvasElement>(null)
  const aviso = useEstado((e) => e.aviso)
  const centro = useRef<HTMLDivElement>(null)
  const tip = useRef<HTMLDivElement>(null)
  const halo = useRef<HTMLCanvasElement>(null)
  const [sinRed, setSinRed] = useState(!navigator.onLine)
  const [mapa, setMapa] = useState<MapaGL | null>(null)
  const [coords, setCoords] = useState<[number, number] | null>(null)

  useEffect(() => {
    if (!protocoloRegistrado) {
      maplibregl.addProtocol('pmtiles', new Protocol().tile)
      protocoloRegistrado = true
    }
    const m = new maplibregl.Map({
      container: contenedor.current!,
      style: construirEstilo(location.origin, navigator.onLine) as maplibregl.StyleSpecification,
      center: [-60, 10], zoom: 1.6, maxPitch: 70, minZoom: 0.8,
      attributionControl: { compact: true, customAttribution: ATRIBUCION },
      canvasContextAttributes: { antialias: true },
    })
    ;(window as unknown as { __mapa: MapaGL }).__mapa = m
    m.on('styleimagemissing', (e) => { if (e.id === 'trama' && !m.hasImage('trama')) m.addImage('trama', trama()) })
    const motores: (MotorCoropleta | undefined)[] = []
    let version = 0
    const [aplicarVersion, pararColor] = crearRecoloreo(m, (n, id) => (motores[n] ? (motores[n]!.estado(id) ?? SIN_DATO) : undefined), (p) => useEstado.getState().setPintando(p))
    const aplicarMes = (_mes: number) => cargarDatos()
    // Datos reales: /api/coropleta por nivel para la capa activa; sin dato = hueco
    const cargarDatos = async () => {
      const { mes, filtro, capa: idCapa } = useEstado.getState()
      const c = capaPorId(idCapa)
      try {
        for (const n of [0, 1, 2] as Nivel[]) {
          const [ids, d, f] = await Promise.all([clienteDefecto.orden(n), clienteDefecto.coropleta(n, c.id, mes), c.fraccion ? clienteDefecto.coropleta(n, c.fraccion, mes) : undefined])
          if (mes !== useEstado.getState().mes || idCapa !== useEstado.getState().capa) return // llegó tarde: ya se pidió otro mes o capa
          motores[n]?.destruir()
          const mo = crearMotorCoropleta(m, { nivel: n, rango: c.rango })
          mo.aplicar(valoresCapa(c, d.valores, mes, c.unidadProducto ?? ''), ids, filtro, f?.valores)
          motores[n] = mo
        }
        aplicarVersion(++version)
      } catch { useEstado.getState().setAviso(t('globo.sinBaseCoropleta')) }
    }
    m.on('style.load', () => { registrarPatron(m); if (!m.hasImage('trama')) m.addImage('trama', trama()) })
    const texto = (e: Parameters<typeof textoValor>[0]) => { const c = capaPorId(useEstado.getState().capa); return textoValor(e, c.unidad, c.rango) }
    const etiqueta = () => {
      if (!centro.current) return
      const nivel = nivelParaZoom(m.getZoom())
      const c = m.getContainer()
      const f = m.queryRenderedFeatures([c.clientWidth / 2, c.clientHeight / 2], { layers: capasInteractivas(nivel) })[0]
      if (!f || m.getZoom() < 6) { centro.current.style.display = 'none'; return }
      const nf = Number(f.properties.nivel), id = String(f.properties.id)
      const t = texto(motores[nf]?.estado(id))
      centro.current.style.display = 'block'
      centro.current.textContent = `${f.properties.nombre ?? id}: ${t}`
    }
    m.on('idle', etiqueta) // tras mover y tras cargar teselas/valores
    const parar = iniciarEstrellas(lienzo.current!, m)
    const pararHalo = iniciarHalo(halo.current!, m)
    // Si fallan las teselas del fondo de detalle, queda Blue Marble y se avisa
    // Teselas de límites o API caídas: aviso visible, los contornos siguen donde haya teselas
    m.on('error', (e) => { const sid = (e as { sourceId?: string }).sourceId; if (sid && /^admd$/.test(sid)) useEstado.getState().setAviso(t('globo.sinLimites')) })
    m.on('error', (e) => { if ((e as { sourceId?: string }).sourceId === 'detalle') setSinRed(true) })
    let hover: { nivel: number; id: number | string } | null = null
    let sel: { nivel: number; id: number | string } | null = null
    let marco = 0
    let ultimo: maplibregl.MapMouseEvent | null = null

    const quitarHover = () => {
      if (hover) m.setFeatureState(ref(hover.nivel, hover.id), { hover: false })
      hover = null
      if (tip.current) tip.current.style.display = 'none'
    }
    const procesar = () => {
      marco = 0
      const e = ultimo
      if (!e) return
      const nivel = nivelParaZoom(m.getZoom())
      const f = m.queryRenderedFeatures(e.point, { layers: capasInteractivas(nivel) })[0]
      const id = f?.properties?.id as string | undefined
      if (id === undefined) return quitarHover()
      const nivelF = Number(f.properties.nivel) // un respaldo puede ser de un nivel menor al activo
      if (!hover || hover.id !== id || hover.nivel !== nivelF) {
        quitarHover()
        hover = { nivel: nivelF, id }
        m.setFeatureState(ref(nivelF, id), { hover: true })
      }
      const u = porClave.get(claveUnidad(nivelF, id))
      const est = motores[nivelF]?.estado(String(id))
      const t = tip.current!
      t.style.display = 'block'
      t.style.transform = `translate(${e.point.x + 14}px, ${e.point.y + 14}px)`
      const nombre = document.createElement('b')
      nombre.textContent = String(f.properties?.nombre ?? u?.nombre ?? id)
      const linea = (txt: string) => { const d = document.createElement('div'); d.textContent = txt; return d }
      t.replaceChildren(nombre, ...(u?.pais ? [linea(u.pais)] : []),
        linea(texto(est)))
    }
    m.on('mousemove', (e) => {
      setCoords([e.lngLat.lng, e.lngLat.lat])
      ultimo = e
      if (!marco) marco = requestAnimationFrame(procesar)
    })
    m.getCanvas().addEventListener('mouseleave', quitarHover)
    m.on('click', (e) => {
      const nivel = nivelParaZoom(m.getZoom())
      const f = m.queryRenderedFeatures(e.point, { layers: capasInteractivas(nivel) })[0]
      const id = f?.properties?.id
      if (id !== undefined) useEstado.getState().seleccionarPorId(Number(f.properties.nivel), id)
    })

    // Vuelo: bbox de /api/unidad/:id; si cruza el antimeridiano o no hay base, punto interior o aviso
    const volar = async (u: Unidad) => {
      const ZOOM = [3.5, 5.5, 7.5]
      try {
        const r = await fetch(`/api/unidad/${encodeURIComponent(String(u.id))}`)
        if (!r.ok) throw new Error(String(r.status))
        const d = (await r.json()).unidad
        if (useEstado.getState().seleccion !== u) return // el usuario ya eligió otra
        if (d.bbox_oeste <= -179.9 && d.bbox_este >= 179.9) // cruza el antimeridiano: fitBounds daría todo el mundo
          return void m.flyTo({ center: [d.punto_lon, d.punto_lat], zoom: ZOOM[u.nivel] ?? 4, duration: 1800, essential: true })
        m.fitBounds([[d.bbox_oeste, d.bbox_sur], [d.bbox_este, d.bbox_norte]], { padding: { top: 80, bottom: 120, left: 120, right: 380 }, duration: 1800, maxZoom: 9, essential: true })
      } catch {
        useEstado.getState().setAviso(t('globo.sinBaseCentrar'))
      }
    }
    // Selección: resalta y vuela al bbox (vale igual para clic y búsqueda)
    const dejarSel = useEstado.subscribe((s, previo) => {
      if (s.seleccion === previo.seleccion) return
      if (sel) m.setFeatureState(ref(sel.nivel, sel.id), { sel: false })
      const u: Unidad | null = s.seleccion
      sel = u ? { nivel: u.nivel, id: u.id } : null
      if (!u) return
      m.setFeatureState(ref(u.nivel, u.id), { sel: true })
      volar(u)
    })
    // Cambio de proyección y de mes
    const dejarOtros = useEstado.subscribe((s, previo) => {
      if (s.proyeccion !== previo.proyeccion) {
        m.setProjection({ type: s.proyeccion })
        const v = s.proyeccion === 'globe' ? 'visible' : 'hidden'
        if (lienzo.current) lienzo.current.style.visibility = v
        if (halo.current) halo.current.style.visibility = v
      }
      if (s.mes !== previo.mes) aplicarMes(s.mes)
      if (s.filtro !== previo.filtro || s.capa !== previo.capa) cargarDatos()
      if (s.opacidad !== previo.opacidad) for (const c of NIVELES) {
        m.setPaintProperty(`${c.fuente}-relleno`, 'fill-opacity', opacidadRelleno(c, s.opacidad) as never)
        if (c.sinHijo.length) m.setPaintProperty(`${c.fuente}-respaldo`, 'fill-opacity', opacidadRelleno(c, s.opacidad, true) as never)
      }
    })

    m.on('load', async () => {
      await cargarIndice()
      const o = useEstado.getState().opacidad
      if (o !== OPACIDAD) for (const c of NIVELES) { m.setPaintProperty(`${c.fuente}-relleno`, 'fill-opacity', opacidadRelleno(c, o) as never); if (c.sinHijo.length) m.setPaintProperty(`${c.fuente}-respaldo`, 'fill-opacity', opacidadRelleno(c, o, true) as never) }
      cargarDatos() // mes inicial al cargar
      setMapa(m)
      onMapa?.(m)
    })
    return () => { parar(); pararHalo(); pararColor(); dejarSel(); dejarOtros(); cancelAnimationFrame(marco); m.remove() }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  return (
    <div className="globo">
      <canvas ref={lienzo} className="estrellas" aria-hidden="true" />
      <canvas ref={halo} className="halo" aria-hidden="true" />
      <div ref={contenedor} className="mapa" />
      {aviso && <div className="aviso-red" style={{ top: 40 }} role="alert">{aviso}</div>}
      {sinRed && <div className="aviso-red" role="status">{avisoSinRed()}</div>}
      <div ref={centro} className="etiqueta-centro" style={{ display: 'none' }} role="status" aria-live="polite" />
      <Leyenda />
      <div ref={tip} className="tooltip" style={{ display: 'none' }} role="tooltip" />
      <div className="aviso-disputa">{avisoDisputa()}</div>
      {mapa && <Controles mapa={mapa} coords={coords} />}
    </div>
  )
}
