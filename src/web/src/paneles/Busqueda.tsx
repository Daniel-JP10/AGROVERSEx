// asistido por SI: Claude Code (Anthropic), escritura y revisión de código; base del prototipo migrada en el hackatón
import { useEffect, useRef, useState } from 'react'
import type { FilaIndice } from '../datos/busqueda'
import { claveUnidad, cargarFilas, porClave } from '../datos/indice'
import { useEstado } from '../app/estado'
import { nombreNivel } from '../globo/config'
import { useIdioma, t } from '../textos/i18n'

export function Busqueda() {
  const [texto, setTexto] = useState('')
  const [res, setRes] = useState<FilaIndice[]>([])
  const [activo, setActivo] = useState(0)
  const [listo, setListo] = useState(false)
  const worker = useRef<Worker | null>(null)
  const rid = useRef(0)
  const seleccionar = useEstado((s) => s.seleccionar)
  const lengua = useIdioma()

  // Carga perezosa tras el primer render; el buscador vive en un Worker. una sola descarga (indice.ts); el Worker recibe las filas
  useEffect(() => {
    const w = new Worker(new URL('../datos/busqueda.worker.ts', import.meta.url), { type: 'module' })
    w.onmessage = (e: MessageEvent<{ rid: number; res: FilaIndice[] }>) => { if (e.data.rid === rid.current) setRes(e.data.res) }
    worker.current = w
    void cargarFilas().then((filas) => { w.postMessage({ filas }); setListo(true) })
    return () => w.terminate()
  }, [])
  useEffect(() => {
    if (!texto.trim()) return setRes([])
    worker.current?.postMessage({ rid: ++rid.current, texto })
  }, [texto, listo])

  const elegir = (f: FilaIndice) => {
    const u = porClave.get(claveUnidad(f.nivel, f.id))
    if (u) seleccionar(u)
    setTexto(''); setRes([])
  }
  const abierto = !!texto && res.length > 0
  return (
    <div className="busqueda">
      <input
        type="search" placeholder={listo ? t('busqueda.placeholder') : t('busqueda.cargando')} aria-label={t('busqueda.etiqueta')}
        role="combobox" aria-expanded={abierto} aria-controls="res-busqueda" aria-autocomplete="list"
        aria-activedescendant={abierto ? `res-${activo}` : undefined} value={texto}
        onChange={(e) => { setTexto(e.target.value); setActivo(0) }}
        onKeyDown={(e) => {
          if (e.key === 'ArrowDown') { e.preventDefault(); setActivo((a) => Math.min(a + 1, res.length - 1)) }
          else if (e.key === 'ArrowUp') { e.preventDefault(); setActivo((a) => Math.max(a - 1, 0)) }
          else if (e.key === 'Enter' && res[activo]) elegir(res[activo])
          else if (e.key === 'Escape') { if (texto) setTexto(''); else seleccionar(null) }
        }}
      />
      {abierto && (
        <ul role="listbox" id="res-busqueda">
          {res.map((f, i) => (
            <li key={f.id} id={`res-${i}`} role="option" aria-selected={i === activo} className={i === activo ? 'activo' : ''} onMouseDown={() => elegir(f)}>
              {f.d === 1 ? t('unidad.disputa') : (lengua === 'en' ? f.en : f.es) ?? f.n} <small>{f.d === 1 ? '' : f.nivel === 0 ? nombreNivel(0) : f.ctx}</small>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}
