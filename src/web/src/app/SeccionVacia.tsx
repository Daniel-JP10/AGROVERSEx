// asistido por SI: Claude Code (Anthropic), cuerpo común de las secciones todavía sin contenido
import { t } from '../textos/i18n'
import type { ClaveTexto } from '../textos/en'

// Título, frase de lo que va a mostrar y estado sin dato; ningún número
export function SeccionVacia({ titulo, descripcion }: { titulo: ClaveTexto; descripcion: ClaveTexto }) {
  return (
    <main className="seccion">
      <h1>{t(titulo)}</h1>
      <p>{t(descripcion)}</p>
      <p className="sin-dato" role="status">{t('aviso.sin_dato')}</p>
    </main>
  )
}
