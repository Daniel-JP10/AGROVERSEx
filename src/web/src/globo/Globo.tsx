// asistido por SI: Claude Code (Anthropic), escritura y revisión de código; base del prototipo migrada en el hackatón; fase 3 sin coordenadas en vivo; series del mundo y ponderación (S1w)
import { useEffect, useRef, useState } from 'react'
import * as maplibregl from 'maplibre-gl'
import type { Map as MapaGL } from 'maplibre-gl'
import workerUrl from 'maplibre-gl/dist/maplibre-gl-worker.mjs?url'
import { Protocol } from 'pmtiles'
import 'maplibre-gl/dist/maplibre-gl.css'
import { NIVELES, construirEstilo, nivelParaZoom, capasInteractivas, OPACIDAD, opacidadRelleno, ATRIBUCION, avisoDisputa, esDisputa, nombreUnidad } from './config'
import { crearRecoloreo } from './recoloreo'
import { iniciarEstrellas } from './estrellas'
import { iniciarHalo } from './atmosfera'
import { avisoSinRed } from './fondos'
import './globo.css'
import { cargarIndice, claveUnidad, porClave, type Unidad } from '../datos/indice'
import { useEstado } from '../app/estado'
import { crearMotorCoropleta, SIN_CULTIVO, SIN_DATO_REAL, textoValor, type MotorCoropleta } from './coropleta'
import { Leyenda } from './leyenda'
import { registrarPatron } from './patron'
import { cargarCoropleta, cargarGeo, cargarMeta, hayMundo, iso3DeUnidad, metaActual, textoEstado, usePonderacion, type ProductoMes } from '../datos/estatico'
import { capaPorId } from '../datos/capas'
import { MARCA_RELLENO, trasPrimerRelleno } from '../datos/primerRelleno'
import type { Nivel } from '../datos/tipos'
import { Controles } from './Controles'
import { idioma, t } from '../textos/i18n'

// MapLibre 6 trae el worker como módulo aparte; Vite debe darle su URL
maplibregl.setWorkerUrl(workerUrl)
let protocoloRegistrado = false
const ref = (nivel: number, id: number | string) => {
  const c = NIVELES[nivel]
  return { source: c.fuente, sourceLayer: c.capaFuente, id }
}

// Trama de rayas para las zonas en disputa (es_disputa = 1)
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
    // Atribución cerrada al cargar (botón i); el texto completo va en el pie del marco
    // idle: MapLibre abre la atribución al llegar sus datos, que en WebKit llegan después de load
    m.once('idle', () => contenedor.current?.querySelector('.maplibregl-ctrl-attrib')?.classList.remove('maplibregl-compact-show'))
    m.on('styleimagemissing', (e) => { if (e.id === 'trama' && !m.hasImage('trama')) m.addImage('trama', trama()) })
    const motores: (MotorCoropleta | undefined)[] = []
    let version = 0
    const [aplicarVersion, pararColor] = crearRecoloreo(m, (n, id) => (motores[n] ? (motores[n]!.estado(id) ?? SIN_DATO_REAL) : undefined), (p) => useEstado.getState().setPintando(p))
    // Hay relleno cuando alguna unidad del nivel país ya lleva valor en su estado (no basta con que la cola quede vacía)
    const hayRelleno = () => {
      const c = NIVELES[0]
      return m.querySourceFeatures(c.fuente, { sourceLayer: c.capaFuente }).some((f) => f.id !== undefined && m.getFeatureState({ source: c.fuente, sourceLayer: c.capaFuente, id: f.id }).ok === true)
    }
    // Primer relleno pintado: cuadro tras el que ya hay valor en el estado; lo mide la prueba de presupuesto (≤ 6 s con red lenta, plan v1 §a)
    const medirRelleno = () => { if (version > 0 && hayRelleno()) { performance.mark(MARCA_RELLENO); m.off('render', medirRelleno) } }
    m.on('render', medirRelleno)
    const aplicarMes = (_mes: number) => cargarDatos()
    // Datos reales de archivos estáticos (datos/estatico.ts): una unidad con valor nulo = hueco; una unidad fuera de Colombia no se pinta
    let producto: ProductoMes | null = null
    // adm2 del mundo: solo los países con teselas adm2 cargadas (cada país pesa unos MB)
    let paises2: string[] = []
    const paisesAdm2 = () => {
      const lista = metaActual().paises_adm2 ?? []
      const s = new Set<string>()
      for (const f of m.querySourceFeatures(NIVELES[2].fuente, { sourceLayer: NIVELES[2].capaFuente })) {
        const p = iso3DeUnidad(String(f.properties?.unidad_id ?? ''))
        if (lista.includes(p)) s.add(p)
      }
      return [...s].sort()
    }
    const cargarDatos = async (soloNivel2 = false) => {
      await cargarMeta().catch(() => undefined)
      const { mes, filtro, capa: idCapa } = useEstado.getState()
      const pond = usePonderacion.getState().ponderacion
      const c = capaPorId(idCapa)
      try {
        for (const n of (soloNivel2 ? [2] : [0, 1, 2]) as Nivel[]) {
          // Primera carga: los niveles finos (unos MB) esperan al primer relleno para no quitarle red al país y a sus teselas
          if (n > 0) await trasPrimerRelleno()
          if (n === 2) paises2 = paisesAdm2()
          const d = await cargarCoropleta(n, c.id, mes, paises2)
          if (mes !== useEstado.getState().mes || idCapa !== useEstado.getState().capa || pond !== usePonderacion.getState().ponderacion) return // llegó tarde
          motores[n]?.destruir()
          const base = crearMotorCoropleta(m, { nivel: n, rango: c.rango })
          base.aplicar(d.valores, d.ids, filtro, d.frac, d)
          // Sin cultivo (ponderación de cultivo): ni color ni trama, y el texto lo dice; nunca 0
          const mo: MotorCoropleta = d.sinCultivo.size ? { ...base, estado: (id) => (d.sinCultivo.has(id) ? SIN_CULTIVO : base.estado(id)) } : base
          motores[n] = mo
          producto = d.producto
          aplicarVersion(++version) // cada nivel se pinta al llegar: el país (unos KB) no espera al nivel 2 (unos MB)
        }
      } catch { useEstado.getState().setAviso(t('globo.sinBaseCoropleta')) }
    }
    // El relleno arranca con el estilo: no espera al índice ni a 'load', que aguarda también las teselas del fondo GIBS
    let arrancado = false
    m.on('style.load', () => { registrarPatron(m); if (!m.hasImage('trama')) m.addImage('trama', trama()); if (!arrancado) { arrancado = true; cargarDatos() } })
    const texto = (e: Parameters<typeof textoValor>[0]) => { const c = capaPorId(useEstado.getState().capa); return textoValor(e, c.unidad, c.rango) }
    const etiqueta = () => {
      if (!centro.current) return
      const nivel = nivelParaZoom(m.getZoom())
      const c = m.getContainer()
      const f = m.queryRenderedFeatures([c.clientWidth / 2, c.clientHeight / 2], { layers: capasInteractivas(nivel) })[0]
      if (!f || m.getZoom() < 6) { centro.current.style.display = 'none'; return }
      const nf = Number(f.properties.nivel), id = String(f.properties.unidad_id)
      const t = texto(motores[nf]?.estado(id))
      centro.current.style.display = 'block'
      centro.current.textContent = `${nombreUnidad(String(f.properties.nombre ?? id), esDisputa(f.properties))}: ${t}`
    }
    m.on('idle', etiqueta) // tras mover y tras cargar teselas/valores
    // Al acercarse a otro país, su adm2 se carga
    m.on('moveend', () => { if (hayMundo() && nivelParaZoom(m.getZoom()) >= 1 && paisesAdm2().join() !== paises2.join()) void cargarDatos(true) })
    const dejarPond = usePonderacion.subscribe(() => { void cargarDatos() })
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
      const id = f?.properties?.unidad_id as string | undefined
      if (id === undefined) return quitarHover()
      const nivelF = Number(f.properties.nivel) // un respaldo puede ser de un nivel menor al activo
      if (!hover || hover.id !== id || hover.nivel !== nivelF) {
        quitarHover()
        hover = { nivel: nivelF, id }
        m.setFeatureState(ref(nivelF, id), { hover: true })
      }
      const u = porClave.get(claveUnidad(nivelF, id))
      const est = motores[nivelF]?.estado(String(id))
      const caja = tip.current!
      caja.style.display = 'block'
      caja.style.transform = `translate(${e.point.x + 14}px, ${e.point.y + 14}px)`
      const nombre = document.createElement('b')
      const disp = esDisputa(f.properties) || !!u?.disputa
      nombre.textContent = nombreUnidad(String(f.properties?.nombre ?? u?.nombre ?? id), disp)
      const linea = (txt: string) => { const d = document.createElement('div'); d.textContent = txt; return d }
      caja.replaceChildren(nombre, ...(u?.pais && !disp ? [linea(u.pais)] : []),
        linea(texto(est)),
        ...(est && !est.hueco && !est.sinCultivo && producto ? [linea(`${t('globo.fraccionValida')} ${(est.frac ?? NaN).toLocaleString(idioma(), { maximumFractionDigits: 2 })} · ${producto.producto} ${producto.version} · ${textoEstado(producto.estado, useEstado.getState().capa, useEstado.getState().mes)}`)] : []))
    }
    m.on('mousemove', (e) => {
      ultimo = e
      if (!marco) marco = requestAnimationFrame(procesar)
    })
    m.getCanvas().addEventListener('mouseleave', quitarHover)
    m.on('click', (e) => {
      const nivel = nivelParaZoom(m.getZoom())
      const f = m.queryRenderedFeatures(e.point, { layers: capasInteractivas(nivel) })[0]
      const id = f?.properties?.unidad_id
      if (id !== undefined) useEstado.getState().seleccionarPorId(Number(f.properties.nivel), id)
    })

    // Vuelo: bbox de unidades_geo (archivo estático); si cruza el antimeridiano, punto interior; sin bbox, aviso
    const volar = async (u: Unidad) => {
      const ZOOM = [3.5, 5.5, 7.5]
      try {
        const g = (await cargarGeo())[String(u.id)]
        if (!g) throw new Error('sin bbox')
        if (useEstado.getState().seleccion !== u) return // el usuario ya eligió otra
        if (g[0] <= -179.9 && g[2] >= 179.9 && g[5] !== undefined) // cruza el antimeridiano: fitBounds daría todo el mundo
          return void m.flyTo({ center: [g[5], g[6]!], zoom: ZOOM[u.nivel] ?? 4, duration: 1800, essential: true })
        m.fitBounds([[g[0], g[1]], [g[2], g[3]]], { padding: { top: 80, bottom: 120, left: 120, right: 380 }, duration: 1800, maxZoom: 9, essential: true })
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
      setMapa(m)
      onMapa?.(m)
    })
    return () => { parar(); pararHalo(); pararColor(); dejarSel(); dejarPond(); dejarOtros(); cancelAnimationFrame(marco); m.remove() }
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
      {mapa && <Controles mapa={mapa} />}
    </div>
  )
}
