// asistido por SI: Claude Code (Anthropic), escritura y revisión de código; base del prototipo migrada en el hackatón
import { useEffect, useState } from 'react'
import { useEstado } from '../app/estado'
import { migaDe, type UnidadMiga } from '../datos/busqueda'
import { claveUnidad, porClave } from '../datos/indice'
import { cargarGeo, nivelDeUnidad } from '../datos/estatico'
import { nombreUnidad } from '../globo/config'
import { t } from '../textos/i18n'

// País › Departamento › Unidad, con el padre_id de unidades_geo (archivo estático)
export function Miga() {
  const sel = useEstado((s) => s.seleccion)
  const seleccionar = useEstado((s) => s.seleccionar)
  const [pasos, setPasos] = useState<{ id: string; nombre: string; nivel: number }[]>([])

  useEffect(() => {
    if (!sel) return setPasos([])
    let vivo = true
    cargarGeo().then((geo) => {
      if (!vivo) return
      const un = new Map<string, UnidadMiga>()
      // sube por padre_id; sin padre válido, al país por iso3 (contratos/unidades.md: cruce_ambiguo)
      let k: string | null = String(sel.id)
      for (let i = 0; k && i < 3; i++) {
        const u = porClave.get(claveUnidad(nivelDeUnidad(k), k))
        if (!u) break
        const iso = String(u.pais_id ?? u.id).split('-')[0]
        const padre: string | null = u.nivel === 0 ? null : (geo[k]?.[4] ?? `${iso}-ADM0`)
        un.set(k, { padre_id: padre, iso3: iso, nombre: u.nombre, nivel: u.nivel })
        k = padre
      }
      setPasos(migaDe(String(sel.id), un))
    }).catch(() => setPasos([{ id: String(sel.id), nombre: sel.nombre, nivel: sel.nivel }]))
    return () => { vivo = false }
  }, [sel])

  return (
    <nav className="miga" aria-label={t('miga.ubicacion')}>
      {pasos.map((p, i) => {
        const u = porClave.get(claveUnidad(p.nivel, p.id))
        return i === pasos.length - 1 || !u
          ? <span key={p.id} aria-current={i === pasos.length - 1 ? 'page' : undefined}>{i > 0 && ' › '}{nombreUnidad(p.nombre, !!u?.disputa)}</span>
          : <span key={p.id}>{i > 0 && ' › '}<button onClick={() => seleccionar(u)}>{nombreUnidad(p.nombre, !!u.disputa)}</button></span>
      })}
    </nav>
  )
}
