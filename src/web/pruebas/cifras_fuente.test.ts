// asistido por SI: Claude Code (Anthropic), cada cifra de los textos sale de los datos o queda atada por prueba al valor del cálculo o de su fuente (O1, C-3)
import { readFileSync } from 'node:fs'
import { describe, expect, it } from 'vitest'
import meta from '../public/datos/meta.json'
import { BASE_ULTIMO_INDICE, ERROR_ESFERA_PCT, FONDO, FRACCION_MINIMA, cifra } from '../src/textos/cifras'
import { ERROR_ESFERA_PCT as ERROR_GEODESIA } from '../src/herramientas/geodesia'
import { en } from '../src/textos/en'
import { RIESGOS } from '../src/paneles/lotes/modelo'

const leer = (ruta: string) => readFileSync(new URL(ruta, import.meta.url), 'utf8')

describe('cifras de los textos atadas a su fuente', () => {
  it('primer mes y número de meses se leen de meta.json, no están escritos en cifras.ts', () => {
    expect(cifra('fecha_inicio_serie', 'en')).toBe(`${meta.mes0}-01`)
    const fuente = leer('../src/textos/cifras.ts')
    expect(fuente).not.toMatch(/N_MESES\s*=\s*\d/)
    expect(fuente).not.toMatch(/anio:\s*20\d\d,\s*mes:\s*1\b/)
  })
  it('la línea base es una sola constante que usa el cálculo de anomalías', () => {
    const series = leer('../src/paneles/Series.tsx')
    expect(series).toContain('anomalia(valor, 0, BASE_ULTIMO_INDICE)')
    expect(series).toMatch(/import \{[^}]*BASE_ULTIMO_INDICE[^}]*\} from '..\/textos\/cifras'/)
    expect(BASE_ULTIMO_INDICE).toBeGreaterThan(0)
  })
  it('la fracción válida mínima es el umbral con que Datos publica un valor', () => {
    const py = leer('../../../src/simulacion/geo/serie_mensual.py')
    const m = /UMBRAL_FRAC_VALIDA\s*=\s*([\d.]+)/.exec(py)
    expect(m, 'UMBRAL_FRAC_VALIDA en serie_mensual.py').not.toBeNull()
    expect(FRACCION_MINIMA).toBe(Number(m![1]))
  })
  it('el error de la esfera es el que declara geodesia.ts', () => {
    expect(ERROR_ESFERA_PCT).toBe(ERROR_GEODESIA)
  })
  it('la fecha del fondo es la del título oficial de la capa GIBS usada (evidencia gibs_fondo.md)', () => {
    const capa = /GIBS\}\/(BlueMarble_[A-Za-z_]+)\//.exec(leer('../src/globo/fondos.ts'))![1]
    const ev = leer('../../../datos/evidencia/gibs_fondo.md')
    const m = new RegExp(`${capa}\\.json : "Blue Marble \\((\\w+) (\\d{4})`).exec(ev)
    expect(m, capa).not.toBeNull()
    const mes = new Date(`${m![1]} 1, 2000`).getMonth() + 1
    expect(FONDO).toEqual({ anio: Number(m![2]), mes })
  })
  it('el 2 de capa.t2m es la altura del código de variable T2M del producto', () => {
    const codigo = /\(T(\d)M\)/.exec(meta.variables.t2m.productos[0].producto)
    expect(codigo).not.toBeNull()
    expect(en['capa.t2m']).toContain(codigo![1])
  })
  it('la resolución de POWER del panel de lotes sale de la ficha power_diario.md', () => {
    const ficha = /celda de reanálisis MERRA-2 de `([\d,]+) x/.exec(leer('../../../datos/fichas/power_diario.md'))
    expect(ficha).not.toBeNull()
    expect(RIESGOS.helada.resolucion).toBe(`POWER ~${ficha![1]}°`)
    expect(leer('../src/paneles/lotes/modelo.ts')).not.toContain("'POWER ~0,5°'")
  })
})
