// asistido por SI: Claude Code (Anthropic), escritura y revisión de código; base del prototipo migrada en el hackatón
import { useEffect, useState } from 'react'
import { clienteDefecto } from '../datos/consultas'
import type { Meta } from '../datos/tipos'
import { Chip } from './Chip'
import { t } from '../textos/i18n'

// La tabla fuente guarda identificadores; aquí van el nombre legible y si el dato es real o imitado
const NOMBRE: Record<string, string> = {
  soilgrids2: 'SoilGrids 2.0', gmted2010: 'GMTED2010', koppen_beck2023: 'Köppen-Geiger (Beck et al. 2023)',
  'EV-AGU': 'Productos de agua que se imitan (SMAP, IMERG, GRACE, GLDAS)', 'EV-VEG': 'Productos de vegetación que se imitan (MODIS, HLS)',
  'EV-SUE': 'Referencias de suelo', demo: 'Simulación AGROVERSEx',
}
const REAL = /^(soilgrids|gmted|koppen)/

export function Fuentes() {
  const [m, setM] = useState<Meta | null>(null)
  useEffect(() => { clienteDefecto.meta().then(setM).catch(() => {}) }, [])
  if (!m) return <p role="status">{t('comun.cargando')}</p>
  return (
    <div>
      {m.fuentes.map((f, i) => (
        <details key={i}>
          <summary>{NOMBRE[String(f.id)] ?? String(f.nombre ?? f.producto ?? f.id ?? `fuente ${i + 1}`)} <Chip e={REAL.test(String(f.id)) ? 'real_contexto' : String(f.etiqueta ?? '')} /></summary>
          <dl>{Object.entries(f).filter(([, v]) => v !== null).map(([k, v]) => <div key={k}><dt>{k}</dt><dd>{String(v)}</dd></div>)}</dl>
        </details>
      ))}
      <p className="etiqueta">{t('fuentes.climatologia')}</p>
      <p className="etiqueta">{m.rotulo_estatico}</p>
    </div>
  )
}
