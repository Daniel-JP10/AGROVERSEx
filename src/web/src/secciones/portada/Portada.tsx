// asistido por SI: Claude Code (Anthropic), portada: la idea en dos frases y el botón que arranca el recorrido guiado
import { useRecorrido } from '../../app/recorrido/estado'
import { t } from '../../textos/i18n'

export function Portada() {
  const iniciar = useRecorrido((s) => s.iniciar)
  return (
    <main className="seccion portada">
      <h1>AGROVERSEx</h1>
      <p>{t('portada.idea_1')}</p>
      <p>{t('portada.idea_2')}</p>
      <button type="button" className="boton-principal" onClick={iniciar}>{t('portada.iniciar')}</button>
    </main>
  )
}
