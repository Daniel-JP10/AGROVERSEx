// asistido por SI: Claude Code (Anthropic), escritura y revisión de código; base del prototipo migrada en el hackatón
import { useEffect, useState } from 'react'
import { useEstado } from '../app/estado'
import { migaDe, type UnidadMiga } from '../datos/busqueda'
import { claveUnidad, porClave } from '../datos/indice'

// País › Departamento › Unidad, con padre_id e iso3 de /api/unidad/:id
export function Miga() {
  const sel = useEstado((s) => s.seleccion)
  const seleccionar = useEstado((s) => s.seleccionar)
  const [pasos, setPasos] = useState<{ id: string; nombre: string; nivel: number }[]>([])

  useEffect(() => {
    if (!sel) return setPasos([])
    const id = String(sel.id)
    const un = new Map<string, UnidadMiga>()
    const pais = porClave.get(claveUnidad(0, sel.pais_id ?? id))
    if (pais) un.set(String(pais.id), { padre_id: null, iso3: String(pais.id), nombre: pais.nombre, nivel: 0 })
    // Sin API el departamento sale del ctx del índice ("Meta · Colombia"); sin id, no es botón
    const dep = sel.nivel === 2 ? sel.pais.split(' · ')[0] : ''
    const depU = dep ? [...porClave.values()].find((x) => x.nivel === 1 && x.nombre === dep && x.pais === pais?.nombre) : undefined
    const kd = depU ? String(depU.id) : '~dep'
    if (dep && dep !== pais?.nombre) un.set(kd, { padre_id: null, iso3: String(sel.pais_id), nombre: dep, nivel: 1 })
    un.set(id, { padre_id: dep && un.has(kd) ? kd : null, iso3: String(sel.pais_id ?? id), nombre: sel.nombre, nivel: sel.nivel })
    setPasos(migaDe(id, un)) // vista provisoria sin API
    let vivo = true
    fetch(`/api/unidad/${encodeURIComponent(id)}`).then((r) => (r.ok ? r.json() : Promise.reject(r.status))).then((d) => {
      if (!vivo) return
      const u = d.unidad
      if (d.padre) un.set(d.padre.id, { padre_id: d.padre.nivel > 0 ? u.iso3 : null, iso3: u.iso3, nombre: d.padre.nombre, nivel: d.padre.nivel })
      un.set(id, { padre_id: u.padre_id, iso3: u.iso3, nombre: u.nombre, nivel: u.nivel })
      setPasos(migaDe(id, un))
    }).catch(() => {})
    return () => { vivo = false }
  }, [sel])

  return (
    <nav className="miga" aria-label="Ubicación">
      {pasos.map((p, i) => {
        const u = porClave.get(claveUnidad(p.nivel, p.id))
        return i === pasos.length - 1 || !u
          ? <span key={p.id} aria-current={i === pasos.length - 1 ? 'page' : undefined}>{i > 0 && ' › '}{p.nombre}</span>
          : <span key={p.id}>{i > 0 && ' › '}<button onClick={() => seleccionar(u)}>{p.nombre}</button></span>
      })}
    </nav>
  )
}
