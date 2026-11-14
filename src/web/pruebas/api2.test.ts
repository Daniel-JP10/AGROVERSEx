// asistido por SI: Claude Code (Anthropic), escritura y revisión de código; base del prototipo migrada en el hackatón
import { beforeAll, describe, expect, it } from 'vitest'
import { abrirDb } from '../server/sqlite'
import { manejar } from '../server/api'
import { crearFixture } from './fixture'

let db: ReturnType<typeof abrirDb>
beforeAll(() => { db = abrirDb(crearFixture()) })
const get = (u: string) => manejar(db, new URL(u, 'http://x'))
const j = (u: string) => JSON.parse(get(u).cuerpo as string)

describe('serie', () => {
  it('desde>hasta, rango fuera de 0..322 o más de 12 vars dan 400', () => {
    expect(get('/api/serie/AAA?vars=precip&desde=3&hasta=1').status).toBe(400)
    expect(get('/api/serie/AAA?vars=precip&desde=0&hasta=323').status).toBe(400)
    expect(get('/api/serie/AAA?vars=precip&desde=-1&hasta=2').status).toBe(400)
    expect(get('/api/serie/AAA?vars=' + Array(13).fill('precip').join(',')).status).toBe(400)
    expect(get('/api/serie/AAA?vars=precip;DROP').status).toBe(400)
    expect(get('/api/serie/NOPE?vars=precip').status).toBe(404)
  })
  it('hueco: null con bandera, no 0; desescala; p10/p90 si existen; sin fila = -1', () => {
    const r = j('/api/serie/AAA.1_1?vars=precip,t2m&desde=0&hasta=4')
    expect(r.meses).toEqual([0, 1, 2, 3, 4])
    expect(r.series.precip.valor.slice(0, 4)).toEqual([0.3, 0.301, null, 0.303])
    expect(r.series.precip.bandera).toEqual([0, 0, 1, 0, -1])
    expect(r.series.precip.valor[4]).toBeNull()
    expect(r.series.precip.unidad_medida).toBe('mm/h')
    expect(r.series.precip.rango).toEqual([0, 50])
    expect(r.series.t2m.valor[0]).toBeCloseTo(23.02)
    expect(r.series.t2m.p10).toHaveLength(5)
    expect(r.series.precip.p10).toBeUndefined()
  })
})

describe('tablas de referencia', () => {
  it('enso ordenado por mes_id', () => {
    expect(j('/api/enso').map((r: { mes_id: number }) => r.mes_id)).toEqual([0, 1, 2])
  })
  it('anual y eventos', () => {
    expect(j('/api/anual/AAA').filas.map((f: { anio: number }) => f.anio)).toEqual([2000, 2001])
    expect(j('/api/eventos/AAA')[0]).toMatchObject({ id: 'e1', intensidad: 0.7, etiqueta: 'FUENTE' })
    expect(get('/api/anual/NOPE').status).toBe(404)
  })
})

describe('rotaciones y lotes', () => {
  it('sirve etiquetas, incluida PENDIENTE, y no combina efectos', () => {
    const r = j('/api/rotaciones/AAA')
    expect(r.vacio).toBe(false)
    expect(r.sistemas[0].etiqueta).toBe('FUENTE')
    expect(r.antecesor[0]).toMatchObject({ efecto2: 2.5, beta_lluvia: 0.6, beta_t: -1 })
    expect(r.sucesion).toHaveLength(1)
    const p = j('/api/rotaciones/AAA?region=Otra')
    expect(p.sistemas[0].etiqueta).toBe('PENDIENTE')
    expect(get('/api/rotaciones/AAA?region=x').status).toBe(400)
  })
  it('región sin datos: 200 con vacio y motivo', () => {
    const r = get('/api/rotaciones/BBB')
    expect(r.status).toBe(200)
    expect(JSON.parse(r.cuerpo as string)).toMatchObject({ vacio: true, motivo: expect.any(String) })
    expect(j('/api/lotes/BBB').vacio).toBe(true)
  })
  it('?unidad= usa zona_demo; fuera de zona o sin zona: vacio con motivo', () => {
    const r = j('/api/rotaciones?unidad=AAA.1.1_1')
    expect(r).toMatchObject({ vacio: false, zona: 'corn_belt' })
    expect(r.sistemas[0].region).toBe('Corn Belt')
    expect(r.antecesor).toHaveLength(1) // solo EE. UU., por país de la zona
    expect(j('/api/rotaciones?unidad=BBB')).toMatchObject({ vacio: true, motivo: expect.stringContaining('zona DEMO') })
    expect(get('/api/rotaciones?unidad=NOPE').status).toBe(404)
  })
  it('/api/eventos sin id lista todos los eventos', () => {
    expect(j('/api/eventos')).toHaveLength(1)
  })
  it('lotes por descendencia y detalle desescalado', () => {
    expect(j('/api/lotes/AAA').lotes.map((l: { id: string }) => l.id)).toEqual(['L1'])
    const d = j('/api/lote/L1')
    expect(d.diario[0]).toMatchObject({ ndvi: 0.5, sm_sensor: null })
    expect(get('/api/lote/nada').status).toBe(404)
  })
})
