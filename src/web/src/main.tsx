// asistido por SI: Claude Code (Anthropic), escritura y revisión de código; base del prototipo migrada en el hackatón
import { createRoot } from 'react-dom/client'
import { App } from './app/App'
import './estilos.css'

createRoot(document.getElementById('raiz')!).render(<App />)
