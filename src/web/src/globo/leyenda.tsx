// asistido por SI: Claude Code (Anthropic), leyenda en hoja: variable, unidad, producto, versión y estado de meta.json, trama sin dato, y ponderación con PI-D1 en Technical (plan v2 §3, S1w)
import { useEffect, useState } from 'react'
import metaBuild from '../../public/datos/meta.json'
import { PALETA } from './config'
import { useEstado } from '../app/estado'
import { capaPorId } from '../datos/capas'
import { cargarMeta, hayMundo, metaActual, textoEstado, usePonderacion } from '../datos/estatico'
import { CAMPO_PI_D1, PI_D1_INFORME, rangoPiD1 } from '../secciones/ciencia/pi_d1'
import { ID_PATRON } from './patron'
import { idioma, t, useIdioma } from '../textos/i18n'
import { useModo } from '../textos/modos'

type ProductoMeta = { producto: string; version: string; estado: 'final' | 'provisional' }
type Variables = Record<string, { productos: ProductoMeta[] }>

// Productos de la variable tal como los declara meta.json (lo escribe src/mapa_estatico/construir.py); el del despliegue manda
export const productosDe = (variable: string, meta: { variables?: unknown } = metaActual()): ProductoMeta[] =>
  (meta.variables as Variables | undefined)?.[variable]?.productos ?? (metaBuild.variables as Variables)[variable]?.productos ?? []

const pc = (x: number) => (x * 100).toLocaleString(idioma(), { minimumFractionDigits: 1, maximumFractionDigits: 1 })
/** Línea PI-D1 del modo Technical: cifras de pi_d1_mundo.json al umbral registrado, sin Late; null si el archivo no las trae */
export function lineaPiD1(): string | null {
  const r = rangoPiD1(PI_D1_INFORME, 'registrado')
  return r ? t('tierra.pond.pid1').replace('{min}', pc(r.min)).replace('{max}', pc(r.max)) : null
}

// Escala con unidades, producto con estado y la trama de huecos (el color no es el único canal)
export function Leyenda() {
  useIdioma()
  const capa = capaPorId(useEstado((s) => s.capa))
  const mes = useEstado((s) => s.mes)
  const modo = useModo((s) => s.modo)
  const { ponderacion, set } = usePonderacion()
  const [, setMeta] = useState(0)
  useEffect(() => { cargarMeta().then(() => setMeta((n) => n + 1)).catch(() => undefined) }, [])
  const productos = productosDe(capa.id)
  const mundo = hayMundo()
  const pond = mundo ? ponderacion : 'area'
  const linea = lineaPiD1()
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
        <dt>{t('tierra.pond.titulo')}</dt>
        <dd data-ponderacion={pond}>{t(pond === 'cultivo' ? 'tierra.pond.cultivo' : 'tierra.pond.area')}</dd>
      </dl>
      {modo === 'tecnico' && mundo && (
        <div className="ponderacion" role="radiogroup" aria-label={t('tierra.pond.titulo')}>
          {(['cultivo', 'area'] as const).map((p) => (
            <label key={p}><input type="radio" name="ponderacion" value={p} checked={ponderacion === p} onChange={() => set(p)} /> {t(p === 'cultivo' ? 'tierra.pond.cultivo' : 'tierra.pond.area')}</label>
          ))}
        </div>
      )}
      {modo === 'tecnico' && linea && <p className="pid1" data-fuente={CAMPO_PI_D1}>{linea} <small>{t('tierra.pond.fuente')}</small></p>}
      {modo === 'tecnico' && <p className="limites">{t('tierra.limites')}</p>}
      <div className="hueco"><span className={`muestra ${ID_PATRON}`} aria-hidden="true" /> {t('leyenda.sinDato')}</div>
    </div>
  )
}
