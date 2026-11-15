// asistido por SI: Claude Code (Anthropic), comparador de la línea base y el frente con indicadores en banda y tarjeta de cinco secciones v1.1
import { t } from '../../textos/i18n'
import type { ClaveTexto } from '../../textos/en'
import { Banda } from './Banda'
import { SECCIONES_TARJETA, type EstrategiaGemelo, type SeccionTarjeta, type Tarjeta as TTarjeta } from './gemelo'
import { traducir, type Catalogo } from './textosGemelo'

// data-bloque conserva los nombres cortos que usan las pruebas y el recorrido
const BLOQUE: Record<SeccionTarjeta, [string, ClaveTexto]> = {
  por_que: ['porque', 'tarjeta.porque'], evidencia: ['evidencia', 'tarjeta.evidencia'], beneficios: ['beneficios', 'tarjeta.beneficios'], vacios: ['vacios', 'tarjeta.vacios'], riesgos: ['riesgos', 'tarjeta.riesgos'],
}

interface P { e: EstrategiaGemelo; base?: boolean; tarjeta?: TTarjeta; catalogo?: Catalogo }

function Tarjeta({ e, base, tarjeta, catalogo }: P) {
  const tr = (clave: string | undefined, plano: string) => (catalogo && clave ? traducir(catalogo, clave) : plano)
  return (
    <article className="estrategia" data-testid="estrategia">
      <h3>{e.nombre} <span className="etiqueta">{e.etiqueta}</span></h3>
      <p className="insignia">{base ? <span data-testid="linea-base">{t('rotaciones.linea_base')}</span> : t('rotaciones.alternativa')}</p>
      <p><strong>{t('rotaciones.secuencia')}:</strong> {e.secuencia.replace(/\s*->\s*/g, ' → ')}</p>
      <p className="juicio" role="note">{t('aviso.juicio')}</p>
      <table>
        <caption>{t('rotaciones.indicadores')}</caption>
        <tbody>
          {Object.entries(e.indicadores).map(([nombre, i]) => (
            <tr key={nombre}>
              <th scope="row" data-texto-gemelo="">{tr(i.nombre_clave, nombre.replace(/_/g, ' '))}</th>
              <td><Banda p10={i.p10} p50={i.p50} p90={i.p90} unidad={tr(`unit.${i.unidad}`, i.unidad)} /></td>
              <td><small data-texto-gemelo="">{catalogo && i.explicacion_clave ? traducir(catalogo, i.explicacion_clave) : `${i.definicion} ${i.explicacion}`}</small></td>
            </tr>
          ))}
        </tbody>
      </table>
      {SECCIONES_TARJETA.map((s) => {
        const [b, clave] = BLOQUE[s]
        const entradas = catalogo ? tarjeta?.[s] : undefined
        return (
          <section key={s} data-bloque={b}>
            <h4>{tarjeta?.secciones_claves?.[s] && catalogo ? traducir(catalogo, tarjeta.secciones_claves[s]) : t(clave)}</h4>
            {entradas?.length
              ? <ul>{entradas.map((x, n) => <li key={n} data-texto-gemelo="">{traducir(catalogo!, x.clave, x.parametros)}</li>)}</ul>
              : <p className="sin-dato">{t('rotaciones.pendiente_gemelo')}</p>}
          </section>
        )
      })}
    </article>
  )
}

// orden: ids de las estrategias según las prioridades; sin él, la línea base primero y luego el frente
export function ComparadorEstrategias({ linea_base, frente, tarjetas, catalogo, orden }: { linea_base: EstrategiaGemelo; frente: EstrategiaGemelo[]; tarjetas?: Record<string, TTarjeta>; catalogo?: Catalogo; orden?: string[] }) {
  const todas = [linea_base, ...frente]
  const lista = orden ? orden.map((id) => todas.find((e) => e.id === id)).filter((e): e is EstrategiaGemelo => !!e) : todas
  return (
    <section className="comparador-estrategias" aria-label={t('seccion.rotaciones')}>
      {lista.map((e) => <Tarjeta key={e.id} e={e} base={e.id === linea_base.id} tarjeta={tarjetas?.[e.id]} catalogo={catalogo} />)}
    </section>
  )
}
