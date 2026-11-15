// asistido por SI: Claude Code (Anthropic), respaldo de #/lote mientras la sección de W3 no exista o carga
import { t } from '../../textos/i18n'

export function CargandoSeccion() {
  return <main className="seccion" aria-busy="true"><p role="status">{t('marco.lote.cargando')}</p></main>
}

export function MarcadorLote() {
  return (
    <main className="seccion">
      <h1>{t('marco.nav.lote')}</h1>
      <p className="sin-dato" role="status">{t('marco.lote.pronto')}</p>
    </main>
  )
}
