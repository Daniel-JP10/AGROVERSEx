// asistido por SI: Claude Code (Anthropic), resumen corto de la pestaña Rotaciones del panel con enlace a la sección completa
import { t } from '../../textos/i18n'
import type { RespRotaciones } from './datos'

// El comparador completo vive en #/rotaciones y lee al gemelo v1.1; aquí no se muestra ningún resultado
export function Rotaciones(_: { resp: RespRotaciones }) {
  return (
    <section className="comparador" aria-label={t('seccion.rotaciones')}>
      <p>{t('rotaciones.panel_resumen')}</p>
      <p><a href="#/rotaciones">{t('rotaciones.panel_enlace')}</a></p>
    </section>
  )
}
