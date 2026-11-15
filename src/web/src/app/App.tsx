// asistido por SI: Claude Code (Anthropic), escritura y revisión de código; base del prototipo migrada en el hackatón
import { Tierra } from '../secciones/tierra/Tierra'
import { Cabecera } from './Cabecera'
import { AVISO_PIE } from '../textos/avisos'

export function App() {
  return (
    <div className="app">
      <Cabecera />
      <Tierra />
      <footer className="pie">{AVISO_PIE}</footer>
    </div>
  )
}
