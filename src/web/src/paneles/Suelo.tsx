// asistido por SI: Claude Code (Anthropic), pestaña Soil: T-D4 no corre hoy, nunca se muestra la base simulada (plan v2 §7.5)
import { t } from '../textos/i18n'

export function Suelo(_: { id: string }) {
  return (
    <div role="status" data-testid="suelo">
      <p><strong>{t('tierra.suelo.noDisponible')}</strong></p>
      <p className="hueco">{t('tierra.suelo.nota')}</p>
    </div>
  )
}
