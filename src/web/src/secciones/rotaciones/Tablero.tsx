// asistido por SI: Claude Code (Anthropic), tablero de Rotaciones (plan fase 3 v2 §5): fichas, gráfico con bandas, comparador de escenarios y panel N y C
import { useState, type ReactNode } from 'react'
import { t, type ClaveTodo } from '../../textos/i18n'
import { useModo } from '../../textos/modos'
import { GraficoBanda } from '../lote/GraficoBanda'
import { nombreMes } from '../lote/Lote'
import {
  escenariosDe, llenar, nombreCultivo, nombreEscenario, nombreEstrategia, unidadIndicador, unidadVariable,
  type EstadoLote, type EstrategiaSim, type Simulacion,
} from '../lote/datos'
import { UNIDADES_TRAYECTORIA, type VariableTrayectoria } from '../lote/unidades'
import { Banda } from './Banda'
import { MOSTRAR_CARBONO } from './carbono'
import { ordenar, type Pesos } from './ordenPrioridades'

type Listo = Extract<EstadoLote, { estado: 'listo' }>
const MAX = 3

/** Ids de las estrategias de la simulación en el orden de las prioridades (fórmula del contrato §4). */
export const ordenSimulacion = (sim: Simulacion, pesos: Pesos) =>
  ordenar(sim.estrategias.map((e) => ({ id: e.id, valores: sim.prioridades.valores[e.id] ?? {} })), pesos)

function Fichas({ e }: { e?: EstrategiaSim }) {
  return (
    <section className="tarjeta fichas" aria-labelledby="h-fichas">
      <h2 id="h-fichas">{t('rotaciones.fichas')}</h2>
      {!e ? <p className="sin-dato">{t('lote.no_disponible')}</p> : (
        <>
          <p><small>{llenar(t('rotaciones.fichas_nota'), { estrategia: nombreEstrategia(e) })}</small></p>
          <ol className="secuencia">
            {e.temporadas.map((s, k) => {
              const m = /^A(\d+)-(\d\d)-(\d\d)$/.exec(s.siembra)
              return (
                <li key={k} className="ficha">
                  <strong>{nombreCultivo(s.cultivo)}</strong>
                  {m && <small>{llenar(t('rotaciones.siembra'), { mes: nombreMes(Number(m[2]) - 1, 'short'), dia: String(Number(m[3])), anio: String(Number(m[1])) })}</small>}
                </li>
              )
            })}
          </ol>
        </>
      )}
    </section>
  )
}

function GraficoCentral({ sim, orden }: { sim: Simulacion; orden: string[] }) {
  const [variable, setVariable] = useState<VariableTrayectoria>('agua_raiz')
  const [elegidas, setElegidas] = useState<string[] | null>(null)
  // Sin elección propia, las 3 primeras de las prioridades
  const ids = elegidas ?? orden.slice(0, MAX)
  const alternar = (id: string) => {
    const ya = ids.includes(id)
    if (!ya && ids.length >= MAX) return
    setElegidas(ya ? ids.filter((x) => x !== id) : [...ids, id])
  }
  const series = ids.map((id) => sim.estrategias.find((e) => e.id === id)).filter((e): e is EstrategiaSim => !!e)
  return (
    <section className="tarjeta grafico-central" aria-labelledby="h-grafico">
      <h2 id="h-grafico">{t('rotaciones.grafico')}</h2>
      <p><small>{t('rotaciones.grafico_nota')}</small></p>
      <div className="ejes">
        <label>{t('rotaciones.variable')}{' '}
          <select value={variable} onChange={(ev) => setVariable(ev.target.value as VariableTrayectoria)}>
            {(Object.keys(UNIDADES_TRAYECTORIA) as VariableTrayectoria[]).map((v) => <option key={v} value={v}>{t(`lote.var_${v}` as ClaveTodo)}</option>)}
          </select>
        </label>
      </div>
      <fieldset className="elegidas">
        <legend>{t('rotaciones.elegidas')} <small>{t('rotaciones.maximo')}</small></legend>
        {orden.map((id) => {
          const e = sim.estrategias.find((x) => x.id === id)
          if (!e) return null
          return (
            <label key={id}><input type="checkbox" checked={ids.includes(id)} disabled={!ids.includes(id) && ids.length >= MAX} onChange={() => alternar(id)} /> {nombreEstrategia(e)} <small>({id})</small></label>
          )
        })}
      </fieldset>
      <GraficoBanda titulo={t(`lote.var_${variable}` as ClaveTodo)} unidad={unidadVariable(variable)} anios={sim.metadatos.horizonte_anios}
        series={series.map((e) => ({ id: e.id, nombre: nombreEstrategia(e), ...(e.trayectoria_mensual?.[variable] as { p10: number[]; p50: number[]; p90: number[] }) }))} />
      <p className="eje-anios"><small>{t('rotaciones.eje_anios')}</small></p>
    </section>
  )
}

function ComparadorEscenarios({ d, orden, escenario, setEscenario }: { d: Listo; orden: string[]; escenario: string; setEscenario: (e: string) => void }) {
  const ks = ['indice_exposicion_erosiva', 'drenaje_mm_anio'] as const
  return (
    <section className="tarjeta comparador-esc" aria-labelledby="h-comp-esc">
      <h2 id="h-comp-esc">{t('rotaciones.comparador')}</h2>
      <p><small>{t('rotaciones.comparador_nota')}</small></p>
      <label>{t('rotaciones.escenario_elegido')}{' '}
        <select value={escenario} onChange={(ev) => setEscenario(ev.target.value)}>
          {escenariosDe(d.lote).map((x) => <option key={x} value={x}>{nombreEscenario(d.cat, x)}</option>)}
        </select>
      </label>
      <table>
        <thead><tr><th scope="col">{t('rotaciones.estrategia_col')}</th>{ks.map((k) => <th key={k} scope="col" data-texto-gemelo="">{d.cat[`indicator.${k}.name`] ?? k}</th>)}</tr></thead>
        <tbody>
          {orden.map((id) => {
            const e = d.sim.estrategias.find((x) => x.id === id)
            if (!e) return null
            return (
              <tr key={id} data-testid="fila-escenario">
                <th scope="row">{nombreEstrategia(e)} <small>({id})</small></th>
                {ks.map((k) => {
                  const i = e.indicadores[k]
                  return <td key={k}>{i ? <Banda p10={i.p10} p50={i.p50} p90={i.p90} unidad={unidadIndicador(d.cat, i.unidad)} /> : <span className="sin-dato">{t('lote.no_disponible')}</span>}</td>
                })}
              </tr>
            )
          })}
        </tbody>
      </table>
    </section>
  )
}

/** Panel N y C: solo campos del gemelo, misma base; detrás de MOSTRAR_CARBONO. */
export function PanelNC({ sim, e, mostrar = MOSTRAR_CARBONO }: { sim: Simulacion; e?: EstrategiaSim; mostrar?: boolean }) {
  useModo((s) => s.modo) // suscripción: repinta al cambiar de modo
  const modo = useModo.getState().modo
  const c = e?.trayectoria_mensual?.C
  const cambio = e?.indicadores.cambio_carbono_t_ha
  return (
    <section className="tarjeta panel-nc" aria-labelledby="h-nc" data-testid="panel-nc">
      <h2 id="h-nc">{t('rotaciones.nc')}</h2>
      {!mostrar || !c || !cambio ? <p className="sin-dato">{t('rotaciones.nc_no_disponible')}</p> : (
        <>
          {/* V6: el paquete no trae estado inicial de C; el índice 0 es la media de enero del año 1 y se rotula así */}
          {[c.p10[0], c.p50[0], c.p90[0]].every((v) => typeof v === 'number' && Number.isFinite(v))
            ? <p><span data-banda="">{llenar(t('rotaciones.nc_inicial'), { p10: c.p10[0] as number, p50: c.p50[0] as number, p90: c.p90[0] as number })}</span></p>
            : <p className="sin-dato">{t('rotaciones.nc_no_disponible')}</p>}
          <p><small>{t('rotaciones.nc_base')}</small></p>
          <p>{t('rotaciones.nc_cambio')}: <Banda p10={cambio.p10} p50={cambio.p50} p90={cambio.p90} unidad="t C/ha" /></p>
          {modo === 'tecnico' && (
            <ul className="limitaciones">
              <li>{t('rotaciones.nc_lim_rango')}</li>
              <li>{llenar(t('rotaciones.nc_lim_muestras'), { n: String(sim.metadatos.miembros?.parametros ?? '') })}</li>
            </ul>
          )}
        </>
      )}
    </section>
  )
}

export function Tablero({ d, pesos, escenario, setEscenario, prioridades }: { d: Listo; pesos: Pesos; escenario: string; setEscenario: (e: string) => void; prioridades?: ReactNode }) {
  const orden = ordenSimulacion(d.sim, pesos)
  const primera = d.sim.estrategias.find((e) => e.id === orden[0])
  return (
    <div className="tablero">
      <div className="t-izq">
        <Fichas e={primera} />
        <PanelNC sim={d.sim} e={primera} />
      </div>
      <div className="t-centro"><GraficoCentral key={orden.slice(0, MAX).join()} sim={d.sim} orden={orden} /></div>
      <div className="t-der">{prioridades}<ComparadorEscenarios d={d} orden={orden} escenario={escenario} setEscenario={setEscenario} /></div>
      {d.sim.metadatos.metodo_eto === 'penman_monteith_fao56' && <p className="metodo" data-testid="metodo">{t('rotaciones.metodo')}</p>}
    </div>
  )
}
