// asistido por SI: Claude Code (Anthropic), prueba del empalme IMERG Final (mm/hr) a Late (mm/day) pasando por paraMostrar (T-D2)
import { describe, expect, it } from 'vitest'
import { paraMostrar } from '../src/comun/unidades'
import { enEspanol } from './idioma_es'

// estas pruebas afirman la etiqueta en español (mm/mes, adimensional): fijan el idioma ellas mismas (D-039.1)
enEspanol()
import filas from './fixture_empalme_imerg.json'

type Fila = { unidad_id: string; mes: string; valor: number; estado: string; unidad: string }
const F = filas as Fila[]
const unidades = [...new Set(F.map(f => f.unidad_id))]
const mostrar = (f: Fila, unidad = f.unidad) => paraMostrar('precip', f.valor, unidad, f.mes)

// Climatología de octubre de Final en pantalla (media 2015-2024) y razón de la serie mostrada de 2025-10
function razon(u: string, tratar: (f: Fila) => { valor: number | null; unidad: string }) {
  const oct = F.filter(f => f.unidad_id === u && f.estado === 'final' && f.mes.endsWith('-10')).map(f => tratar(f).valor as number)
  const late = F.find(f => f.unidad_id === u && f.mes === '2025-10')!
  return (tratar(late).valor as number) / (oct.reduce((a, b) => a + b, 0) / oct.length)
}

// Rango físico: la lluvia mensual de una unidad en un octubre rara vez es menos de 0,5 ni más de 2 veces su climatología
// (variabilidad interanual de IMERG mensual en Colombia, INFERENCIA); un factor 24 o 28-31 queda muy por fuera.
const RANGO = [0.5, 2]

describe('empalme IMERG Final a Late en la serie mostrada', () => {
  it('2025-09 (Final) y 2025-10 (Late) salen en la misma unidad de pantalla', () => {
    for (const u of unidades) {
      const fin = mostrar(F.find(f => f.unidad_id === u && f.mes === '2025-09')!)
      const late = mostrar(F.find(f => f.unidad_id === u && f.mes === '2025-10')!)
      expect(late.unidad).toBe(fin.unidad)
    }
  })
  it('2025-10 mostrado / octubre de Final mostrado queda en el rango físico', () => {
    for (const u of unidades) {
      const r = razon(u, f => mostrar(f))
      expect(r, `${u}: razón ${r}`).toBeGreaterThan(RANGO[0]); expect(r, `${u}: razón ${r}`).toBeLessThan(RANGO[1])
    }
  })
  it('control: con Late convertido aparte (mm/day por días del mes) la razón es física, así que el dato no es el problema', () => {
    const conv = (f: Fila) => { const m = mostrar(f); return f.unidad === 'mm/day' ? { valor: f.valor * 31, unidad: 'mm/mes' } : m }
    for (const u of unidades) { const r = razon(u, conv); expect(r).toBeGreaterThan(RANGO[0]); expect(r).toBeLessThan(RANGO[1]) }
  })
})

describe('Final (mm/hr) y Late (mm/day) del mismo valor físico por cada camino', () => {
  const mes = 11 * 12 + 9 // 2025-10 contado desde 2000-01
  const dias = 31
  const hr = 0.1 // mm/hr
  const dia = hr * 24 // mm/day, mismo valor físico
  it('mmHoraAMmMes, mmPorMes y valoresCapa terminan iguales', async () => {
    const { mmHoraAMmMes } = await import('../src/datos/desescalar')
    const { mmPorMes } = await import('../src/datos/series')
    const { valoresCapa, capaPorId } = await import('../src/datos/capas')
    const esperado = hr * 24 * dias
    expect(mmHoraAMmMes(hr, mes, 'mm/hr')).toBeCloseTo(esperado)
    expect(mmHoraAMmMes(dia, mes, 'mm/day')).toBeCloseTo(esperado)
    expect(mmPorMes(hr, mes, 'mm/hr')).toBeCloseTo(esperado)
    expect(mmPorMes(dia, mes, 'mm/day')).toBeCloseTo(esperado)
    const c = capaPorId('precip')
    expect(valoresCapa(c, new Float32Array([hr]), mes, 'mm/hr')[0]).toBeCloseTo(esperado, 3)
    expect(valoresCapa(c, new Float32Array([dia]), mes, 'mm/day')[0]).toBeCloseTo(esperado, 3)
  })
})

import pares from './fixture_pares_COL.json'
describe('paraMostrar cubre todo par (variable, unidad) de serie_mensual en Colombia', () => {
  // fixture: datos/extraer_pares_variable_unidad.py sobre datos/procesados/series/COL
  it.each(pares as [string, string][])('%s en %s tiene conversión', (v, u) => {
    expect(() => paraMostrar(v, 1, u, '2025-10')).not.toThrow()
  })
  it('un par inventado lanza error con el par en el mensaje', () => {
    expect(() => paraMostrar('precip', 1, 'furlong/fortnight', '2025-10')).toThrow(/precip.*furlong/)
    expect(() => paraMostrar('inventada', 1, 'mm/hr', '2025-10')).toThrow(/inventada/)
  })
  it('T2M de K a °C', () => expect(paraMostrar('t2m', 273.15, 'K', '2025-10')).toEqual({ valor: 0, unidad: '°C' }))
})
