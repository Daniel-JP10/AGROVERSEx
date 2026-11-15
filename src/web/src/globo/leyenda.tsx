// asistido por SI: Claude Code (Anthropic), escritura y revisión de código; base del prototipo migrada en el hackatón
import { useEffect, useState } from 'react'
import { PALETA } from './config'
import { useEstado } from '../app/estado'
import { capaPorId } from '../datos/capas'
import { cargarMatriz } from '../datos/estatico'
import { ID_PATRON } from './patron'
import { t } from '../textos/i18n'

// Leyenda: escala con unidades, chip de producto y la trama de huecos (el color no es el único canal)
export function Leyenda() {
  const capa = capaPorId(useEstado((s) => s.capa))
  const [producto, setProducto] = useState(t('leyenda.sinProducto'))
  // El chip sale de los productos del archivo estático de la variable (nombre completo: GLDAS lleva MODELO)
  useEffect(() => {
    setProducto(t('leyenda.sinProducto'))
    cargarMatriz(capa.id, 0).then((m) => setProducto(m.productos.map((p) => `${p.producto} ${p.version}${p.estado === 'provisional' ? ` (${t('bandera.provisional')})` : ''}`).join(' → '))).catch(() => undefined)
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
