// asistido por SI: Claude Code (Anthropic), alerta de helada del gemelo v1.1 §9: avisos primero y estado por estrategia solo junto a ellos
import { idioma, t } from '../../textos/i18n'
import { nombreEstrategia } from '../lote/datos'
import type { ClaveTexto } from '../../textos/en'
import type { EntradaTexto, EstrategiaGemelo } from './gemelo'
import { traducir, type Catalogo } from './textosGemelo'

export interface AlertaHeladaGemelo {
  clave_nombre?: string
  provisional?: boolean
  avisos?: EntradaTexto[]
  validacion?: { estacion?: string; periodo?: [string, string]; n_dias?: number; estacion_dias_le_0c?: number } | null
  estrategias?: Record<string, { estado?: string; clave?: string; parametros?: Record<string, unknown> }>
}

const ESTADO: Record<string, ClaveTexto> = { activa: 'rotaciones.alerta_activa', vigilancia: 'rotaciones.alerta_vigilancia', sin_alerta: 'rotaciones.alerta_sin_alerta' }

export function AlertaHelada({ alerta, estrategias, catalogo }: { alerta?: AlertaHeladaGemelo; estrategias: EstrategiaGemelo[]; catalogo?: Catalogo }) {
  // Un estado nunca se muestra sin sus avisos: sin avisos o sin catálogo no hay nada que leer con garantías
  if (!alerta || !catalogo || !alerta.avisos?.length) return <p className="sin-dato">{t('rotaciones.pendiente_gemelo')}</p>
  const v = alerta.validacion
  const estacion = v && v.estacion && v.periodo && typeof v.n_dias === 'number' && typeof v.estacion_dias_le_0c === 'number'
    ? t('rotaciones.alerta_estacion').replace('{estacion}', v.estacion).replace('{dias}', String(v.estacion_dias_le_0c)).replace('{n_dias}', String(v.n_dias)).replace('{desde}', v.periodo[0]).replace('{hasta}', v.periodo[1])
    : null
  return (
    <div className="alerta-helada" data-testid="alerta-helada">
      {alerta.clave_nombre && <h3 data-texto-gemelo="">{traducir(catalogo, alerta.clave_nombre)}</h3>}
      <ul className="avisos-alerta" data-testid="avisos-alerta">
        {alerta.avisos.map((a, i) => <li key={i} data-texto-gemelo="">{traducir(catalogo, a.clave, a.parametros)}</li>)}
        {estacion && <li data-texto-gemelo="" data-testid="alerta-estacion">{estacion}</li>}
      </ul>
      <dl>
        {estrategias.map((e) => {
          const x = alerta.estrategias?.[e.id]
          if (!x?.estado || !x.clave) return null
          return (
            <div key={e.id} data-estado={x.estado}>
              <dt>{idioma() === 'en' ? nombreEstrategia(e) : e.nombre} <span className="insignia">{ESTADO[x.estado] ? t(ESTADO[x.estado]) : x.estado}</span></dt>
              <dd data-texto-gemelo="">{traducir(catalogo, x.clave, x.parametros)}</dd>
            </div>
          )
        })}
      </dl>
    </div>
  )
}
