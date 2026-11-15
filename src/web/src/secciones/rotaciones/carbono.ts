// asistido por SI: Claude Code (Anthropic), puerta del carbono: ninguna cifra de carbono en pantalla mientras MOSTRAR_CARBONO sea false
import type { EstrategiaGemelo, SalidaOptimizacion, Tarjeta } from './gemelo'

// Orden del director (13:27): el orquestador la pasa a true cuando el verificador apruebe el panel N y C
export const MOSTRAR_CARBONO = false

const ES_CARBONO = /carbon/i
const sinIndicadores = (e: EstrategiaGemelo): EstrategiaGemelo => ({
  ...e,
  indicadores: Object.fromEntries(Object.entries(e.indicadores).filter(([k]) => !ES_CARBONO.test(k))),
  frente_a_linea_base: e.frente_a_linea_base && {
    gana: e.frente_a_linea_base.gana.filter((s) => !ES_CARBONO.test(s)),
    cede: e.frente_a_linea_base.cede.filter((s) => !ES_CARBONO.test(s)),
    similar: e.frente_a_linea_base.similar.filter((s) => !ES_CARBONO.test(s)),
  },
})
const sinTarjeta = (tj: Tarjeta): Tarjeta =>
  Object.fromEntries(Object.entries(tj).map(([k, v]) => [k, Array.isArray(v) ? v.filter((x) => !ES_CARBONO.test(JSON.stringify(x))) : v])) as Tarjeta

/** Quita del documento de optimización todo indicador, objetivo, texto o tarjeta que lleve carbono. */
export function sinCarbono(doc: SalidaOptimizacion, mostrar = MOSTRAR_CARBONO): SalidaOptimizacion {
  if (mostrar) return doc
  return {
    ...doc,
    objetivos: doc.objetivos.filter((o) => !ES_CARBONO.test(o.id) && !ES_CARBONO.test(o.indicador)),
    linea_base: sinIndicadores(doc.linea_base),
    frente: doc.frente.map(sinIndicadores),
    tarjetas: doc.tarjetas && Object.fromEntries(Object.entries(doc.tarjetas).map(([k, v]) => [k, sinTarjeta(v)])),
    compromisos: {
      ...doc.compromisos,
      explicacion: doc.compromisos.explicacion.filter((s) => !ES_CARBONO.test(s)),
      explicacion_claves: doc.compromisos.explicacion_claves?.filter((x) => !ES_CARBONO.test(JSON.stringify(x))),
      mejor_por_objetivo: Object.fromEntries(Object.entries(doc.compromisos.mejor_por_objetivo).filter(([k]) => !ES_CARBONO.test(k))),
    },
  }
}
