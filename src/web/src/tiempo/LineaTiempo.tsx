// asistido por SI: Claude Code (Anthropic), escritura y revisión de código; base del prototipo migrada en el hackatón
import './tiempo.css'
import { useEffect, useMemo, useRef, useState, type KeyboardEvent } from 'react'
import { useEstado } from '../app/estado'
import { N_MESES } from './valor'
import { CALENDARIO, mesIdAEtiqueta, mesesConHueco } from './huecos'
import { crearReproductor } from './Reproductor'
import { CintaEnso } from './CintaEnso'
import { QueryClient } from '@tanstack/react-query'
import { precargarMeses } from '../datos/consultas'
import { capaPorId } from '../datos/capas'

const VELOCIDAD = 4 // meses por segundo
const qcPrecarga = new QueryClient()
// Sin bloquear: no se espera la promesa. shortcut: nivel 1 fijo, el nivel activo del mapa no está en el estado; subir si hace falta.
const precargar = (a: number, b: number) => { void precargarMeses(1, useEstado.getState().capa, a, b, qcPrecarga) }
const espera = (ms: number) => new Promise((f) => setTimeout(f, ms))

// Pinta el mes pedido y espera a que el globo termine (reutiliza `pintando`); tope 1,5 s
async function pintar(m: number) {
  const s = useEstado.getState()
  s.setMes(m)
  await espera(50)
  const t0 = performance.now()
  while (useEstado.getState().pintando && performance.now() - t0 < 1500) await espera(30)
  if (m >= N_MESES - 1) s.setReproduciendo(false)
}

export function LineaTiempo() {
  const mes = useEstado((s) => s.mes)
  const reproduciendo = useEstado((s) => s.reproduciendo)
  const pintando = useEstado((s) => s.pintando)
  const { setMes, setReproduciendo } = useEstado.getState()
  const idCapa = useEstado((s) => s.capa)
  const [clave, setClave] = useState(capaPorId(idCapa).calendario)
  // Al cambiar de capa, el sombreado sigue al producto que se está pintando
  useEffect(() => { setClave(capaPorId(idCapa).calendario) }, [idCapa])
  const [paso, setPaso] = useState<1 | 12>(1)
  const producto = CALENDARIO[clave]
  const sinDato = useMemo(() => new Set(mesesConHueco(producto)), [producto])

  const rep = useRef(crearReproductor({ velocidad: VELOCIDAD, siguiente: pintar, precargar }))
  useEffect(() => { rep.current.irA(mes) }, [mes])
  useEffect(() => {
    if (reproduciendo) { if (mes >= N_MESES - 1) setMes(0); rep.current.irA(useEstado.getState().mes); rep.current.play() } else rep.current.pausa()
    return () => rep.current.pausa()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [reproduciendo])

  const alTeclado = (e: KeyboardEvent) => {
    const t = e.target as HTMLElement
    if (t.tagName === 'SELECT') return
    const d = e.shiftKey ? 12 : paso
    const acciones: Record<string, () => void> = {
      ArrowRight: () => setMes(mes + d), ArrowUp: () => setMes(mes + d),
      ArrowLeft: () => setMes(mes - d), ArrowDown: () => setMes(mes - d),
      Home: () => setMes(0), End: () => setMes(N_MESES - 1),
      ' ': () => setReproduciendo(!reproduciendo),
    }
    if (e.key === ' ' && t.tagName === 'BUTTON') return // el botón ya reacciona al espacio
    if (acciones[e.key]) { e.preventDefault(); acciones[e.key]() }
  }

  const nota = sinDato.has(mes) ? `sin dato · ${producto.nombre}` : producto.provisionalDesde !== undefined && mes >= producto.provisionalDesde ? 'provisional' : producto.parciales?.includes(mes) ? 'con huecos' : ''

  return (
    <div className="tiempo" onKeyDown={alTeclado}>
      <div className="fila">
        <button onClick={() => setMes(mes - paso)} aria-label="Mes anterior">◀</button>
        <button onClick={() => setReproduciendo(!reproduciendo)} aria-label={reproduciendo ? 'Pausar' : 'Reproducir'}>{reproduciendo ? '❚❚' : '▶'}</button>
        <button onClick={() => setMes(mes + paso)} aria-label="Mes siguiente">▶|</button>
        <span className="ext">{mesIdAEtiqueta(0)}</span>
        <input type="range" min={0} max={N_MESES - 1} value={mes} onChange={(e) => setMes(+e.target.value)} aria-label="Mes" aria-valuetext={mesIdAEtiqueta(mes)} />
        <span className="ext">{mesIdAEtiqueta(N_MESES - 1)}</span>
        <strong className="mes" data-testid="mes">{mesIdAEtiqueta(mes)}</strong>
        <select value={paso} onChange={(e) => setPaso(+e.target.value as 1 | 12)} aria-label="Paso de las flechas"><option value={1}>mes</option><option value={12}>año</option></select>
        <select value={clave} onChange={(e) => setClave(e.target.value)} aria-label="Producto activo">
          {Object.entries(CALENDARIO).map(([k, p]) => <option key={k} value={k}>{p.nombre}</option>)}
        </select>
        {/* El mapa solo muestra este mes cuando no hay "pintando…" */}
        {pintando && <span role="status" className="aviso-t">pintando… el mapa aún no muestra {mesIdAEtiqueta(mes)}</span>}
        {nota && <span className="aviso-t" data-testid="nota">{nota}</span>}
      </div>
      <CintaEnso producto={producto} mes={mes} />
    </div>
  )
}
