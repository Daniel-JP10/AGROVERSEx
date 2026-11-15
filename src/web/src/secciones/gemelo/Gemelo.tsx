// asistido por SI: Claude Code (Anthropic), sección El gemelo del lote: lee el lote de la ruta y carga el ejemplo solo con VITE_EJEMPLOS=1
import { useEffect, useState } from 'react'
import { useRuta } from '../../app/ruta'
import { GemeloVista } from './GemeloVista'
import type { Estrategia } from './tipos'

// Vite sustituye la bandera al compilar: sin ella el ejemplo no entra a la versión pública
const cargarEjemplo = () => (import.meta.env.VITE_EJEMPLOS === '1' ? import('./ejemplo') : Promise.resolve(null))

type Props = { base?: Estrategia; alternativa?: Estrategia }

// Con `base` (corrida real del gemelo) se rotula simulación del modelo; sin ella solo hay ejemplo o nada
export function Gemelo({ base, alternativa }: Props = {}) {
  const { params } = useRuta()
  const [ejemplo, setEjemplo] = useState<readonly Estrategia[] | null>(null)
  useEffect(() => { if (!base) void cargarEjemplo().then((m) => m && setEjemplo(m.ESTRATEGIAS_EJEMPLO)) }, [base])
  if (base) return <GemeloVista origen="corrida" lote={params.lote} base={base} alternativa={alternativa} />
  return <GemeloVista origen="ejemplo" lote={params.lote} base={ejemplo?.[0]} alternativa={ejemplo?.[1]} />
}
