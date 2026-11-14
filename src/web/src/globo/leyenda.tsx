// asistido por SI: Claude Code (Anthropic), escritura y revisión de código; base del prototipo migrada en el hackatón
import { useEffect, useState } from 'react'
import { PALETA } from './config'
import { useEstado } from '../app/estado'
import { capaPorId } from '../datos/capas'
import { clienteDefecto } from '../datos/consultas'
import { ID_PATRON } from './patron'
import { t } from '../textos/i18n'

// Leyenda: escala con unidades, chip de producto y la trama de huecos (el color no es el único canal)
export function Leyenda() {
  const capa = capaPorId(useEstado((s) => s.capa))
  const [producto, setProducto] = useState(t('leyenda.sinProducto'))
  // El chip sale de la tabla variable (/api/meta), no de un texto fijo
  useEffect(() => {
    clienteDefecto.meta().then((x) => {
      const v = x.variables.find((q) => q.id === capa.id) as (typeof x.variables[0] & { producto?: string; resolucion_nativa?: string }) | undefined
      if (v?.producto) setProducto(`${v.producto}${v.resolucion_nativa ? ` · ${v.resolucion_nativa}` : ''}`)
    }).catch(() => undefined)
  }, [capa.id])
  const grad = `linear-gradient(90deg, ${PALETA.map(([p, c]) => `${c} ${p * 100}%`).join(', ')})`
  return (
    <div className="leyenda" role="group" aria-label={t('leyenda.titulo')}>
      <b>{capa.nombre}</b> <span className="chip">{producto}</span>
      <div className="barra" style={{ background: grad }} />
      <div className="extremos"><span>{capa.rango[0]}</span><span>{capa.unidad}</span><span>{capa.rango[1]}+</span></div>
      <div className="hueco"><span className={`muestra ${ID_PATRON}`} aria-hidden="true" /> {t('leyenda.sinDato')}</div>
    </div>
  )
}
