// asistido por SI: Claude Code (Anthropic), leyenda en hoja: variable, unidad, producto, versión y estado de meta.json, y trama sin dato (plan v2 §3)
import meta from '../../public/datos/meta.json'
import { PALETA } from './config'
import { useEstado } from '../app/estado'
import { capaPorId } from '../datos/capas'
import { textoEstado } from '../datos/estatico'
import { ID_PATRON } from './patron'
import { t, useIdioma } from '../textos/i18n'

type ProductoMeta = { producto: string; version: string; estado: 'final' | 'provisional' }
const VARIABLES = meta.variables as Record<string, { productos: ProductoMeta[] }>

// Productos de la variable tal como los declara meta.json (lo escribe src/mapa_estatico/construir.py)
export const productosDe = (variable: string): ProductoMeta[] => VARIABLES[variable]?.productos ?? []

// Escala con unidades, producto con estado y la trama de huecos (el color no es el único canal)
export function Leyenda() {
  useIdioma()
  const capa = capaPorId(useEstado((s) => s.capa))
  const mes = useEstado((s) => s.mes)
  const productos = productosDe(capa.id)
  const grad = `linear-gradient(90deg, ${PALETA.map(([p, c]) => `${c} ${p * 100}%`).join(', ')})`
  return (
    <div className="leyenda hoja" role="group" aria-label={t('leyenda.titulo')}>
      <b>{capa.nombre}</b>
      <div className="barra" style={{ background: grad }} />
      <div className="extremos"><span>{capa.rango[0]}</span><span>{capa.unidad}</span><span>{capa.rango[1]}+</span></div>
      <dl>
        <dt>{t('tierra.leyenda.unidad')}</dt><dd>{capa.unidad}</dd>
        <dt>{t('tierra.leyenda.producto')}</dt>
        <dd>{productos.length ? productos.map((p) => <span key={p.producto} className="chip">{p.producto} {p.version} · {textoEstado(p.estado, capa.id, p.estado === 'provisional' ? mes : undefined)}</span>) : t('leyenda.sinProducto')}</dd>
      </dl>
      <div className="hueco"><span className={`muestra ${ID_PATRON}`} aria-hidden="true" /> {t('leyenda.sinDato')}</div>
    </div>
  )
}
