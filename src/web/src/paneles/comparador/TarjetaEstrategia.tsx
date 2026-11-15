// asistido por SI: Claude Code (Anthropic), escritura y revisión de código; base del prototipo migrada en el hackatón
import { CLAVES, type Ordenada } from './ordenar'
import type { Adaptado } from './datos'
import { ROTULOS } from './Prioridades'

const SIN = 'sin evidencia en la demo'
const SIN_EV = ['forraje', 'mercado']
const f = (n: number | null | undefined) => (n == null ? 'sin dato publicado' : String(n))

export function TarjetaEstrategia({ o, d, rol }: { o: Ordenada; d: Adaptado; rol: string }) {
  const e = o.estrategia
  const a = d.antecesor.find((x) => e.nombre.toLowerCase().includes(x.antecesor.toLowerCase()))
  return (
    <article className="tarjeta" data-testid="tarjeta">
      <h3>{e.nombre} <small>({rol})</small></h3>
      <p className="puntaje">Puntaje {o.puntaje.toFixed(2)} (intervalo {o.intervalo[0].toFixed(2)} a {o.intervalo[1].toFixed(2)}) · DEMO</p>
      {o.rindeMenosQueHabitual != null && <p className="insignia" data-testid="rinde-menos">rinde menos que la habitual en {Math.abs(o.rindeMenosQueHabitual)} %</p>}
      {o.viola.map((v) => <p key={v} className="insignia viola">viola una restricción: {v}</p>)}
      <section data-bloque="porque"><h4>1. Por qué se sugiere</h4><p>Secuencia documentada para {d.region}; el orden lo fijan las prioridades del usuario.</p></section>
      <section data-bloque="evidencia"><h4>2. Qué evidencia la respalda</h4><p>{d.fuentes.join(', ')} · {d.etiqueta}{d.chino && ' · procedencia china: depende de un mapa de un grupo chino (D-009), uso sujeto a decisión del director'}</p></section>
      <section data-bloque="beneficios"><h4>3. Beneficios</h4>
        <ul>
          <li>Rendimiento (Kluger): {a ? `Efecto₂ ${f(a.efecto2)} %, Eff_div ${f(a.eff_div)} %, β lluvia ${f(a.beta_lluvia)}, β T ${f(a.beta_t)}; ${a.significativo ? 'significativo' : 'no significativo'}; sin intervalo publicado, confianza baja.` : 'sin coeficiente publicado'}</li>
          {CLAVES.map((k) => <li key={k}>{ROTULOS[k]}: {SIN_EV.includes(k) || !e.beneficios[k] ? SIN : e.beneficios[k]!.v}</li>)}
          <li>Ingreso suplementario: {SIN}</li>
        </ul>
        {a && <p className="nota">Efecto₂, Eff_div y los β se muestran por separado. Cualquier suma de ellos es combinación propia, no del artículo.</p>}
      </section>
      <section data-bloque="vacios"><h4>4. Vacíos de información</h4><p>Agua, erosión y materia orgánica sin fuente cargada en la demo; los equipos que exige cada estrategia son SUPUESTO.</p></section>
      <section data-bloque="riesgos"><h4>5. Riesgos para revisión local</h4><p><span className="insignia">revisión local</span> menor humedad profunda bajo coberturas (−18 %, n = 61).</p></section>
    </article>
  )
}
