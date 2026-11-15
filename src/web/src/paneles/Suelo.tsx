// asistido por SI: Claude Code (Anthropic), escritura y revisión de código; base del prototipo migrada en el hackatón
import { useEffect, useState } from 'react'
import { clienteDefecto } from '../datos/consultas'
import type { DetalleUnidad } from '../datos/tipos'
import { Chip } from './Chip'
import { t } from '../textos/i18n'

const noMedido = () => [t('suelo.lab'), t('suelo.compactacion'), t('suelo.moMedida'), t('suelo.salMedida')]

const nombres = (): Record<string, string> => ({
  soc_0_30: t('suelo.carbono'), phh2o_0_30: t('suelo.ph'), clay_0_30: t('suelo.arcilla'), sand_0_30: t('suelo.arena'),
  silt_0_30: t('suelo.limo'), bdod_0_30: t('suelo.densidad'), cec_0_30: t('suelo.cic'),
  nitrogen_0_30: t('suelo.nitrogeno'), elev_media: t('suelo.elevMedia'), elev_min: t('suelo.elevMin'), elev_max: t('suelo.elevMax'),
})

export function Suelo({ id }: { id: string }) {
  const [d, setD] = useState<DetalleUnidad | null>(null)
  useEffect(() => { setD(null); clienteDefecto.unidad(id).then(setD).catch(() => {}) }, [id])
  if (!d) return <p role="status">{t('comun.cargando')}</p>
  return (
    <div>
      <p className="etiqueta">{t('suelo.sinFecha')}</p>
      {d.estatico.length ? d.estatico.map((e) => (
        <div className="dato" key={e.variable_id}>
          <span>{nombres()[e.variable_id] ?? e.variable_id} <Chip e={e.etiqueta} /></span>
          <strong>{e.media === null ? t('comun.sinDato') : e.media.toLocaleString('es', { maximumFractionDigits: 2 })} <small>{e.unidad_medida}</small></strong>
        </div>
      )) : <p>{t('suelo.sinAtributos')} <Chip e="PENDIENTE" /></p>}
      <h3>{t('suelo.noMedido')}</h3>
      <ul>{noMedido().map((x) => <li key={x}>{x} <Chip e="PENDIENTE" /></li>)}</ul>
    </div>
  )
}
