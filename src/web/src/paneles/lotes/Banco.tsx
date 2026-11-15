// asistido por SI: Claude Code (Anthropic), escritura y revisión de código; base del prototipo migrada en el hackatón
import { useState } from 'react'
import { t } from '../../textos/i18n'

// Banco de prueba: formulario de laboratorio que no guarda nada.
export function Banco() {
  const CAMPOS = ['pH', t('suelo.materiaOrganica'), t('suelo.nitrogenoLab')]
  const [enviado, setEnviado] = useState(false)
  return (
    <form data-testid="banco" onSubmit={(e) => { e.preventDefault(); setEnviado(true) }}>
      <h3>{t('banco.titulo')}</h3>
      {CAMPOS.map((c) => <label key={c} style={{ display: 'block' }}>{c} <input name={c} inputMode="decimal" /></label>)}
      <button type="submit">{t('banco.probar')}</button>
      {enviado && <p role="status">{t('banco.aviso')}</p>}
    </form>
  )
}
