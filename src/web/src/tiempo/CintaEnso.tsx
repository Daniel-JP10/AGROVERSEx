// asistido por SI: Claude Code (Anthropic), escritura y revisión de código; base del prototipo migrada en el hackatón
import { useEffect, useState } from 'react'
import { N_MESES } from './valor'
import { mesIdAEtiqueta, mesesConHueco, type Producto } from './huecos'

export interface PuntoEnso { mes: number; roni: number }
export interface Evento { mes: number; nombre: string }
export interface DatosCinta { enso: PuntoEnso[]; eventos: Evento[] }

/** RONI real de /api/enso ([{mes_id, oni, roni}]) y eventos globales de /api/eventos (inicio y fin son años: el marcador va en enero del año de inicio). */
export async function cargarCinta(f: typeof fetch = fetch): Promise<DatosCinta> {
  const pedir = async (u: string) => { try { const r = await f(u); const j = r.ok ? await r.json() : null; return Array.isArray(j) ? j : [] } catch { return [] } }
  const [enso, ev] = await Promise.all([pedir('/api/enso'), pedir('/api/eventos')])
  return {
    enso: enso.map((r: { mes_id: number; roni: number }) => ({ mes: r.mes_id, roni: r.roni })),
    eventos: ev.map((e: { tipo: string; inicio: number; fin: number; region_texto: string }) => ({ mes: (e.inicio - 2000) * 12, nombre: `${e.tipo} · ${e.region_texto} (${e.inicio === e.fin ? e.inicio : `${e.inicio}-${e.fin}`})` })),
  }
}

const H = 40
export function CintaEnso({ producto, mes }: { producto: Producto; mes: number }) {
  const [d, setD] = useState<DatosCinta | null>(null)
  useEffect(() => { void cargarCinta().then(setD) }, [])
  const x = (m: number) => m + 0.5
  const y = (r: number) => H / 2 - (r / 3) * (H / 2)
  const linea = d?.enso.map((p) => `${x(p.mes)},${y(p.roni)}`).join(' ')
  return (
    <div className="cinta">
      <svg viewBox={`0 0 ${N_MESES} ${H}`} preserveAspectRatio="none" role="img" aria-label={`RONI, eventos y meses sin dato de ${producto.nombre}`}>
        {mesesConHueco(producto).map((m) => <rect key={m} className="hueco" x={m} y={0} width={1} height={H} />)}
        {(producto.parciales ?? []).map((m) => <rect key={m} className="parcial" x={m} y={0} width={1} height={H} />)}
        {producto.provisionalDesde !== undefined && <rect className="prov" x={producto.provisionalDesde} y={H - 4} width={N_MESES - producto.provisionalDesde} height={4} />}
        <line className="cero" x1={0} x2={N_MESES} y1={H / 2} y2={H / 2} />
        {linea && <polyline className="roni" points={linea} vectorEffect="non-scaling-stroke" />}
        {d?.eventos.map((e, i) => <line key={i} className="evento" x1={x(e.mes)} x2={x(e.mes)} y1={0} y2={H} vectorEffect="non-scaling-stroke"><title>{`${e.nombre} · ${mesIdAEtiqueta(e.mes)}`}</title></line>)}
        <line className="cursor" x1={x(mes)} x2={x(mes)} y1={0} y2={H} vectorEffect="non-scaling-stroke" />
      </svg>
      <small>{d && !d.enso.length ? 'RONI: sin dato' : 'RONI (°C) real'} · eventos de la tabla evento (marcador en el año de inicio) · gris: sin dato de {producto.nombre}</small>
    </div>
  )
}
