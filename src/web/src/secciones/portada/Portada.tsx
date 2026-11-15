// asistido por SI: Claude Code (Anthropic), entrada #/: marca, frase del universo, raíces hacia las seis secciones y Start (plan v2 §2)
import { useState, type ComponentType } from 'react'
import { aHash, type Seccion } from '../../app/ruta'
import { t, useIdioma, type ClaveTodo } from '../../textos/i18n'
import { IconoCiencia, IconoDatos, IconoFuentes, IconoGlobo, IconoLote, IconoRotaciones } from './iconos'
import './portada.css'

type Nodo = { seccion: Seccion; x: number; y: number; icono: ComponentType; imagen?: string }

// Orden del reloj desde arriba a la izquierda: es el orden de tabulación. x, y en el lienzo 1000 × 600
export const NODOS: Nodo[] = [
  { seccion: 'tierra', x: 190, y: 110, icono: IconoGlobo, imagen: 'portada/globo.webp' },
  { seccion: 'lote', x: 810, y: 110, icono: IconoLote, imagen: 'lotes/bloque_DEMO-COL-01.webp' },
  { seccion: 'rotaciones', x: 880, y: 300, icono: IconoRotaciones },
  { seccion: 'ciencia', x: 810, y: 490, icono: IconoCiencia },
  { seccion: 'datos', x: 190, y: 490, icono: IconoDatos },
  { seccion: 'fuentes', x: 120, y: 300, icono: IconoFuentes },
]
const CX = 500, CY = 300

// Raíz curva desde el anillo del centro hasta el nodo; nace fuera del texto para no restarle contraste
const inicio = ({ x, y }: Nodo) => [CX + Math.sign(x - CX) * 235, CY + (y - CY) * 0.3]
function raiz(n: Nodo) {
  const { x, y } = n
  const [x0, y0] = inicio(n)
  const mx = (x0 + x) / 2
  return `M${x0} ${y0} C ${mx} ${y0} ${mx} ${y} ${x} ${y}`
}
function hojas(n: Nodo, i: number) {
  const [x0, y0] = inicio(n)
  const px = (x0 + n.x) / 2, py = (y0 + n.y) / 2
  const s = i % 2 ? -1 : 1
  return `M${px} ${py} q ${8 * s} -16 ${22 * s} -14 q -6 14 -22 14 Z M${n.x - (n.x - x0) * 0.2} ${n.y} q ${-6 * s} 16 ${-20 * s} 16 q 4 -14 20 -16 Z`
}

function Raices() {
  return (
    <svg className="raices" viewBox="0 0 1000 600" preserveAspectRatio="xMidYMid meet" aria-hidden="true" focusable="false">
      <circle className="nucleo" cx={CX} cy={CY} r="250" />
      {NODOS.map((n, i) => (
        <g key={n.seccion}>
          <path className="raiz" pathLength={1} d={raiz(n)} />
          <path className="hojita" d={hojas(n, i)} />
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
  return <img className="figura-nodo" src={`${import.meta.env.BASE_URL}${nodo.imagen}`} alt="" width={112} height={112} decoding="async" onError={() => setFallo(true)} />
}

export function Portada() {
  useIdioma()
  return (
    <main className="portada">
      <div className="lienzo">
        <Raices />
        <div className="centro">
          <h1>AGROVERSEx</h1>
          <p>{t('portada.universo')}</p>
          <p>{t('portada.universo_2')}</p>
        </div>
        <nav className="nodos" aria-label={t('portada.nodos')}>
          {NODOS.map((n) => (
            <a key={n.seccion} className="nodo" data-nodo={n.seccion} href={aHash({ seccion: n.seccion, params: {} })}
              style={{ left: `${n.x / 10}%`, top: `${n.y / 6}%` }}>
              <Figura nodo={n} />
              <span>{t(`portada.nodo.${n.seccion}` as ClaveTodo)}</span>
            </a>
          ))}
        </nav>
      </div>
      <a className="boton-principal comenzar" href={aHash({ seccion: 'tierra', params: {} })}>{t('portada.comenzar')}</a>
    </main>
  )
}
