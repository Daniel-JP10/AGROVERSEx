// asistido por SI: Claude Code (Anthropic), escritura y revisión de código; base del prototipo migrada en el hackatón
import { createRoot } from 'react-dom/client'
import { Rotaciones } from './Rotaciones'
import { FIX_CORN_BELT } from './fixtures'
import '../../app/tema.css'

// Arnés de la prueba E2E: monta el comparador con el fixture del Corn Belt
createRoot(document.getElementById('r')!).render(<Rotaciones resp={FIX_CORN_BELT} />)
