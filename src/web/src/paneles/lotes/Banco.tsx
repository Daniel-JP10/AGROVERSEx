// asistido por SI: Claude Code (Anthropic), escritura y revisión de código; base del prototipo migrada en el hackatón
import { useState } from 'react'

// Banco de prueba: formulario de laboratorio que no guarda nada.
const CAMPOS = ['pH', 'Materia orgánica (%)', 'Nitrógeno (mg/kg)']
export function Banco() {
  const [enviado, setEnviado] = useState(false)
  return (
    <form data-testid="banco" onSubmit={(e) => { e.preventDefault(); setEnviado(true) }}>
      <h3>Banco de prueba · análisis de laboratorio</h3>
      {CAMPOS.map((c) => <label key={c} style={{ display: 'block' }}>{c} <input name={c} inputMode="decimal" /></label>)}
      <button type="submit">Probar</button>
      {enviado && <p role="status">Banco de prueba: no se guardó nada. SIMULADO · DEMO</p>}
    </form>
  )
}
