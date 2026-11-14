// asistido por SI: Claude Code (Anthropic), escritura y revisión de código; base del prototipo migrada en el hackatón
import { beforeAll, describe, expect, it } from 'vitest'
import { abrirDb } from '../server/sqlite'
import { ErrorEntrada, validarId, validarMes, validarNivel, validarVariable } from '../server/validar'
import { manejar } from '../server/api'
import { crearFixture } from './fixture'

let ruta: string
let db: ReturnType<typeof abrirDb>
beforeAll(() => { ruta = crearFixture(); db = abrirDb(ruta) })

const get = (u: string) => manejar(db, new URL(u, 'http://x'))
const i16 = (b: Buffer) => Array.from(new Int16Array(b.buffer, b.byteOffset, b.byteLength / 2))

describe('validación', () => {
  it('mes fuera de 0..322 o no entero lanza ErrorEntrada', () => {
    for (const m of [323, -1, '1; DROP', 1.5, null]) expect(() => validarMes(m)).toThrow(ErrorEntrada)
    expect(validarMes('322')).toBe(322)
  })
  it('variable en lista blanca; inyección lanza', () => {
    expect(validarVariable(db, 'precip')).toBe('precip')
    expect(() => validarVariable(db, 'x; DROP TABLE mensual')).toThrow(ErrorEntrada)
    expect(() => validarVariable(db, 'elev_media')).toThrow(ErrorEntrada) // sin columna mensual
  })
  it('nivel solo 0, 1 o 2; id debe existir', () => {
    expect(validarNivel('2')).toBe(2)
    expect(() => validarNivel('9')).toThrow(ErrorEntrada)
    expect(validarId(db, 'AAA')).toBe('AAA')
    expect(() => validarId(db, "x' OR 1=1")).toThrow(ErrorEntrada)
  })
  it('abrirDb es de solo lectura', () => {
    expect(() => db.exec("INSERT INTO metadatos VALUES('a','b')")).toThrow()
  })
})

describe('endpoints', () => {
  it('orden por id dentro del nivel', () => {
    expect(JSON.parse(get('/api/orden?nivel=1').cuerpo as string).ids).toEqual(['AAA.1_1', 'BBB.1_1'])
  })
  it('coropleta binaria: tamaño, orden, hueco y cabeceras', () => {
    const r = get('/api/coropleta?nivel=1&var=precip&mes=2')
    expect(r.status).toBe(200)
    const v = i16(r.cuerpo as Buffer)
    expect((r.cuerpo as Buffer).byteLength).toBe(2 * 2)
    expect(v).toEqual([-32768, 402]) // AAA.1_1 es el hueco; BBB.1_1 es i=3 -> 400+2
    expect(r.cabeceras['X-Escala']).toBe('0.001')
    expect(r.cabeceras['X-Desplazamiento']).toBe('0')
    expect(r.cabeceras['X-Rango']).toBe('0,50')
  })
  it('coropleta.json trae [valor, fraccion, bandera]', () => {
    const j = JSON.parse(get('/api/coropleta.json?nivel=1&var=precip&mes=2').cuerpo as string)
    expect(j['AAA.1_1']).toEqual([null, 0, 1])
    expect(j['BBB.1_1']).toEqual([0.402, 1, 0])
  })
  it('entradas inválidas dan 400; id inexistente 404', () => {
    expect(get('/api/coropleta?nivel=7&var=precip&mes=0').status).toBe(400)
    expect(get('/api/coropleta?nivel=1&var=zzz&mes=0').status).toBe(400)
    expect(get('/api/coropleta?nivel=1&var=precip&mes=999').status).toBe(400)
    expect(get('/api/unidad/NOEXISTE').status).toBe(404)
  })
  it('rango: concatena meses y rechaza 25', () => {
    const r = get('/api/coropleta_rango?nivel=0&var=precip&desde=0&hasta=1')
    expect((r.cuerpo as Buffer).byteLength).toBe(2 * 2 * 2)
    expect(get('/api/coropleta_rango?nivel=0&var=precip&desde=0&hasta=24').status).toBe(400)
    expect(get('/api/coropleta_rango?nivel=0&var=precip&desde=5&hasta=1').status).toBe(400)
  })
  it('unidad trae estático con rótulo, clases y padre', () => {
    const u = JSON.parse(get('/api/unidad/AAA').cuerpo as string)
    expect(u.estatico[0]).toMatchObject({ variable_id: 'elev_media', media: 1234.5, q50: null, valido_min: -500, valido_max: 9000 })
    expect(u.estatico[0].rotulo).toBe('media del producto agregado, sin intervalo')
    expect(u.clases[0].clase).toBe('Af')
    expect(JSON.parse(get('/api/unidad/AAA.1_1').cuerpo as string).padre.id).toBe('AAA')
  })
  it('meta trae variables con escala, rango y etiqueta', () => {
    const m = JSON.parse(get('/api/meta').cuerpo as string)
    expect(m.variables.find((v: { id: string }) => v.id === 'precip')).toMatchObject({ escala: 0.001, valido_max: 50, etiqueta: 'FUENTE' })
    expect(m.meses).toEqual({ min: 0, max: 322 })
    expect(m.unidades_por_nivel['2']).toBe(2)
  })
  it('ruta desconocida da 404', () => { expect(get('/api/nada').status).toBe(404) })
})
