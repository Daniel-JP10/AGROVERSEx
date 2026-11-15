// asistido por SI: Claude Code, fuentes reales de las variables pintadas (T-D9)
import { useEffect, useState } from 'react'
import { cargarMatriz, textoEstado, type ProductoMes } from '../datos/estatico'
import { CAPAS } from '../datos/capas'
import { t } from '../textos/i18n'

export function Fuentes() {
  const [f, setF] = useState<{ id: string; nombre: string; productos: ProductoMes[] }[] | null>(null)
  useEffect(() => {
    Promise.all(CAPAS.map((c) => cargarMatriz(c.id, 0).then((m) => ({ id: c.id, nombre: c.nombre, productos: m.productos })))).then(setF).catch(() => {})
  }, [])
  if (!f) return <p role="status">{t('comun.cargando')}</p>
  return (
    <div>
      {f.map((v) => (
        <details key={v.id}>
          <summary>{v.nombre}</summary>
          {v.productos.map((p) => (
            <dl key={p.producto}>
              <div><dt>{t('globo.producto')}</dt><dd>{p.producto}</dd></div>
              <div><dt>version</dt><dd>{p.version}</dd></div>
              <div><dt>{t('globo.estado')}</dt><dd>{textoEstado(p.estado)}</dd></div>
              <div><dt>unit</dt><dd>{p.unidad}</dd></div>
            </dl>
          ))}
        </details>
      ))}
      <p className="etiqueta">{t('fuentes.ponderacion')}</p>
      <p className="etiqueta">{t('fuentes.fondo')}</p>
    </div>
  )
}
