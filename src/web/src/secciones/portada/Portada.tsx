// asistido por SI: Claude Code (Anthropic), entrada #/ rediseñada (R1): mapa de puntos, halo, raíces orgánicas con savia, nodos con volumen y Start con brillo
import { useEffect, useState, type ComponentType } from 'react'
import { aHash, type Seccion } from '../../app/ruta'
import { t, useIdioma, type ClaveTodo } from '../../textos/i18n'
import { IconoGlobo, IconoLote, IlustracionCiencia, IlustracionDatos, IlustracionFuentes, IlustracionRotaciones } from './iconos'
import './portada.css'

type Nodo = { seccion: Seccion; x: number; y: number; icono: ComponentType; imagen?: string }

// Orden del reloj desde arriba a la izquierda: es el orden de tabulación. x, y en el lienzo 1000 × 600
export const NODOS: Nodo[] = [
  { seccion: 'tierra', x: 190, y: 120, icono: IconoGlobo, imagen: 'portada/globo.webp' },
  { seccion: 'lote', x: 810, y: 120, icono: IconoLote, imagen: 'lotes/bloque_DEMO-COL-01.webp' },
  { seccion: 'rotaciones', x: 880, y: 305, icono: IlustracionRotaciones },
  { seccion: 'ciencia', x: 810, y: 490, icono: IlustracionCiencia },
  { seccion: 'datos', x: 190, y: 490, icono: IlustracionDatos },
  { seccion: 'fuentes', x: 120, y: 305, icono: IlustracionFuentes },
]
const CX = 500, CY = 300

// Generador determinista: la misma figura en cada carga y en las capturas
function azar(semilla: number) {
  let s = semilla >>> 0
  return () => { s = (s * 1664525 + 1013904223) >>> 0; return s / 4294967296 }
}
type P2 = [number, number]
const bez = (p: P2[], u: number): P2 => {
  const a = 1 - u
  return [a * a * a * p[0][0] + 3 * a * a * u * p[1][0] + 3 * a * u * u * p[2][0] + u * u * u * p[3][0],
    a * a * a * p[0][1] + 3 * a * a * u * p[1][1] + 3 * a * u * u * p[2][1] + u * u * u * p[3][1]]
}
const tangente = (p: P2[], u: number): P2 => {
  const a = bez(p, Math.max(0, u - 0.01)), b = bez(p, Math.min(1, u + 0.01)), l = Math.hypot(b[0] - a[0], b[1] - a[1]) || 1
  return [(b[0] - a[0]) / l, (b[1] - a[1]) / l]
}
const trazo = (p: P2[]) => `M${p[0][0].toFixed(1)} ${p[0][1].toFixed(1)} C ${p.slice(1).map((q) => `${q[0].toFixed(1)} ${q[1].toFixed(1)}`).join(' ')}`

// Hoja con la base en (0,0) apuntando a +x; se coloca con translate, rotate y scale
const HOJA = 'M0 0 C 6 -7 16 -7 24 0 C 16 7 6 7 0 0 Z'

export interface Raiz { principal: P2[]; hebra: P2[]; ramas: string[]; hojas: { x: number; y: number; a: number; s: number; r: number }[] }

/** Raíz del anillo del centro al nodo: tronco curvo, ramas que se abren, ramitas y hojas. */
export function construirRaiz(n: Nodo, i: number): Raiz {
  const r = azar(97 + i * 131)
  const ang = Math.atan2(n.y - CY, n.x - CX)
  const S: P2 = [CX + Math.cos(ang) * 222, CY + Math.sin(ang) * 138]
  const dist = Math.hypot(n.x - S[0], n.y - S[1])
  const E: P2 = [n.x - ((n.x - S[0]) / dist) * 62, n.y - ((n.y - S[1]) / dist) * 62]
  const v: P2 = [E[0] - S[0], E[1] - S[1]], perp: P2 = [-v[1] / dist, v[0] / dist]
  const w1 = (r() - 0.5) * 70, w2 = (r() - 0.5) * 70
  const principal: P2[] = [S, [S[0] + v[0] * 0.35 + perp[0] * w1, S[1] + v[1] * 0.35 + perp[1] * w1], [S[0] + v[0] * 0.7 - perp[0] * w2, S[1] + v[1] * 0.7 - perp[1] * w2], E]
  const ramas: string[] = [], hojas: Raiz['hojas'] = []
  // Las ramas nacen lejos del título para no taparlo
  ;[0.36, 0.52, 0.68, 0.84].forEach((u, k) => {
    const o = bez(principal, u), tg = tangente(principal, u), lado = k % 2 ? 1 : -1
    const giro = lado * (0.55 + r() * 0.35), largo = 44 + r() * 38
    const dir: P2 = [tg[0] * Math.cos(giro) - tg[1] * Math.sin(giro), tg[0] * Math.sin(giro) + tg[1] * Math.cos(giro)]
    const fin: P2 = [o[0] + dir[0] * largo, o[1] + dir[1] * largo]
    ramas.push(trazo([o, [o[0] + tg[0] * largo * 0.4, o[1] + tg[1] * largo * 0.4], [fin[0] - dir[0] * largo * 0.3 + tg[0] * 6, fin[1] - dir[1] * largo * 0.3 + tg[1] * 6], fin]))
    // Ramita secundaria desde la mitad de la rama
    const m: P2 = [(o[0] + fin[0]) / 2, (o[1] + fin[1]) / 2]
    const fin2: P2 = [m[0] + (dir[0] * 0.6 - lado * dir[1] * 0.8) * 18, m[1] + (dir[1] * 0.6 + lado * dir[0] * 0.8) * 18]
    ramas.push(trazo([m, [m[0] + dir[0] * 6, m[1] + dir[1] * 6], [fin2[0] - dir[0] * 4, fin2[1] - dir[1] * 4], fin2]))
    const a = (Math.atan2(dir[1], dir[0]) * 180) / Math.PI
    hojas.push({ x: fin[0], y: fin[1], a, s: 0.7 + r() * 0.4, r: r() }, { x: fin2[0], y: fin2[1], a: a - lado * 40, s: 0.45 + r() * 0.25, r: r() })
    // Hojita sobre el tronco
    const ot = bez(principal, u + 0.08), tt = tangente(principal, u + 0.08)
    hojas.push({ x: ot[0], y: ot[1], a: (Math.atan2(tt[1], tt[0]) * 180) / Math.PI - lado * 60, s: 0.4 + r() * 0.2, r: r() })
  })
  // Segunda hebra que se separa del tronco y vuelve: da cuerpo orgánico sin tapar el título
  const sep = 9 + r() * 6
  const hebra: P2[] = [principal[0], [principal[1][0] + perp[0] * sep * 2, principal[1][1] + perp[1] * sep * 2], [principal[2][0] - perp[0] * sep * 1.4, principal[2][1] - perp[1] * sep * 1.4], principal[3]]
  return { principal, hebra, ramas, hojas }
}
const RAICES = NODOS.map(construirRaiz)

function useMovimientoReducido() {
  const consulta = '(prefers-reduced-motion: reduce)'
  const [reducido, setReducido] = useState(() => typeof matchMedia === 'function' && matchMedia(consulta).matches)
  useEffect(() => {
    if (typeof matchMedia !== 'function') return
    const m = matchMedia(consulta), f = () => setReducido(m.matches)
    m.addEventListener('change', f)
    return () => m.removeEventListener('change', f)
  }, [])
  return reducido
}

// Marcas del anillo de circuito alrededor del título
const MARCAS = Array.from({ length: 36 }, (_, k) => (k * Math.PI * 2) / 36)

function Raices({ reducido }: { reducido: boolean }) {
  return (
    <svg className="raices" viewBox="0 0 1000 600" preserveAspectRatio="xMidYMid meet" aria-hidden="true" focusable="false">
      <defs>
        <linearGradient id="g-tallo" x1="0" x2="1"><stop offset="0" stopColor="#3f9c63" /><stop offset="1" stopColor="#9df5b8" /></linearGradient>
        <linearGradient id="g-hoja" x1="0" x2="1"><stop offset="0" stopColor="#2f8a52" /><stop offset="0.6" stopColor="#6fe39a" /><stop offset="1" stopColor="#c7ffd8" /></linearGradient>
        <radialGradient id="g-halo"><stop offset="0.55" stopColor="#5ee08f" stopOpacity="0" /><stop offset="0.8" stopColor="#5ee08f" stopOpacity="0.18" /><stop offset="1" stopColor="#5ee08f" stopOpacity="0" /></radialGradient>
        <filter id="f-brillo" x="-20%" y="-20%" width="140%" height="140%"><feGaussianBlur stdDeviation="3.5" /></filter>
      </defs>
      <g className="halo">
        <ellipse className="halo-luz" cx={CX} cy={CY} rx="250" ry="168" fill="url(#g-halo)" />
        <ellipse className="anillo anillo-ext" cx={CX} cy={CY} rx="214" ry="134" />
        <ellipse className="anillo anillo-int" cx={CX} cy={CY} rx="196" ry="122" />
        <g className="circuito">
          {MARCAS.map((a, k) => {
            const largo = k % 3 ? 1.045 : 1.1
            const x1 = CX + Math.cos(a) * 214, y1 = CY + Math.sin(a) * 134, x2 = CX + Math.cos(a) * 214 * largo, y2 = CY + Math.sin(a) * 134 * largo
            return <g key={k}><line x1={x1} y1={y1} x2={x2} y2={y2} />{k % 3 === 0 && <circle cx={x2} cy={y2} r="2.2" />}</g>
          })}
        </g>
      </g>
      {RAICES.map((r, i) => (
        <g key={NODOS[i].seccion} className="raiz-grupo" style={{ ['--i' as string]: i }}>
          <path className="raiz-brillo" d={trazo(r.principal)} filter="url(#f-brillo)" />
          <path className="raiz" pathLength={1} d={trazo(r.principal)} />
          <path className="raiz-luz" pathLength={1} d={trazo(r.principal)} />
          <path className="hebra" pathLength={1} d={trazo(r.hebra)} />
          {r.ramas.map((rd, k) => <path key={k} className="rama" pathLength={1} d={rd} style={{ ['--k' as string]: k }} />)}
          {r.hojas.map((h, k) => (
            <g key={`h${k}`} transform={`translate(${h.x.toFixed(1)} ${h.y.toFixed(1)}) rotate(${h.a.toFixed(0)}) scale(${h.s.toFixed(2)})`}>
              <path className="hoja-r" d={HOJA} style={{ ['--r' as string]: h.r.toFixed(2) }} />
            </g>
          ))}
          {/* Savia luminosa que viaja hacia el nodo; con movimiento reducido no se dibuja */}
          {!reducido && [0, 1].map((k) => (
            <circle key={`s${k}`} className="savia" r="2.4" opacity="0">
              <animateMotion dur={`${3.2 + i * 0.25}s`} begin={`${1.6 + k * 1.7 + i * 0.3}s`} repeatCount="indefinite" path={trazo(r.principal)} />
              {/* Invisible hasta que arranca y se apaga al llegar: nunca se ve quieta en el origen */}
              <animate attributeName="opacity" values="0;1;1;0" keyTimes="0;0.1;0.85;1" dur={`${3.2 + i * 0.25}s`} begin={`${1.6 + k * 1.7 + i * 0.3}s`} repeatCount="indefinite" />
            </circle>
          ))}
        </g>
      ))}
    </svg>
  )
}

// Si la imagen no carga (o aún no existe) el nodo cae a su ícono SVG
function Figura({ nodo }: { nodo: Nodo }) {
  const [fallo, setFallo] = useState(false)
  const Icono = nodo.icono
  if (!nodo.imagen || fallo) return <Icono />
  return <img className="figura-nodo" src={`${import.meta.env.BASE_URL}${nodo.imagen}`} alt="" width={128} height={128} decoding="async" onError={() => setFallo(true)} />
}

export function Portada() {
  useIdioma()
  const reducido = useMovimientoReducido()
  return (
    <main className="portada">
      <div className="mapa-puntos" aria-hidden="true" style={{ backgroundImage: `url(${import.meta.env.BASE_URL}portada/mundo_puntos.svg)` }} />
      <div className="lienzo">
        <Raices reducido={reducido} />
        <div className="p-centro">
          <h1>AGROVERSEx</h1>
          <p>{t('portada.universo')}</p>
          <p>{t('portada.universo_2')}</p>
        </div>
        <nav className="nodos" aria-label={t('portada.nodos')}>
          {NODOS.map((n, i) => (
            <a key={n.seccion} className="nodo" data-nodo={n.seccion} href={aHash({ seccion: n.seccion, params: {} })}
              style={{ left: `${n.x / 10}%`, top: `${n.y / 6}%`, ['--i' as string]: i }}>
              <div className="figura" aria-hidden="true"><Figura nodo={n} /></div>
              <span>{t(`portada.nodo.${n.seccion}` as ClaveTodo)}</span>
            </a>
          ))}
        </nav>
      </div>
      <a className="boton-principal comenzar" href={aHash({ seccion: 'tierra', params: {} })}>{t('portada.comenzar')}</a>
    </main>
  )
}
