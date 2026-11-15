// asistido por SI: Claude Code (Anthropic), navegación entre las siete secciones del universo
import { SECCIONES, aHash, type Seccion } from './ruta'
import { t } from '../textos/i18n'

// Enlaces nativos: se usan con Tab y Enter sin código extra
export function Navegacion({ actual }: { actual: Seccion }) {
  return (
    <nav className="nav" aria-label={t('nav.etiqueta')}>
      {SECCIONES.map((s) => (
        <a key={s} href={aHash({ seccion: s, params: {} })} aria-current={s === actual ? 'page' : undefined}>{t(`seccion.${s}`)}</a>
      ))}
    </nav>
  )
}
