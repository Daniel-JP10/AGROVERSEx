// asistido por SI: Claude Code (Anthropic), íconos e ilustraciones SVG propios de los nodos de la entrada (R1: volumen, gradientes y brillo; sin recursos de terceros)
// Todos van dentro de un enlace con texto visible: el dibujo es decoración (aria-hidden)
import hlsUsa from '../../../../../datos/lotes/hls_validez_DEMO-USA-01.json'

const P = { viewBox: '0 0 64 64', 'aria-hidden': true, focusable: false, className: 'icono-nodo' } as const
const I = { viewBox: '0 0 120 120', 'aria-hidden': true, focusable: false, className: 'ilustracion' } as const

// Respaldo de línea cuando no carga la imagen del globo o del bloque
export const IconoGlobo = () => (
  <svg {...P}><circle cx="32" cy="32" r="22" /><path d="M10 32 H54 M32 10 C 22 20 22 44 32 54 M32 10 C 42 20 42 44 32 54 M14 21 C 24 25 40 25 50 21 M14 43 C 24 39 40 39 50 43" /></svg>
)
export const IconoLote = () => (
  <svg {...P}><path d="M8 26 L32 14 L56 26 L32 38 Z" /><path d="M8 26 V38 L32 50 L56 38 V26 M32 38 V50" /><path d="M16 26 L36 16 M24 30 L44 20 M30 34 L50 24" /></svg>
)

// Ciclo de tres flechas con volumen alrededor de un brote sobre suelo y una gota
export const IlustracionRotaciones = () => (
  <svg {...I}>
    <defs>
      <linearGradient id="ro-a" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stopColor="#b8ffcf" /><stop offset="1" stopColor="#2e9b5c" /></linearGradient>
      <linearGradient id="ro-b" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stopColor="#a8f3ff" /><stop offset="1" stopColor="#2a8fa3" /></linearGradient>
      <linearGradient id="ro-c" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stopColor="#ffe2a8" /><stop offset="1" stopColor="#c27a1f" /></linearGradient>
      <radialGradient id="ro-suelo" cx="0.5" cy="0.3"><stop offset="0" stopColor="#8a6340" /><stop offset="1" stopColor="#3e2a18" /></radialGradient>
      <linearGradient id="ro-hoja" x1="0" x2="1"><stop offset="0" stopColor="#2f8a52" /><stop offset="1" stopColor="#9df5b8" /></linearGradient>
      <linearGradient id="ro-gota" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stopColor="#c9f6ff" /><stop offset="1" stopColor="#2c86c9" /></linearGradient>
    </defs>
    <path d="M60 14 A46 46 0 0 1 102 44" fill="none" stroke="url(#ro-a)" strokeWidth="9" strokeLinecap="round" />
    <path d="M96 38 L106 48 L110 34 Z" fill="#9df5b8" />
    <path d="M104 72 A46 46 0 0 1 52 105" fill="none" stroke="url(#ro-b)" strokeWidth="9" strokeLinecap="round" />
    <path d="M58 98 L46 106 L58 112 Z" fill="#7fdcef" />
    <path d="M22 88 A46 46 0 0 1 36 22" fill="none" stroke="url(#ro-c)" strokeWidth="9" strokeLinecap="round" />
    <path d="M30 28 L42 18 L44 32 Z" fill="#f2c477" />
    <ellipse cx="60" cy="78" rx="24" ry="8" fill="url(#ro-suelo)" />
    <path d="M60 76 C 60 66 60 58 60 50" stroke="#4fbf7a" strokeWidth="2.6" fill="none" strokeLinecap="round" />
    <path d="M60 60 C 48 58 44 48 46 42 C 56 44 60 50 60 60 Z" fill="url(#ro-hoja)" />
    <path d="M60 55 C 70 52 76 44 74 36 C 64 38 60 46 60 55 Z" fill="url(#ro-hoja)" />
    <path d="M86 62 C 82 68 80 72 80 75 A6 6 0 0 0 92 75 C 92 72 90 68 86 62 Z" fill="url(#ro-gota)" />
  </svg>
)

// Fracción de observaciones HLS válidas por mes, lote DEMO-USA-01, 2022-2024
// Archivo y campo: datos/lotes/hls_validez_DEMO-USA-01.json · meses.<YYYY-MM>.media (sin cifras escritas en la figura)
export const BARRAS_HLS: number[] = Object.keys(hlsUsa.meses).sort().map((m) => (hlsUsa.meses as Record<string, { media: number }>)[m].media)

export const IlustracionCiencia = () => (
  <svg {...I} data-fuente="datos/lotes/hls_validez_DEMO-USA-01.json · meses.*.media">
    <defs>
      <linearGradient id="ci-panel" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stopColor="#1d3a2c" stopOpacity="0.95" /><stop offset="1" stopColor="#0b1a13" stopOpacity="0.95" /></linearGradient>
      <linearGradient id="ci-borde" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stopColor="#b8ffcf" /><stop offset="1" stopColor="#2e9b5c" /></linearGradient>
      <linearGradient id="ci-barra" x1="0" y1="1" x2="0" y2="0"><stop offset="0" stopColor="#2e9b5c" /><stop offset="1" stopColor="#c7ffd8" /></linearGradient>
      <linearGradient id="ci-lupa" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stopColor="#e9fff1" stopOpacity="0.5" /><stop offset="1" stopColor="#7be0a0" stopOpacity="0.1" /></linearGradient>
    </defs>
    <rect x="8" y="18" width="104" height="80" rx="10" fill="url(#ci-panel)" stroke="url(#ci-borde)" strokeWidth="2" />
    <path d="M16 88 H104" stroke="#3f6b55" strokeWidth="1" />
    {BARRAS_HLS.map((v, k) => {
      const h = Math.max(1.5, v * 62)
      return <rect key={k} x={17 + k * 2.4} y={88 - h} width="1.7" height={h} rx="0.6" fill="url(#ci-barra)" />
    })}
    <circle cx="92" cy="34" r="13" fill="url(#ci-lupa)" stroke="#d9ffe6" strokeWidth="3" />
    <path d="M101 43 L112 54" stroke="#d9ffe6" strokeWidth="5" strokeLinecap="round" />
  </svg>
)

// Nube con base de datos apilada y flechas de descarga
export const IlustracionDatos = () => (
  <svg {...I}>
    <defs>
      <linearGradient id="da-nube" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stopColor="#e6fbff" /><stop offset="1" stopColor="#6fc6d6" /></linearGradient>
      <linearGradient id="da-disco" x1="0" x2="1"><stop offset="0" stopColor="#2a7f93" /><stop offset="0.5" stopColor="#7fe0ef" /><stop offset="1" stopColor="#2a7f93" /></linearGradient>
    </defs>
    <path d="M30 58 C 14 58 12 40 26 37 C 26 20 50 16 56 30 C 64 20 86 24 84 42 C 98 43 98 58 86 58 Z" fill="url(#da-nube)" />
    <g>
      <path d="M44 66 V96 A16 5 0 0 0 76 96 V66" fill="url(#da-disco)" />
      <ellipse cx="60" cy="66" rx="16" ry="5" fill="#c9f6ff" />
      <path d="M44 76 A16 5 0 0 0 76 76 M44 86 A16 5 0 0 0 76 86" fill="none" stroke="#1d5d6c" strokeWidth="1.4" />
    </g>
    <path d="M22 70 V96 M17 90 L22 96 L27 90 M98 70 V96 M93 90 L98 96 L103 90" fill="none" stroke="#9df5b8" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round" />
  </svg>
)

// Libro abierto con páginas de volumen y una constelación de citas enlazadas
export const IlustracionFuentes = () => (
  <svg {...I}>
    <defs>
      <linearGradient id="fu-izq" x1="1" x2="0"><stop offset="0" stopColor="#d6f5e1" /><stop offset="1" stopColor="#7bbf95" /></linearGradient>
      <linearGradient id="fu-der" x1="0" x2="1"><stop offset="0" stopColor="#d6f5e1" /><stop offset="1" stopColor="#7bbf95" /></linearGradient>
      <linearGradient id="fu-tapa" x1="0" x2="1"><stop offset="0" stopColor="#1f6b45" /><stop offset="1" stopColor="#3fa66b" /></linearGradient>
    </defs>
    <path d="M10 64 L60 74 L110 64 L110 102 L60 112 L10 102 Z" fill="url(#fu-tapa)" />
    <path d="M14 62 C 32 56 48 58 60 66 L60 106 C 48 98 32 96 14 100 Z" fill="url(#fu-izq)" />
    <path d="M106 62 C 88 56 72 58 60 66 L60 106 C 72 98 88 96 106 100 Z" fill="url(#fu-der)" />
    <path d="M22 72 H50 M22 80 H48 M22 88 H50 M70 72 H98 M72 80 H98 M70 88 H98" stroke="#3f7a59" strokeWidth="1.6" strokeLinecap="round" />
    <path d="M30 40 L52 26 L74 36 L92 18 M52 26 L60 48 L74 36" fill="none" stroke="#9df5b8" strokeWidth="1.4" opacity="0.8" />
    {[[30, 40], [52, 26], [74, 36], [92, 18], [60, 48]].map(([x, y], k) => <circle key={k} cx={x} cy={y} r={k === 3 ? 4 : 3} fill="#c7ffd8" />)}
  </svg>
)
