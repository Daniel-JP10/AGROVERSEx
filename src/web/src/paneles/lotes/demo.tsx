// asistido por SI: Claude Code (Anthropic), escritura y revisión de código; base del prototipo migrada en el hackatón
import { createRoot } from 'react-dom/client'
import { Lotes } from './Lotes'
import '../../app/tema.css'

// Arnés E2E: zona DEMO andina (unidad COL.7_2 de la muestra)
createRoot(document.getElementById('r')!).render(<Lotes id={new URLSearchParams(location.search).get('id') ?? 'COL.7_2'} />)
