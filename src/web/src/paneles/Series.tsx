// asistido por SI: Claude Code (Anthropic), escritura y revisión de código; base del prototipo migrada en el hackatón
import { useEffect, useState } from 'react'
import { BandaSerie } from '../graficos/BandaSerie'
import { anomalia, nombreVar, pedirSerie, tendencia, type RespSerie, type Num } from '../datos/series'
import { paraMostrar } from '../comun/unidades'
import { Chip } from './Chip'
import { CAPAS } from '../datos/capas'
import { useEstado } from '../app/estado'

const VARS = CAPAS.map((c) => c.id)
const CAMBIOS = [{ mes: 180, texto: 'GLDAS → SMAP' }] // ene-2015
const fmt = (x: number) => x.toFixed(3)

export function Series({ id }: { id: string }) {
  const [v, setV] = useState(useEstado.getState().capa)
  const [anom, setAnom] = useState(false)
  const [r, setR] = useState<RespSerie | null>(null)
  const [err, setErr] = useState(false)
  useEffect(() => { setR(null); setErr(false); pedirSerie(id, VARS).then(setR).catch(() => setErr(true)) }, [id])
  const s = r?.series[v]
  if (err) return <p role="status">No se pudo cargar la serie.</p>
  if (!s) return <p role="status">Cargando serie…</p>
  const cv = (a?: Num[]) => a?.map((x, i) => paraMostrar(v, x, s.unidad_medida, i).valor)
  let valor = cv(s.valor)!, p10 = cv(s.p10), p90 = cv(s.p90)
  const unidad = paraMostrar(v, null, s.unidad_medida, 0).unidad
  if (anom) { valor = anomalia(valor, 0, 191); p10 = undefined; p90 = undefined }
  const t = tendencia(valor)
  const ok = valor.filter((x) => x !== null).length
  return (
    <div>
      <label>Variable <select value={v} onChange={(e) => setV(e.target.value)}>{VARS.map((x) => <option key={x} value={x}>{nombreVar(x)}</option>)}</select></label>
      <label><input type="checkbox" checked={anom} onChange={(e) => setAnom(e.target.checked)} /> Anomalía vs 2000-2015</label>
      <BandaSerie valor={valor} p10={p10} p90={p90} variable={v} unidad={unidad} cambiosFuente={CAMBIOS} />
      <p className="etiqueta"><Chip e="SIMULADO" /> {ok} de {valor.length} meses con dato; huecos sin interpolar. Banda p10–p90 {p10 ? 'del producto' : 'no disponible'}.</p>
      <p className="etiqueta">Tendencia: {fmt(t.pendiente * 12)} {unidad}/año (IC 95 % {fmt(t.ic[0] * 12)} a {fmt(t.ic[1] * 12)})</p>
    </div>
  )
}
