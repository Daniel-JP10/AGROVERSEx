// asistido por SI: Claude Code (Anthropic), escritura y revisión de código; base del prototipo migrada en el hackatón
import './tiempo.css'
import { useEffect, useMemo, useRef, useState, type KeyboardEvent } from 'react'
import { useEstado } from '../app/estado'
import { N_MESES } from './valor'
import { CALENDARIO, mesIdAEtiqueta, mesesConHueco, provisionalDesdeDe } from './huecos'
import { crearReproductor } from './Reproductor'
import { CintaEnso } from './CintaEnso'
import { cargarMatriz, enRevision, textoEstado } from '../datos/estatico'
import { CAPAS, capaPorId } from '../datos/capas'
import { t, useIdioma } from '../textos/i18n'

const VELOCIDAD = 4 // meses por segundo
// Sin bloquear. Los archivos estáticos traen todos los meses de una variable, así que precargar es cargar la matriz del nivel 1.
// shortcut: nivel 1 fijo, el nivel activo del mapa no está en el estado; subir si hace falta.
const precargar = () => { void cargarMatriz(useEstado.getState().capa, 1).catch(() => undefined) }
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


// Sin reproducción automática en la versión pública: se traba con las series del mundo (ver alTeclado)
export const REPRODUCCION_AUTOMATICA = false
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
  const lengua = useIdioma() // los nombres de producto cambian con el idioma
  // El mes desde el que el producto es provisional sale de la matriz de su variable (nivel 0, unos KB)
  const [provDesde, setProvDesde] = useState<number | undefined>()
  useEffect(() => {
    const capa = CAPAS.find((c) => c.calendario === clave)
    setProvDesde(undefined)
    if (capa) void cargarMatriz(capa.id, 0).then((m) => setProvDesde(provisionalDesdeDe(m))).catch(() => undefined)
  }, [clave])
  // eslint-disable-next-line react-hooks/exhaustive-deps
  const producto = useMemo(() => ({ ...CALENDARIO[clave], ...(provDesde !== undefined && { provisionalDesde: provDesde }) }), [clave, provDesde, lengua])
  const sinDato = useMemo(() => new Set(mesesConHueco(producto)), [producto])

  const rep = useRef(crearReproductor({ velocidad: VELOCIDAD, siguiente: pintar, precargar }))
  useEffect(() => { rep.current.irA(mes) }, [mes])
  useEffect(() => {
    if (reproduciendo) { if (mes >= N_MESES - 1) setMes(0); rep.current.irA(useEstado.getState().mes); rep.current.play() } else rep.current.pausa()
    return () => rep.current.pausa()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [reproduciendo])

  // Director 16:54: Play automático fuera de la versión pública. Medido sobre el dist del mundo (prueba_reproduccion_tiempo.json):
  // 5 a 8 cuadros/s, tareas de más de 1 s y Pause tarda hasta 3 s. El mes se elige a mano (deslizador, pasos de mes y año)
  const alTeclado = (e: KeyboardEvent) => {
    const t = e.target as HTMLElement
    if (t.tagName === 'SELECT') return
    const d = e.shiftKey ? 12 : paso
    const acciones: Record<string, () => void> = {
      ArrowRight: () => setMes(mes + d), ArrowUp: () => setMes(mes + d),
      ArrowLeft: () => setMes(mes - d), ArrowDown: () => setMes(mes - d),
      Home: () => setMes(0), End: () => setMes(N_MESES - 1),
      ...(REPRODUCCION_AUTOMATICA && { ' ': () => setReproduciendo(!reproduciendo) }),
    }
    if (e.key === ' ' && t.tagName === 'BUTTON') return // el botón ya reacciona al espacio
    if (acciones[e.key]) { e.preventDefault(); acciones[e.key]() }
  }

  const nota = sinDato.has(mes) ? `${t('tiempo.sinDato')} · ${producto.nombre}` : enRevision(idCapa, mes) ? textoEstado('provisional', idCapa, mes) : producto.provisionalDesde !== undefined && mes >= producto.provisionalDesde ? t('bandera.provisional') : producto.parciales?.includes(mes) ? t('tiempo.huecos') : ''

  return (
    <div className="tiempo" onKeyDown={alTeclado}>
      <div className="fila">
        <button onClick={() => setMes(mes - paso)} aria-label={t('tiempo.anterior')}>◀</button>
        {REPRODUCCION_AUTOMATICA && <button onClick={() => setReproduciendo(!reproduciendo)} aria-label={reproduciendo ? t('tiempo.pausar') : t('tiempo.reproducir')}>{reproduciendo ? '❚❚' : '▶'}</button>}
        <button onClick={() => setMes(mes + paso)} aria-label={t('tiempo.siguiente')}>▶|</button>
        <span className="ext">{mesIdAEtiqueta(0)}</span>
        <input type="range" min={0} max={N_MESES - 1} value={mes} onChange={(e) => setMes(+e.target.value)} aria-label={t('tiempo.mesEtiqueta')} aria-valuetext={mesIdAEtiqueta(mes)} />
        <span className="ext">{mesIdAEtiqueta(N_MESES - 1)}</span>
        <strong className="mes" data-testid="mes">{mesIdAEtiqueta(mes)}</strong>
        <select value={paso} onChange={(e) => setPaso(+e.target.value as 1 | 12)} aria-label={t('tiempo.paso')}><option value={1}>{t('tiempo.mes')}</option><option value={12}>{t('tiempo.anio')}</option></select>
        <select value={clave} onChange={(e) => setClave(e.target.value)} aria-label={t('tiempo.producto')}>
          {Object.entries(CALENDARIO).map(([k, p]) => <option key={k} value={k}>{p.nombre}</option>)}
        </select>
        {/* El mapa solo muestra este mes cuando no hay "pintando…" */}
        {pintando && <span role="status" className="aviso-t">{t('tiempo.pintando')} {mesIdAEtiqueta(mes)}</span>}
        {nota && <span className="aviso-t" data-testid="nota">{nota}</span>}
      </div>
      <CintaEnso producto={producto} mes={mes} />
    </div>
  )
}
