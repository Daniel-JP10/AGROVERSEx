// asistido por SI: Claude Code (Anthropic), escritura y revisión de código; base del prototipo migrada en el hackatón
import { CLAVES, type Clave, type Pesos, type Restricciones } from './ordenar'

export const ROTULOS: Record<Clave, string> = { agua: 'Uso de agua', forraje: 'Valor forrajero', nitrogeno: 'Fijación de nitrógeno', erosion: 'Reducción de erosión', materiaOrganica: 'Materia orgánica', mercado: 'Aptitud de mercado' }

// Estado de sesión: vive en el padre, no se guarda
export function Prioridades({ pesos, onPesos, rest, onRest }: { pesos: Pesos; onPesos: (p: Pesos) => void; rest: Restricciones; onRest: (r: Restricciones) => void }) {
  return (
    <fieldset className="prioridades">
      <legend>Prioridades (0 a 5, solo en esta sesión)</legend>
      {CLAVES.map((k) => (
        <label key={k}>{ROTULOS[k]}: <output>{pesos[k]}</output>
          <input type="range" min={0} max={5} step={1} value={pesos[k]} aria-label={ROTULOS[k]} onChange={(e) => onPesos({ ...pesos, [k]: Number(e.target.value) })} />
        </label>
      ))}
      <label>Agua disponible (mm por temporada)
        <input type="number" min={0} value={rest.aguaMaxMm ?? ''} onChange={(e) => onRest({ ...rest, aguaMaxMm: e.target.value === '' ? null : Number(e.target.value) })} />
      </label>
      <label><input type="checkbox" checked={rest.siembraDirecta} onChange={(e) => onRest({ ...rest, siembraDirecta: e.target.checked })} /> Hay equipo de siembra directa</label>
      <label><input type="checkbox" checked={rest.cosechaForraje} onChange={(e) => onRest({ ...rest, cosechaForraje: e.target.checked })} /> Hay equipo de cosecha de forraje</label>
    </fieldset>
  )
}
