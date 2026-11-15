// asistido por SI: Claude Code (Anthropic), sección El lote (#/lote): bloque, terreno, reloj de suelo desnudo, gemelo, escenario y 3 estrategias
import { useState } from 'react'
import { aHash } from '../../app/ruta'
import { idioma, t, useIdioma, type ClaveTodo } from '../../textos/i18n'
import { Banda } from '../rotaciones/Banda'
import { traducir } from '../rotaciones/textosGemelo'
import { GraficoBanda } from './GraficoBanda'
import {
  escenariosDe, fin, fmt, llenar, nombreEscenario, nombreEstrategia, unidadIndicador, unidadVariable,
  type EstadoLote, type EstrategiaSim, type Perfil, type Relieve, type Simulacion,
} from './datos'
import { indiceMes, UNIDADES_TRAYECTORIA, type VariableTrayectoria } from './unidades'
import './lote.css'

type Listo = Extract<EstadoLote, { estado: 'listo' }>
export const nombreMes = (m: number, forma: 'long' | 'short' = 'long') => new Intl.DateTimeFormat(idioma(), { month: forma, timeZone: 'UTC' }).format(Date.UTC(2001, m, 1))
const valorMes = (e: EstrategiaSim, v: VariableTrayectoria, i: number) => {
  const b = e.trayectoria_mensual?.[v]
  return { p10: b?.p10[i] ?? null, p50: b?.p50[i] ?? null, p90: b?.p90[i] ?? null }
}

/** Las 3 primeras estrategias del paquete según D-039 (prioridades.pesos_iguales.orden). */
export const tresPrimeras = (sim: Simulacion): EstrategiaSim[] =>
  sim.prioridades.pesos_iguales.orden.slice(0, 3).map((id) => sim.estrategias.find((e) => e.id === id)).filter((e): e is EstrategiaSim => !!e)

// Brote de dos hojas sobre una gota de suelo: decorativo
function Brote() {
  return (
    <svg className="brote" viewBox="0 0 64 64" aria-hidden="true" focusable="false">
      <path d="M32 60c-11 0-18-7-18-15 0-9 11-18 18-27 7 9 18 18 18 27 0 8-7 15-18 15z" fill="#5a3e2b" />
      <path d="M32 44V26" stroke="#7be0a0" strokeWidth="3" strokeLinecap="round" />
      <path d="M32 30c-2-8-9-11-16-10 1 7 7 12 16 10z" fill="#4caf6e" />
      <path d="M32 27c2-9 10-13 18-12-1 8-8 14-18 12z" fill="#7be0a0" />
    </svg>
  )
}

function Terreno({ relieve, perfil }: { relieve?: Relieve; perfil?: Perfil }) {
  const e = relieve?.elevacion_p10_p50_p90_m
  const p = relieve?.pendiente_p10_p50_p90_m_m
  return (
    <section className="tarjeta terreno" aria-labelledby="h-terreno">
      <h2 id="h-terreno">{t('lote.propiedades')}</h2>
      <p>{t('lote.elevacion')}: {e ? <Banda p10={e[0]} p50={e[1]} p90={e[2]} unidad="m" /> : <span className="sin-dato">{t('lote.no_disponible')}</span>}<br /><small>{t('lote.elevacion_rango')}</small></p>
      {perfil ? <PerfilSvg perfil={perfil} /> : <p className="sin-dato">{t('lote.no_disponible')}</p>}
      <p>{t('lote.pendiente')}: {relieve && p ? <Banda p10={p[0]} p50={relieve.pendiente_media_m_m} p90={p[2]} unidad="m/m" /> : <span className="sin-dato">{t('lote.no_disponible')}</span>}<br /><small>{t('lote.pendiente_rango')}</small></p>
    </section>
  )
}

function PerfilSvg({ perfil }: { perfil: Perfil }) {
  const A = 240, H = 80, I = 6
  const zs = perfil.elevacion_m, ds = perfil.distancia_m
  const lo = Math.min(...zs), hi = Math.max(...zs)
  const x = (d: number) => I + ((d - ds[0]) / (ds[ds.length - 1] - ds[0] || 1)) * (A - 2 * I)
  const y = (z: number) => I + (1 - (z - lo) / (hi - lo || 1)) * (H - 2 * I - 12)
  const linea = zs.map((z, k) => `${x(ds[k]).toFixed(1)},${y(z).toFixed(1)}`).join(' ')
  const c = perfil.indice_centro
  return (
    <figure className="perfil">
      <figcaption>{t('lote.perfil')}</figcaption>
      <svg viewBox={`0 0 ${A} ${H}`} role="img" aria-label={t('lote.perfil_alt')}>
        <polygon className="relleno" points={`${x(ds[0])},${H - 12} ${linea} ${x(ds[ds.length - 1])},${H - 12}`} />
        <polyline className="linea" fill="none" points={linea} />
        <circle className="p-centro" cx={x(ds[c])} cy={y(zs[c])} r={3} />
        <text className="marca" x={I} y={H - 2}>{`${fmt(lo)}–${fmt(hi)} m`}</text>
      </svg>
    </figure>
  )
}

function Reloj({ e, anio, anios, setAnio }: { e?: EstrategiaSim; anio: number; anios: number; setAnio: (a: number) => void }) {
  const R = 46, C = 60
  const b = e?.trayectoria_mensual?.desnudo
  return (
    <section className="tarjeta reloj" aria-labelledby="h-reloj">
      <h2 id="h-reloj">{t('lote.reloj')}</h2>
      <label className="campo">{t('lote.anio')}{' '}
        <select value={anio} onChange={(ev) => setAnio(Number(ev.target.value))}>
          {Array.from({ length: anios }, (_, a) => <option key={a} value={a + 1}>{a + 1}</option>)}
        </select>
      </label>
      {!e || !b ? <p className="sin-dato">{t('lote.no_disponible')}</p> : (
        <>
          <p><small>{llenar(t('lote.reloj_nota'), { estrategia: nombreEstrategia(e) })}</small></p>
          <svg viewBox="0 0 120 120" role="img" aria-label={`${t('lote.reloj')}, ${llenar(t('lote.anio_n'), { n: String(anio) })}`}>
            {Array.from({ length: 12 }, (_, m) => {
              const i = indiceMes(anio, m)
              const a0 = (m / 12) * 2 * Math.PI - Math.PI / 2, a1 = ((m + 1) / 12) * 2 * Math.PI - Math.PI / 2
              const p = (a: number, r: number) => `${(C + r * Math.cos(a)).toFixed(2)},${(C + r * Math.sin(a)).toFixed(2)}`
              const v = b.p50[i] ?? 0
              return (
                <path key={m} className="sector" style={{ fillOpacity: 0.12 + 0.88 * v }}
                  d={`M${p(a0, 16)} L${p(a0, R)} A${R},${R} 0 0 1 ${p(a1, R)} L${p(a1, 16)} A16,16 0 0 0 ${p(a0, 16)} Z`}>
                  <title>{`${nombreMes(m)}: ${fmt(v)} (${fmt(b.p10[i] ?? 0)}–${fmt(b.p90[i] ?? 0)}) ${t('lote.u_fraccion')}`}</title>
                </path>
              )
            })}
            {Array.from({ length: 12 }, (_, m) => {
              const a = ((m + 0.5) / 12) * 2 * Math.PI - Math.PI / 2
              return <text key={m} className="marca" x={C + 55 * Math.cos(a)} y={C + 55 * Math.sin(a) + 3} textAnchor="middle">{nombreMes(m, 'short').slice(0, 3)}</text>
            })}
          </svg>
          <details><summary>{t('rotaciones.datos_grafico')}</summary><table className="reloj-datos">
            <caption className="sr">{t('lote.reloj')}</caption>
            <tbody>
              {Array.from({ length: 12 }, (_, m) => {
                const i = indiceMes(anio, m)
                return <tr key={m}><th scope="row">{nombreMes(m, 'short')}</th><td><Banda p10={b.p10[i]} p50={b.p50[i]} p90={b.p90[i]} unidad={t('lote.u_fraccion')} /></td></tr>
              })}
            </tbody>
          </table></details>
        </>
      )}
    </section>
  )
}

function Bloque({ loteId, perfil, e, anio, mes, setMes }: { loteId: string; perfil?: Perfil; e?: EstrategiaSim; anio: number; mes: number; setMes: (m: number) => void }) {
  const [capa, setCapa] = useState<'relieve' | 'pendiente'>('relieve')
  const [falla, setFalla] = useState(false)
  const i = indiceMes(anio, mes)
  const src = `${import.meta.env.BASE_URL}lotes/bloque_${loteId}${capa === 'pendiente' ? '_pendiente' : ''}.webp`
  const etiquetas: { clave: ClaveTodo; v: VariableTrayectoria; pos: string }[] = [
    { clave: 'lote.etiqueta_agua', v: 'agua_raiz', pos: 'nw' }, { clave: 'lote.etiqueta_cobertura', v: 'V', pos: 'ne' },
    { clave: 'lote.etiqueta_desnudo', v: 'desnudo', pos: 'sw' }, { clave: 'lote.etiqueta_lluvia', v: 'P', pos: 'se' },
  ]
  return (
    <section className="bloque" aria-labelledby="h-bloque">
      <h2 id="h-bloque" className="sr">{t('lote.capas')}</h2>
      <div className="l-controles">
        <fieldset className="l-capas">
          <legend>{t('lote.capas')}</legend>
          {(['relieve', 'pendiente'] as const).map((c) => (
            <label key={c}><input type="radio" name="capa" value={c} checked={capa === c} onChange={() => setCapa(c)} /> {t(c === 'relieve' ? 'lote.capa_relieve' : 'lote.capa_pendiente')}</label>
          ))}
        </fieldset>
        <label className="campo">{t('lote.mes')}{' '}
          <select value={mes} onChange={(ev) => setMes(Number(ev.target.value))}>
            {Array.from({ length: 12 }, (_, m) => <option key={m} value={m}>{nombreMes(m)}</option>)}
          </select>
        </label>
      </div>
      <div className="l-lienzo">
        {falla || !perfil ? <p className="sin-dato">{t('lote.no_disponible')}</p> : (
          <img src={src} alt={t('lote.bloque_alt')} onError={() => setFalla(true)} />
        )}
        {e && etiquetas.map(({ clave, v, pos }) => {
          const x = valorMes(e, v, i)
          const u = unidadVariable(v)
          return (
            <p key={v} className={`l-etiqueta ${pos}`} data-variable={v}>
              <strong>{t(clave)}</strong> <small>{nombreMes(mes)}, {llenar(t('lote.anio_n'), { n: String(anio) })}</small><br />
              <Banda p10={x.p10} p50={x.p50} p90={x.p90} unidad={u} />
            </p>
          )
        })}
      </div>
      {perfil && (
        <>
          <ul className="leyenda-capa">
            {capa === 'relieve' ? <li>{llenar(t('lote.leyenda_relieve'), { min: perfil.leyenda_relieve_m[0], max: perfil.leyenda_relieve_m[1] })}</li> : (
              <>
                <li className="c0">{llenar(t('lote.leyenda_pendiente_baja'), { a: perfil.leyenda_pendiente_m_m[0] })}</li>
                <li className="c1">{llenar(t('lote.leyenda_pendiente_media'), { a: perfil.leyenda_pendiente_m_m[0], b: perfil.leyenda_pendiente_m_m[1] })}</li>
                <li className="c2">{llenar(t('lote.leyenda_pendiente_alta'), { b: perfil.leyenda_pendiente_m_m[1] })}</li>
              </>
            )}
          </ul>
          <p><small>{llenar(t('lote.bloque_nota'), { crs: perfil.crs_destino, celda: perfil.celda_m, exag: perfil.exageracion_vertical })}</small></p>
        </>
      )}
    </section>
  )
}

function Gemelo({ d, e }: { d: Listo; e?: EstrategiaSim }) {
  const { sim, cat, relieve } = d
  const rot = sim.metadatos.rotulo ?? d.lote.rotulo
  const rotulo = rot?.[idioma()] ?? (rot ? traducir(cat, rot.clave, rot.parametros) : t('etiqueta.simulacion_modelo'))
  const et = e?.indicadores.et_real_mm_anio
  const des = e?.indicadores.dias_suelo_desnudo_anio
  const helada = sim.alertas?.helada_etapa_sensible?.avisos?.find((a) => a.clave === 'alert.frost.station_climatology')?.parametros as Record<string, unknown> | undefined
  const hp = helada && ['km', 'dias', 'dias_dato'].every((k) => fin(helada[k])) ? helada as Record<string, number | string> : undefined
  return (
    <section className="tarjeta gemelo-voz" aria-labelledby="h-gemelo">
      <div className="cabeza"><Brote /><h2 id="h-gemelo">{t('lote.gemelo')}</h2></div>
      <p className="rotulo" data-testid="rotulo"><strong data-texto-gemelo="">{rotulo}</strong></p>
      {e && et && fin(et.p10) && fin(et.p50) && fin(et.p90) && <p className="voz" data-voz="agua">{llenar(t('lote.voz_agua'), { nombre: nombreEstrategia(e), p10: et.p10, p50: et.p50, p90: et.p90 })}</p>}
      {hp && (
        <>
          <p className="voz" data-voz="helada">{llenar(t('lote.voz_helada'), { km: hp.km, dias: hp.dias, dias_dato: hp.dias_dato, desde: String(hp.desde), hasta: String(hp.hasta) })}</p>
          <p className="aviso-estacion"><small>{t('lote.aviso_estacion')}</small></p>
        </>
      )}
      {e && des && fin(des.p10) && fin(des.p90) && <p className="voz" data-voz="desnudo">{llenar(t('lote.voz_desnudo'), { nombre: nombreEstrategia(e), p10: des.p10, p90: des.p90 })}</p>}
      <h3>{t('lote.base')}</h3>
      <ul className="base">
        {sim.clima.fuente.includes('NASA POWER') && <li>{llenar(t('lote.base_clima'), { desde: String(sim.clima.anios[0]), hasta: String(sim.clima.anios[1]) })}</li>}
        {sim.suelo.fuente.includes('SoilGrids 2.0') && <li>{t('lote.base_suelo')}</li>}
        {relieve && <li>{llenar(t('lote.base_relieve'), { producto: relieve.producto })}</li>}
        {hp && sim.alertas?.helada_etapa_sensible?.validacion?.estacion && <li>{llenar(t('lote.base_estacion'), { estacion: sim.alertas.helada_etapa_sensible.validacion.estacion, desde: String(hp.desde), hasta: String(hp.hasta) })}</li>}
        {sim.metadatos.metodo_eto === 'penman_monteith_fao56' && <li>{t('lote.base_eto')}</li>}
      </ul>
      <p className="juicio">{t('aviso.juicio')}</p>
    </section>
  )
}

function Estrategias({ d, sel, setSel, loteId }: { d: Listo; sel?: string; setSel: (id: string) => void; loteId: string }) {
  return (
    <section className="tarjeta estrategias" aria-labelledby="h-estrategias">
      <h2 id="h-estrategias">{t('lote.estrategias')}</h2>
      <p><small>{t('lote.estrategias_nota')}</small></p>
      <ol>
        {tresPrimeras(d.sim).map((e) => (
          <li key={e.id} data-testid="estrategia-lote" data-id={e.id} className={sel === e.id ? 'elegida' : ''}>
            <h3>{nombreEstrategia(e)} <small>({e.id})</small></h3>
            {(['indice_exposicion_erosiva', 'et_real_mm_anio'] as const).map((k) => {
              const ind = e.indicadores[k]
              return (
                <p key={k} data-indicador={k}>
                  {traducir(d.cat, `indicator.${k}.name`)}: {ind ? <Banda p10={ind.p10} p50={ind.p50} p90={ind.p90} unidad={unidadIndicador(d.cat, ind.unidad)} /> : <span className="sin-dato">{t('lote.no_disponible')}</span>}
                </p>
              )
            })}
            <button type="button" aria-pressed={sel === e.id} onClick={() => setSel(e.id)}>{t('lote.elegir')}</button>
          </li>
        ))}
      </ol>
      <p><a href={aHash({ seccion: 'rotaciones', params: { lote: loteId } })}>{t('lote.ver_rotaciones')}</a></p>
    </section>
  )
}

export function VistaLote({ estado, loteId, escenario, setEscenario }: { estado: EstadoLote; loteId: string; escenario: string; setEscenario: (e: string) => void }) {
  useIdioma()
  const [pestana, setPestana] = useState<'campo' | 'tiempo'>('campo')
  const [sel, setSel] = useState<string>()
  const [anio, setAnio] = useState(1)
  const [mes, setMes] = useState(0)
  if (estado.estado !== 'listo') {
    return (
      <main className="seccion lote">
        <h1>{t('lote.titulo')}</h1>
        {estado.estado === 'cargando' ? <p role="status">{t('lote.cargando')}</p> : <p className="sin-dato" role="status">{t('lote.no_disponible')}</p>}
      </main>
    )
  }
  const { sim, cat } = estado
  const top = tresPrimeras(sim)
  const e = top.find((x) => x.id === sel) ?? top[0]
  const anios = sim.metadatos.horizonte_anios
  const avisos = (sim.avisos_claves ?? []).filter((a) => a.clave === 'warning.enso_interim').map((a) => traducir(cat, a.clave, a.parametros))
  return (
    <main className="seccion lote">
      <h1>{t('lote.titulo')} <small className="demo">{t('lote.demo')} · {estado.lote.lote_id}</small></h1>
      <p className="aviso-apoyo" role="note">{t('aviso.apoyo')}</p>
      <div role="tablist" aria-label={t('lote.pestanas')} className="l-pestanas">
        {(['campo', 'tiempo'] as const).map((p) => (
          <button key={p} type="button" role="tab" id={`tab-${p}`} aria-controls={`panel-${p}`} aria-selected={pestana === p} onClick={() => setPestana(p)}>
            {t(p === 'campo' ? 'lote.pestana_campo' : 'lote.pestana_tiempo')}
          </button>
        ))}
      </div>
      {avisos.map((a) => <p key={a} className="aviso-principal" role="note" data-texto-gemelo="">{a}</p>)}
      <div className="rejilla-lote">
        <div className="l-izq">
          <Terreno relieve={estado.relieve} perfil={estado.perfil} />
          <Reloj e={e} anio={anio} anios={anios} setAnio={setAnio} />
        </div>
        <div className="l-centro" role="tabpanel" id={`panel-${pestana}`} aria-labelledby={`tab-${pestana}`}>
          {pestana === 'campo' ? <Bloque loteId={loteId} perfil={estado.perfil} e={e} anio={anio} mes={mes} setMes={setMes} /> : (
            <section className="l-tiempo">
              <p><small>{llenar(t('lote.tiempo_nota'), { n: String(anios) })}</small></p>
              {(Object.keys(UNIDADES_TRAYECTORIA) as VariableTrayectoria[]).map((v) => (
                <GraficoBanda key={v} titulo={t(`lote.var_${v}` as ClaveTodo)} unidad={unidadVariable(v)} anios={anios}
                  series={top.map((x) => ({ id: x.id, nombre: nombreEstrategia(x), ...(x.trayectoria_mensual?.[v] as { p10: number[]; p50: number[]; p90: number[] }) }))} />
              ))}
            </section>
          )}
        </div>
        {/* Director 17:38: escenario y estrategias primero, para verlos sin scroll; la voz del gemelo debajo (mismo orden en el DOM y en pantalla) */}
        <div className="l-der">
          <section className="tarjeta escenario" aria-labelledby="h-escenario">
            <h2 id="h-escenario">{t('lote.escenario')}</h2>
            <select aria-labelledby="h-escenario" value={escenario} onChange={(ev) => setEscenario(ev.target.value)}>
              {escenariosDe(estado.lote).map((x) => <option key={x} value={x}>{nombreEscenario(cat, x)}</option>)}
            </select>
          </section>
          <Estrategias d={estado} sel={e?.id} setSel={setSel} loteId={loteId} />
          <Gemelo d={estado} e={e} />
        </div>
      </div>
    </main>
  )
}
