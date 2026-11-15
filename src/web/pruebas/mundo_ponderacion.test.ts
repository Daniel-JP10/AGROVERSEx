// asistido por SI: Claude Code (Anthropic), pruebas de las series del mundo, la ponderación y PI-D1 (S1w)
import { describe, expect, it, vi } from 'vitest'
// leyenda arrastra el estado de la app, que lee localStorage al cargar
vi.hoisted(() => { (globalThis as { localStorage?: unknown }).localStorage ??= { getItem: () => null, setItem: () => undefined } })
import { renderToStaticMarkup } from 'react-dom/server'
import { createElement } from 'react'
import informe from '../src/secciones/ciencia/pi_d1_mundo.json'
import { claveRegistrada, rangoPiD1, umbralesRegistrados, PI_D1_INFORME } from '../src/secciones/ciencia/pi_d1'
import { TarjetaPiD1Mundo } from '../src/secciones/ciencia/Ciencia'
import { rutaMatriz, usePonderacion, ponderacionEfectiva } from '../src/datos/estatico'
import { SIN_CULTIVO, textoValor } from '../src/globo/coropleta'
import { lineaPiD1 } from '../src/globo/leyenda'

const texto = (h: string) => h.replace(/<[^>]+>/g, ' ').replace(/\s+/g, ' ')
const total = (v: keyof typeof informe, k: string) => (informe[v].todos_los_meses.total.fraccion_mayor_a as Record<string, number>)[k]

describe('PI-D1 mundial leído del JSON', () => {
  it('umbral registrado de cada variable: 5 % relativo y 0,5 K en t2m', () => {
    expect(claveRegistrada(informe.ndvi.todos_los_meses)).toBe('5%')
    expect(claveRegistrada(informe.t2m.todos_los_meses)).toBe('0.5 K')
    expect(umbralesRegistrados(PI_D1_INFORME)).toBe('5%, 0.5 K')
  })
  it('el rango sale del archivo, sin IMERG Late', () => {
    const reg = rangoPiD1(PI_D1_INFORME, 'registrado')!
    expect(reg.n).toBe(4)
    expect(reg.min).toBe(total('t2m', '0.5 K'))
    expect(reg.max).toBe(total('ndvi', '5%'))
    // Late (38,7 % al 5 %) no entra
    expect(reg.max).toBeLessThan(total('precipitacion_late', '5%'))
    expect(rangoPiD1(PI_D1_INFORME, '2%')).toEqual({ min: total('precipitacion_final', '2%'), max: total('ndvi', '2%'), n: 3 })
    expect(rangoPiD1(PI_D1_INFORME, '10%')).toEqual({ min: total('precipitacion_final', '10%'), max: total('ndvi', '10%'), n: 3 })
  })
  it('la línea de Technical y la tarjeta de Ciencia muestran las cifras del JSON', () => {
    expect(lineaPiD1()).toBe('Between 12.6 and 35.1 % of unit-month pairs change with the definition (PI-D1)')
    const h = texto(renderToStaticMarkup(createElement(TarjetaPiD1Mundo, {})))
    expect(h).toContain('Between 12.6 and 35.1 % of unit-month pairs change with the definition (PI-D1).')
    expect(h).toContain('with 2%, 39.9 to 58.1 %; with 10%, 12.7 to 18.4 %')
    expect(h).toContain('5%, 0.5 K')
  })
})

describe('series del mundo', () => {
  it('rutas: adm0 y adm1 en MUNDO, adm2 por país, cultivo con sufijo', () => {
    const meta = { mundo: 'MUNDO', ponderaciones: { area: '', cultivo: '_cultivo' } }
    expect(rutaMatriz('precip', 0, 'KEN', 'cultivo', meta)).toBe('datos/MUNDO/precip_0_cultivo.json.gz')
    expect(rutaMatriz('ndvi', 1, 'KEN', 'area', meta)).toBe('datos/MUNDO/ndvi_1.json.gz')
    expect(rutaMatriz('t2m', 2, 'IND', 'cultivo', meta)).toBe('datos/IND/t2m_2_cultivo.json.gz')
    // sin meta del mundo (public/ con COL): la ruta de v0
    expect(rutaMatriz('t2m', 2, 'COL', 'cultivo', {})).toBe('datos/COL/t2m_2.json.gz')
  })
  it('cultivo por defecto; sin series del mundo se lee área', () => {
    expect(usePonderacion.getState().ponderacion).toBe('cultivo')
    expect(ponderacionEfectiva()).toBe('area')
  })
  it('una unidad sin cultivo dice "No cropland", nunca 0', () => {
    const s = textoValor(SIN_CULTIVO, 'mm/month', [0, 500])
    expect(s).toBe('No cropland')
    expect(s).not.toMatch(/\d/)
  })
})
