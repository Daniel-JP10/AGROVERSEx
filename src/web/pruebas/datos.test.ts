// asistido por SI: Claude Code (Anthropic), escritura y revisión de código; base del prototipo migrada en el hackatón
import { describe, expect, it } from 'vitest'
import { QueryClient } from '@tanstack/react-query'
import { desescalar, formatearRango, SIN_DATO } from '../src/datos/desescalar'
import { decodificarCoropleta } from '../src/datos/binario'
import { BANDERA } from '../src/datos/banderas'
import { crearCliente } from '../src/datos/cliente'
import { cargarMes, ultimoMesBueno } from '../src/datos/consultas'

describe('desescalar', () => {
  it('el relleno y null dan null', () => {
    expect(desescalar(-32768, 0.01, 0)).toBeNull()
    expect(desescalar(null, 0.01, 0)).toBeNull()
    expect(desescalar(SIN_DATO, 1, 5)).toBeNull() // con desplazamiento tampoco se vuelve válido
  })
  it('aplica escala y desplazamiento', () => expect(desescalar(2550, 0.01, -10)).toBeCloseTo(15.5, 6))
  it('decodifica Int16 LE con NaN en huecos', () => {
    const r = decodificarCoropleta(new Int16Array([100, -32768]).buffer, 0.01, 0)
    expect(r[0]).toBeCloseTo(1, 5)
    expect(r[1]).toBeNaN()
  })
  it('el rango lleva unidad', () => {
    const t = formatearRango(1, 2, 3, 'mm')
    expect(t).toContain('mm'); expect(t).toContain('1'); expect(t).toContain('3')
  })
  it('banderas en el orden de la fase 2', () => {
    expect(Object.values(BANDERA)).toEqual([1, 2, 4, 8, 16])
  })
})

// Respuesta binaria simulada con las cabeceras de la API.
const resp = (v: number) => new Response(new Int16Array([v]).buffer, { headers: { 'X-Escala': '0.01', 'X-Desplazamiento': '0', 'X-Rango': '0,50' } })

describe('cliente y caché', () => {
  it('reintenta una vez y luego falla', async () => {
    let n = 0
    const c = crearCliente(async () => { n++; throw new Error('red') })
    await expect(c.coropleta(1, 'precip', 0)).rejects.toThrow()
    expect(n).toBe(2)
  })
  it('falla en el mes 5: error visible y el mes mostrado sigue siendo el 4', async () => {
    const c = crearCliente(async (u) => (u.includes('mes=5') ? new Response('x', { status: 500 }) : resp(100)))
    const qc = new QueryClient()
    for (let m = 0; m <= 4; m++) await cargarMes(qc, c, 1, 'precip', m)
    await expect(cargarMes(qc, c, 1, 'precip', 5)).rejects.toThrow()
    expect(qc.getQueryState(['coropleta', 1, 'precip', 5])?.status).toBe('error')
    expect(ultimoMesBueno(qc, 1, 'precip', 5)?.mes).toBe(4)
  })
  it('conserva a lo sumo 48 meses', async () => {
    const c = crearCliente(async () => resp(1))
    const qc = new QueryClient()
    for (let m = 0; m < 50; m++) await cargarMes(qc, c, 1, 'precip', m)
    expect(qc.getQueryCache().findAll({ queryKey: ['coropleta', 1, 'precip'] }).length).toBe(48)
  })
})
