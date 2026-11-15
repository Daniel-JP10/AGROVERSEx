// asistido por SI: Claude Code (Anthropic), escritura y revisión de código; base del prototipo migrada en el hackatón
import { describe, expect, it } from 'vitest'
import { areaKm2, distanciaKm } from '../src/herramientas/geodesia'

// Haversine con radio medio 6371 km. Frente al elipsoide WGS84 el error llega a ~0,5 %:
// por eso la prueba de Bogotá–Medellín usa tolerancia de 2 %.
describe('distanciaKm (haversine, esfera de radio medio)', () => {
  it('1 grado de latitud ≈ 111,19 km (±0,1)', () => {
    expect(Math.abs(distanciaKm([0, 0], [0, 1]) - 111.19)).toBeLessThan(0.1)
  })
  it('Bogotá–Medellín en línea recta ≈ 240 km (±2 %)', () => {
    const bogota: [number, number] = [-74.072, 4.711]
    const medellin: [number, number] = [-75.581, 6.244]
    expect(Math.abs(distanciaKm(bogota, medellin) - 240)).toBeLessThan(240 * 0.02)
  })
  it('es simétrica y vale 0 entre el mismo punto', () => {
    const a: [number, number] = [-74.072, 4.711]
    const b: [number, number] = [-75.581, 6.244]
    expect(distanciaKm(a, b)).toBeCloseTo(distanciaKm(b, a), 9)
    expect(distanciaKm(a, a)).toBe(0)
  })
})

// Área esférica de anillos [lon, lat]: celda de 1° en el ecuador ≈ 12.364 km²
describe('areaKm2 (esférica)', () => {
  const celda: [number, number][] = [[0, 0], [1, 0], [1, 1], [0, 1]]
  it('celda de 1° en el ecuador ≈ 12.364 km² (±1 %)', () => {
    expect(Math.abs(areaKm2(celda) - 12364) / 12364).toBeLessThan(0.01)
  })
  it('no depende del sentido del anillo ni de cerrarlo', () => {
    const cerrada = [...celda, celda[0]]
    expect(areaKm2(cerrada)).toBeCloseTo(areaKm2(celda), 6)
    expect(areaKm2([...celda].reverse())).toBeCloseTo(areaKm2(celda), 6)
  })
  it('un anillo con menos de 3 puntos lanza error', () => {
    expect(() => areaKm2([[0, 0], [1, 1]])).toThrow()
  })
})
