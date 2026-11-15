// asistido por SI: Claude Code (Anthropic), #/gemelo pasa a ser la sección El lote (plan fase 3 v2 §4); W1 redirige #/gemelo a #/lote
import Lote from '../lote'

// Se conserva el nombre mientras app/App.tsx (W1) lo importe; cuando nada lo importe, este archivo se borra
export function Gemelo() {
  return <Lote />
}
