// asistido por SI: Claude Code (Anthropic), ejecuta la ruta y las acciones de interfaz de un paso del recorrido
import * as interfaz from '../../secciones/tierra/interfaz'
import { dato, type Resolver } from '../../textos/huecos'
import { irA } from '../ruta'
import type { Paso, Valor } from './pasos'

type Globo = Pick<typeof interfaz, 'irAUnidad' | 'cambiarVariable' | 'cambiarMes' | 'activarComparador' | 'abrirPestana'>
export interface Entorno { resolver?: Resolver; ir?: typeof irA; globo?: Globo }

const valor = (v: Valor, resolver: Resolver) => (typeof v === 'string' ? v : resolver(v.dato))

/** Navega a la ruta del paso y mueve el globo solo con la interfaz de Daniel; lo que no tiene dato se omite. */
export function ejecutar(paso: Paso, { resolver = dato, ir = irA, globo = interfaz }: Entorno = {}): void {
  const params: Record<string, string> = {}
  for (const [k, v] of Object.entries(paso.params ?? {})) { const x = valor(v, resolver); if (x) params[k] = x }
  ir(paso.ruta, params)
  for (const a of paso.acciones ?? []) {
    try {
      if (a.fn === 'activarComparador') globo.activarComparador(a.activo)
      else if (a.fn === 'abrirPestana') globo.abrirPestana(a.nombre)
      else {
        const x = valor(a.fn === 'irAUnidad' ? a.unidad : a.fn === 'cambiarVariable' ? a.variable : a.mes, resolver)
        if (x) globo[a.fn](x)
      }
    } catch { /* el globo rechazó el valor: el recorrido sigue */ }
  }
}
