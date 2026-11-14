// asistido por SI: Claude Code (Anthropic), escritura y revisión de código; base del prototipo migrada en el hackatón
import { capaPorId } from '../../datos/capas'
import { useEffect, useMemo, useState } from 'react'
import { useEstado } from '../../app/estado'
import { ocultasPorFiltros, UMBRAL_RONI, type AtributosUnidad, type FiltrosGlobales } from '../../datos/filtrar'
import { filtrosRegionalesPara } from './filtros_regionales'

interface Atributos { zona_demo: boolean; unidades: AtributosUnidad[] }
const NIVELES = [0, 1, 2]

// Opciones salen de los datos cargados, no de listas escritas a mano.
const distintos = <T,>(us: AtributosUnidad[], k: keyof AtributosUnidad) =>
  [...new Set(us.map((u) => u[k] as T).filter((v) => v !== undefined && v !== null))].sort() as T[]

function Grupo<T extends string | number>({ nombre, opciones, sel, alCambiar }: { nombre: string; opciones: T[]; sel?: T[]; alCambiar: (v: T[] | undefined) => void }) {
  if (!opciones.length) return null
  const alt = (o: T) => { const s = new Set(sel ?? []); s.has(o) ? s.delete(o) : s.add(o); alCambiar(s.size ? [...s] : undefined) }
  return (
    <fieldset><legend>{nombre}</legend>
      {opciones.map((o) => <label key={o}><input type="checkbox" checked={sel?.includes(o) ?? false} onChange={() => alt(o)} /> {String(o)}</label>)}
    </fieldset>
  )
}

export function Filtros() {
  const unidadCapa = capaPorId(useEstado((s) => s.capa)).unidad
  const filtro = useEstado((s) => s.filtro)
  const setFiltro = useEstado((s) => s.setFiltro)
  const mes = useEstado((s) => s.mes)
  const seleccion = useEstado((s) => s.seleccion)
  const [attrs, setAttrs] = useState<Atributos | null>(null)
  const [globales, setGlobales] = useState<FiltrosGlobales>({})
  const [error, setError] = useState(false)
  const [roni, setRoni] = useState<number[]>([])
  const num = (v: string) => (v === '' ? undefined : Number(v))

  useEffect(() => {
    Promise.all(NIVELES.map((n) => fetch(`/api/atributos?nivel=${n}`).then((r) => (r.ok ? r.json() : Promise.reject(r.status)))))
      .then((rs) => setAttrs({ zona_demo: rs.some((r) => r.zona_demo), unidades: rs.flatMap((r) => r.unidades) }))
      .catch(() => setError(true))
    fetch('/api/enso').then((r) => r.json()).then((f: { mes_id: number; roni: number }[]) => { const a: number[] = []; f.forEach((x) => { a[x.mes_id] = x.roni }); setRoni(a) }).catch(() => undefined)
  }, [])

  // Se recalcula al cambiar el mes: el filtro ENSO depende del mes en curso.
  useEffect(() => {
    const act = !!(globales.koppen || globales.igbp || globales.clase || globales.zona || globales.soloEventos || globales.enso)
    const f = useEstado.getState().filtro
    setFiltro({ ...f, ocultas: act && attrs ? ocultasPorFiltros(attrs.unidades, globales, mes, { roni, umbral: UMBRAL_RONI }) : undefined })
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [globales, mes, attrs, roni])

  const cambiar = (g: FiltrosGlobales) => {
    setGlobales(g) // el efecto de arriba pasa los ids ocultos al motor; fraccion y rango siguen en los campos de abajo
  }
  const us = attrs?.unidades ?? []
  const propia = useMemo(() => us.find((u) => seleccion && u.id === String(seleccion.id)), [us, seleccion])
  const regionales = propia ? filtrosRegionalesPara(propia) : []

  return (
    <aside className="panel panel-herr" aria-label="Filtros">
      <h2>Filtros</h2>
      <label>Mínimo ({unidadCapa})<input type="number" value={filtro.min ?? ''} onChange={(e) => setFiltro({ ...filtro, min: num(e.target.value) })} /></label>
      <label>Máximo ({unidadCapa})<input type="number" value={filtro.max ?? ''} onChange={(e) => setFiltro({ ...filtro, max: num(e.target.value) })} /></label>
      <label>Fracción válida mínima (0 a 1)<input type="number" min={0} max={1} step={0.1} value={filtro.fraccionMin ?? ''} onChange={(e) => setFiltro({ ...filtro, fraccionMin: num(e.target.value) })} /></label>
      {error && <p role="alert">No se pudieron cargar los atributos de las unidades.</p>}
      <Grupo nombre="Clima de Köppen (clase)" opciones={distintos<string>(us, 'koppen')} sel={globales.koppen} alCambiar={(koppen) => cambiar({ ...globales, koppen })} />
      <Grupo nombre="Cobertura IGBP (clase)" opciones={distintos<number>(us, 'igbp')} sel={globales.igbp} alCambiar={(igbp) => cambiar({ ...globales, igbp })} />
      <Grupo nombre="Condición de la tierra" opciones={distintos<string>(us, 'condicion')} sel={globales.clase} alCambiar={(clase) => cambiar({ ...globales, clase })} />
      {attrs && !attrs.zona_demo && <p>Zona DEMO: sin datos en esta base (sin tabla zona_demo).</p>}
      <Grupo nombre="Zona DEMO" opciones={distintos<string>(us, 'zona')} sel={globales.zona} alCambiar={(zona) => cambiar({ ...globales, zona })} />
      <label><input type="checkbox" checked={!!globales.soloEventos} onChange={(e) => cambiar({ ...globales, soloEventos: e.target.checked || undefined })} /> Solo unidades con eventos</label>
      <label>ENSO
        <select aria-describedby="enso-umbral" value={globales.enso ?? ''} onChange={(e) => cambiar({ ...globales, enso: (e.target.value || undefined) as FiltrosGlobales['enso'] })}>
          <option value="">Todos los meses</option>
          <option value="nino">Solo meses de El Niño</option>
          <option value="nina">Solo meses de La Niña</option>
          <option value="neutro">Solo meses neutros</option>
        </select>
      </label>
      <p id="enso-umbral" className="etiqueta">SUPUESTO: |RONI| ≥ {String(UMBRAL_RONI).replace('.', ',')} °C (convención de NOAA para el ONI, aplicada al RONI). Fuera de esos meses el mapa se apaga.</p>
      <p>Las unidades filtradas se ven apagadas con su valor; la trama rayada marca unidades sin dato.</p>
      {seleccion && (
        <section aria-label="Filtros regionales">
          <h3>Regionales de {seleccion.nombre}</h3>
          {!attrs ? <p role="status">Cargando atributos…</p> : !propia ? <p>Sin atributos para esta unidad.</p> : regionales.length === 0 ? <p>Ningún filtro regional aplica a esta unidad.</p> : (
            <ul>{regionales.map((r) => <li key={r.id}><strong>{r.nombre}</strong> <small>FUENTE: {r.evidencia}</small></li>)}</ul>
          )}
        </section>
      )}
    </aside>
  )
}
