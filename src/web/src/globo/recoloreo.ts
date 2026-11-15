// asistido por SI: Claude Code (Anthropic), escritura y revisión de código; base del prototipo migrada en el hackatón
import type { Map as MapaGL } from 'maplibre-gl'
import { NIVELES, ESTADO_VALOR, nivelParaZoom } from './config'
import { claveUnidad, porClave } from '../datos/indice'
import type { EstadoUnidad } from './coropleta'

// Estrategia B de la PoC (PROVISIONAL, veredicto final tras la re-medición): solo los ids de
// teselas cargadas, en rebanadas por frame, y se reaplica al llegar teselas nuevas.
const RANURA = 500

export interface Seleccion {
  nivel: number
  /** null = todas las unidades cargadas; lista = solo esos países (respaldo de países sin nivel inferior) */
  paises: readonly string[] | null
}

/** Qué niveles se recolorean con el nivel activo: ese entero, y de los menores solo el respaldo. */
export function nivelesARecolorear(activo: number): Seleccion[] {
  const r: Seleccion[] = []
  for (const c of NIVELES) {
    if (c.nivel === activo) r.push({ nivel: c.nivel, paises: null })
    else if (c.nivel < activo && c.sinHijo.length) r.push({ nivel: c.nivel, paises: c.sinHijo })
  }
  return r
}

export interface Cola {
  /** Pide pintar un mes: se pinta ya, o queda pendiente si hay un gesto de cámara en curso */
  pedir: (mes: number) => void
  inicioGesto: () => void
  finGesto: () => void
  readonly enGesto: boolean
  readonly pendiente: number | null
}

/** Cola de un solo mes pendiente: durante un gesto no se pinta; al terminar se pinta el último pedido. */
export function crearCola(pintar: (mes: number) => void, alPendiente?: (hay: boolean) => void): Cola {
  let gesto = false
  let pendiente: number | null = null
  return {
    pedir(mes) {
      if (!gesto) return pintar(mes)
      pendiente = mes
      alPendiente?.(true)
    },
    inicioGesto() { gesto = true },
    finGesto() {
      gesto = false
      if (pendiente === null) return
      const m = pendiente
      pendiente = null
      pintar(m)
    },
    get enGesto() { return gesto },
    get pendiente() { return pendiente },
  }
}

/** Mantiene coloreadas las unidades cargadas con el estado vigente (`mes` es una versión: cualquier cambio de datos o filtro la incrementa). Devuelve [aplicarMes, parar]. */
export function crearRecoloreo(mapa: MapaGL, leer: (nivel: number, id: string) => EstadoUnidad | undefined, alPintando?: (pintando: boolean) => void): [(mes: number) => void, () => void] {
  let mes = 0
  let marco = 0
  const cargados = new Map<string, string[]>() // fuente -> ids cargados (se invalida con sourcedata)
  const aplicado = new Map<string, number>() // fuente|id -> mes ya escrito

  // ids cargados de una fuente; con `paises` solo los de esos países (iso3, o el propio id en adm0)
  const ids = (fuente: string, nivel: number, capa: string, paises: readonly string[] | null) => {
    const clave = `${fuente}|${paises ? 'respaldo' : 'todo'}`
    let l = cargados.get(clave)
    if (!l) {
      const s = new Set<string>()
      // querySourceFeatures().state no refleja feature-state en MapLibre 6.16: aquí solo se leen ids
      for (const f of mapa.querySourceFeatures(fuente, { sourceLayer: capa })) {
        const id = f.properties?.unidad_id
        if (typeof id !== 'string' || !porClave.has(claveUnidad(nivel, id))) continue
        if (paises && !paises.includes(String(f.properties?.iso3 ?? id))) continue
        s.add(id)
      }
      cargados.set(clave, (l = [...s]))
    }
    return l
  }

  const paso = () => {
    marco = 0
    let n = 0
    for (const { nivel, paises } of nivelesARecolorear(nivelParaZoom(mapa.getZoom()))) {
      const c = NIVELES[nivel]
      for (const id of ids(c.fuente, c.nivel, c.capaFuente, paises)) {
        const k = `${c.fuente}|${id}`
        if (aplicado.get(k) === mes) continue
        const e = leer(c.nivel, id)
        if (!e) continue // aún sin datos de este nivel: se reintenta al llegar
        mapa.setFeatureState({ source: c.fuente, sourceLayer: c.capaFuente, id }, { [ESTADO_VALOR]: e.v, ok: e.ok, hueco: e.hueco })
        aplicado.set(k, mes)
        if (++n >= RANURA) return void (marco = requestAnimationFrame(paso))
      }
    }
    alPintando?.(false) // todo lo cargado ya lleva el mes vigente
  }
  const arrancar = () => { if (!marco && !cola.enGesto) { alPintando?.(true); marco = requestAnimationFrame(paso) } }
  // Durante un gesto de cámara (movestart a moveend) no se llama a setFeatureState
  const cola = crearCola((m) => { mes = m; arrancar() }, alPintando)
  const alInicio = () => cola.inicioGesto()
  const alFin = () => { cola.finGesto(); arrancar() } // también cubre teselas llegadas durante el gesto

  const alTesela = (e: { sourceId?: string; tile?: unknown }) => {
    if (!e.tile || !e.sourceId) return
    cargados.delete(`${e.sourceId}|todo`) // llegaron teselas: reaplicar el mes vigente
    cargados.delete(`${e.sourceId}|respaldo`)
    arrancar()
  }
  mapa.on('sourcedata', alTesela)
  mapa.on('movestart', alInicio)
  mapa.on('moveend', alFin) // cambio de nivel incluido: el nivel nuevo recibe el mes vigente una vez
  return [cola.pedir, () => { mapa.off('sourcedata', alTesela); mapa.off('movestart', alInicio); mapa.off('moveend', alFin); cancelAnimationFrame(marco) }]
}
