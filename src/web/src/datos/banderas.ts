import { t } from '../textos/i18n'
// asistido por SI: Claude Code (Anthropic), escritura y revisión de código; base del prototipo migrada en el hackatón
// Bits de bandera_motivo, en el orden real de la fase 2 (simulacion/variables.py).
export const BANDERA = {
  HUECO_PRODUCTO: 1 << 0,
  NUBE: 1 << 1,
  NIEVE: 1 << 2,
  PROVISIONAL: 1 << 3,
  FUERA_COBERTURA: 1 << 4,
} as const

// Calidad baja (bit 5) es decisión técnica del controlador; se rotula aparte.
export const BANDERA_CALIDAD_BAJA = 1 << 5

const rotulos = (): [number, string][] => [
  [BANDERA.HUECO_PRODUCTO, t('bandera.hueco')], [BANDERA.NUBE, t('bandera.nube')], [BANDERA.NIEVE, t('bandera.nieve')],
  [BANDERA.PROVISIONAL, t('bandera.provisional')], [BANDERA.FUERA_COBERTURA, t('bandera.cobertura')], [BANDERA_CALIDAD_BAJA, t('bandera.calidad')],
]

// bandera_motivo es por unidad y mes, común a todos los productos: con valor presente no aplican los
// motivos de otro producto. Solo lluvia y ET llevan calidad o provisional propios.
export function rotulosDeVariable(v: string, b: number | null, hayValor: boolean): string[] {
  if (!hayValor) return rotulosBandera(b)
  const propios = v === 'precip' ? BANDERA.PROVISIONAL | BANDERA_CALIDAD_BAJA : v === 'et' ? BANDERA.PROVISIONAL : 0
  return rotulosBandera((b ?? 0) & propios)
}

export const rotulosBandera = (b: number | null): string[] => rotulos().filter(([bit]) => ((b ?? 0) & bit) !== 0).map(([, r]) => r)
