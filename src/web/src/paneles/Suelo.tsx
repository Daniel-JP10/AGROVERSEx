// asistido por SI: Claude Code (Anthropic), escritura y revisión de código; base del prototipo migrada en el hackatón
import { useEffect, useState } from 'react'
import { clienteDefecto } from '../datos/consultas'
import type { DetalleUnidad } from '../datos/tipos'
import { Chip } from './Chip'

const NO_MEDIDO = ['Análisis de laboratorio de la finca', 'Compactación', 'Materia orgánica medida', 'Salinidad medida']

const NOMBRE: Record<string, string> = {
  soc_0_30: 'Carbono orgánico (0-30 cm)', phh2o_0_30: 'pH en agua (0-30 cm)', clay_0_30: 'Arcilla (0-30 cm)', sand_0_30: 'Arena (0-30 cm)',
  silt_0_30: 'Limo (0-30 cm)', bdod_0_30: 'Densidad aparente (0-30 cm)', cec_0_30: 'Capacidad de intercambio catiónico (0-30 cm)',
  nitrogen_0_30: 'Nitrógeno (0-30 cm)', elev_media: 'Elevación media', elev_min: 'Elevación mínima', elev_max: 'Elevación máxima',
}

export function Suelo({ id }: { id: string }) {
  const [d, setD] = useState<DetalleUnidad | null>(null)
  useEffect(() => { setD(null); clienteDefecto.unidad(id).then(setD).catch(() => {}) }, [id])
  if (!d) return <p role="status">Cargando…</p>
  return (
    <div>
      <p className="etiqueta">sin fecha · media del producto agregado, sin intervalo</p>
      {d.estatico.length ? d.estatico.map((e) => (
        <div className="dato" key={e.variable_id}>
          <span>{NOMBRE[e.variable_id] ?? e.variable_id} <Chip e={e.etiqueta} /></span>
          <strong>{e.media === null ? 'sin dato' : e.media.toLocaleString('es', { maximumFractionDigits: 2 })} <small>{e.unidad_medida}</small></strong>
        </div>
      )) : <p>Sin atributos de suelo <Chip e="PENDIENTE" /></p>}
      <h3>No medido</h3>
      <ul>{NO_MEDIDO.map((x) => <li key={x}>{x} <Chip e="PENDIENTE" /></li>)}</ul>
    </div>
  )
}
