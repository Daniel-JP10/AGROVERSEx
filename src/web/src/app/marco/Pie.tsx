// asistido por SI: Claude Code (Anthropic), pie del marco común: aviso de herramienta de apoyo y atribución del mapa
import * as interfaz from '../../secciones/tierra/interfaz'
import { t } from '../../textos/i18n'

// shortcut: la atribución del globo vive en globo/config y la frontera solo deja leer secciones/tierra/interfaz;
// se muestra cuando W2 la reexporte allí como ATRIBUCION (pedido en el reporte de W1)
const ATRIBUCION = (interfaz as unknown as { ATRIBUCION?: string }).ATRIBUCION

export function Pie() {
  return (
    <footer className="pie">
      <p className="aviso-apoyo">{t('aviso.apoyo')}</p>
      {ATRIBUCION && <p className="atribucion">{t('marco.pie.atribucion')}: {ATRIBUCION}</p>}
    </footer>
  )
}
