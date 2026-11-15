// asistido por SI: Claude Code (Anthropic), entrada de la sección El lote para React.lazy (W1 la monta en #/lote)
import { useState } from 'react'
import { useRuta } from '../../app/ruta'
import { loteDeHash, useLote } from './datos'
import { VistaLote } from './Lote'

// Lee ?lote= del hash (por defecto DEMO-COL-01); useRuta solo se usa para repintar al cambiar el hash
export default function Lote() {
  useRuta()
  const loteId = loteDeHash(typeof window === 'undefined' ? '' : window.location.hash)
  const [escenario, setEscenario] = useState('historico')
  return <VistaLote key={loteId} estado={useLote(loteId, escenario)} loteId={loteId} escenario={escenario} setEscenario={setEscenario} />
}
