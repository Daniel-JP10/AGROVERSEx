// asistido por SI: Claude Code (Anthropic), deslizadores de prioridades del agricultor (gemelo_api §4): solo reordenan, no recalculan
import type { ClaveTexto } from '../../textos/en'
import { t } from '../../textos/i18n'
import { DESLIZADORES, PESO_MAX, type Deslizador, type Pesos } from './ordenPrioridades'

export function Deslizadores({ pesos, alCambiar }: { pesos: Pesos; alCambiar: (k: Deslizador, v: number) => void }) {
  return (
    <section className="prioridades" aria-labelledby="h-prioridades">
      <h2 id="h-prioridades">{t('rotaciones.prioridades')}</h2>
      <p>{t('prioridades.nota')}</p>
      {DESLIZADORES.map((k) => (
        <label key={k} className="deslizador">
          <span>{t(`prioridades.${k}` as ClaveTexto)}</span>
          <small>{t('prioridades.ninguna')}</small>
          <input type="range" min={0} max={PESO_MAX} step={1} value={pesos[k]} data-deslizador={k} onChange={(e) => alCambiar(k, Number(e.target.value))} />
          <small>{t('prioridades.alta')}</small>
        </label>
      ))}
    </section>
  )
}
