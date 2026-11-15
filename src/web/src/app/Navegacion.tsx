// asistido por SI: Claude Code (Anthropic), navegación entre las seis secciones del universo (fase 3: el gemelo se fusiona en #/lote)
import { SECCIONES, aHash, type Seccion } from './ruta'
import { t, type ClaveTodo } from '../textos/i18n'

// La portada se alcanza con la marca AGROVERSEx; aquí van las seis secciones
export const NAV = SECCIONES.filter((s) => s !== 'portada')

// Enlaces nativos: se usan con Tab y Enter sin código extra
export function Navegacion({ actual }: { actual: Seccion }) {
  return (
    <nav className="nav" aria-label={t('marco.nav.etiqueta')}>
      {NAV.map((s) => (
        <a key={s} href={aHash({ seccion: s, params: {} })} aria-current={s === actual ? 'page' : undefined}>{t(`marco.nav.${s}` as ClaveTodo)}</a>
      ))}
    </nav>
  )
}
