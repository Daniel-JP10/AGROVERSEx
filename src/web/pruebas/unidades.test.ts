// asistido por SI: Claude Code (Anthropic), pruebas de la conversión única para mostrar (contrato web_componentes §5)
import { describe, expect, it } from 'vitest'
import { paraMostrar, diasDelMes } from '../src/comun/unidades'
import { mmHoraAMmMes } from '../src/datos/desescalar'
import { mmPorMes } from '../src/datos/series'
import { capaPorId, valoresCapa } from '../src/datos/capas'

describe('paraMostrar', () => {
  it('febrero bisiesto 2024 tiene 29 días y 2023 tiene 28 (mes AAAA-MM o índice desde 2000-01)', () => {
    expect(diasDelMes('2024-02')).toBe(29)
    expect(diasDelMes('2023-02')).toBe(28)
    expect(diasDelMes(24 * 12 + 1)).toBe(29)
    expect(diasDelMes(23 * 12 + 1)).toBe(28)
  })
  it('lluvia mm/h a mm/mes con los días reales del mes', () => {
    expect(paraMostrar('precip', 1, 'mm/h', '2024-02')).toEqual({ valor: 696, unidad: 'mm/mes' })
    expect(paraMostrar('precip', 1, 'mm/hr', '2023-02').valor).toBe(672)
    expect(paraMostrar('precip', 1, 'mm/h', '2024-01').valor).toBe(744)
  })
  it('el mes es obligatorio y se valida', () => {
    // @ts-expect-error mes obligatorio
    expect(() => paraMostrar('precip', 1, 'mm/h')).toThrow()
    expect(() => paraMostrar('precip', 1, 'mm/h', '2024-2')).toThrow()
  })
  it('el resto conserva valor y arregla la unidad; sin dato nunca es 0', () => {
    expect(paraMostrar('t2m', 21.5, 'C', '2024-01')).toEqual({ valor: 21.5, unidad: '°C' })
    expect(paraMostrar('ndvi', 0.6, 'adim', '2024-01').unidad).toBe('adimensional')
    expect(paraMostrar('precip', null, 'mm/h', '2024-01').valor).toBeNull()
  })
  it('mmHoraAMmMes, mmPorMes y valoresCapa usan la misma conversión', () => {
    expect(mmHoraAMmMes(1, '2024-02')).toBe(696)
    expect(mmPorMes(1, 24 * 12 + 1)).toBe(696)
    expect(valoresCapa(capaPorId('precip'), new Float32Array([1]), 23 * 12 + 1)[0]).toBe(672)
  })
  it('mm/day pasa a mm/mes con los días reales del mes', () => {
    expect(paraMostrar('precip', 2, 'mm/day', '2024-02')).toEqual({ valor: 58, unidad: 'mm/mes' })
    expect(paraMostrar('precip', 2, 'mm/day', '2025-10')).toEqual({ valor: 62, unidad: 'mm/mes' })
    expect(paraMostrar('precip', 2, 'mm/d', '2025-09').valor).toBe(60)
    expect(paraMostrar('precip', null, 'mm/day', '2025-10').valor).toBeNull()
  })
})
