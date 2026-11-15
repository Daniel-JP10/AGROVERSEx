// asistido por SI: Claude Code (Anthropic), escritura y revisión de código; base del prototipo migrada en el hackatón
import { useEffect, useState } from 'react'
import { Resumen } from './Resumen'
import { Series } from './Series'
import { Suelo } from './Suelo'
import { Fuentes } from './Fuentes'
import { Rotaciones } from './comparador/Rotaciones'
import { pedirRotaciones } from './comparador/datos'
import { Lotes } from './lotes/Lotes'
import './panel.css'

const BASE = ['Resumen', 'Series', 'Suelo', 'Rotaciones'] as const
type Pestana = (typeof BASE)[number] | 'Lotes' | 'Fuentes'
import { Miga } from './Miga'
import { useEstado } from '../app/estado'
import { NOMBRE_NIVEL, nombreUnidad } from '../globo/config'
import { t } from '../textos/i18n'
import { HAY_API } from '../comun/rutas'

export function PanelRegion() {
  const sel = useEstado((s) => s.seleccion)
  const seleccionar = useEstado((s) => s.seleccionar)
  const aviso = useEstado((s) => s.aviso)
  const tab = useEstado((s) => s.pestana) as Pestana
  const setTab = useEstado((s) => s.abrirPestana)
  const [rot, setRot] = useState<Awaited<ReturnType<typeof pedirRotaciones>> | null>(null)
  const [errRot, setErrRot] = useState(false)
  const idSel = sel ? String(sel.id) : ''
  useEffect(() => {
    setRot(null); setErrRot(false)
    if (idSel && !HAY_API) setErrRot(true) // sin API no se pide /api/rotaciones (D-014)
    else if (idSel) pedirRotaciones(idSel).then(setRot).catch(() => setErrRot(true))
  }, [idSel])
  // Lotes solo existe en zonas DEMO (la zona sale de zona_demo vía /api/rotaciones)
  const PESTANAS: Pestana[] = [...BASE, ...(rot?.zona ? ['Lotes' as const] : []), 'Fuentes']
  const activa: Pestana = PESTANAS.includes(tab) ? tab : 'Resumen'
  useEffect(() => {
    const f = (e: KeyboardEvent) => { if (e.key === 'Escape') seleccionar(null) }
    addEventListener('keydown', f)
    return () => removeEventListener('keydown', f)
  }, [seleccionar])
  if (!sel) return null
  const id = String(sel.id)
  return (
    <aside className="panel" aria-label={t('panel.titulo')}>
      <button className="cerrar" aria-label={t('panel.cerrar')} onClick={() => seleccionar(null)}>×</button>
      <Miga />
      {aviso && <p role="status" className="etiqueta">{aviso}</p>}
      <h2>{nombreUnidad(sel.nombre, !!sel.disputa)}</h2>
      <p className="etiqueta">{sel.disputa ? t('unidad.disputa') : NOMBRE_NIVEL[sel.nivel]}{sel.nivel === 0 || sel.disputa ? '' : ` · ${sel.pais}`}</p>
      <div role="tablist" className="pestanas" onKeyDown={(e) => {
        const i = PESTANAS.indexOf(activa), d = e.key === 'ArrowRight' ? 1 : e.key === 'ArrowLeft' ? -1 : 0
        if (d) setTab(PESTANAS[(i + d + PESTANAS.length) % PESTANAS.length])
      }}>
        {PESTANAS.map((p) => (
          <button key={p} role="tab" aria-selected={p === activa} tabIndex={p === activa ? 0 : -1} onClick={() => setTab(p)}>{p}</button>
        ))}
      </div>
      <div role="tabpanel" className="pestana">
        {activa === 'Resumen' && <Resumen id={id} />}
        {activa === 'Series' && <Series id={id} />}
        {activa === 'Suelo' && <Suelo id={id} />}
        {activa === 'Rotaciones' && (errRot ? <p role="alert">{t('panel.errRotaciones')}</p> : rot ? <Rotaciones resp={rot} /> : <p role="status">{t('comun.cargando')}</p>)}
        {activa === 'Lotes' && <Lotes id={id} />}
        {activa === 'Fuentes' && <Fuentes />}
      </div>
    </aside>
  )
}
