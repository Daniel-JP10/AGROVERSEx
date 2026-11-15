// asistido por SI: Claude Code (Anthropic), pruebas de las secciones Ciencia y validación y Datos abiertos (T-W6)
import { createElement } from 'react'
import { renderToStaticMarkup } from 'react-dom/server'
import { afterEach, describe, expect, it } from 'vitest'
import { Ciencia } from '../src/secciones/ciencia/Ciencia'
import { DatosAbiertos } from '../src/secciones/datos-abiertos/DatosAbiertos'
import { en } from '../src/textos/en'
import { es } from '../src/textos/es'
import { alternar, idioma } from '../src/textos/i18n'
import { useModo } from '../src/textos/modos'

afterEach(() => { useModo.getState().set('agricultor'); if (idioma() === 'en') alternar() })

const ciencia = (datos?: Parameters<typeof Ciencia>[0]) => renderToStaticMarkup(createElement<NonNullable<typeof datos>>(Ciencia, datos ?? {}))
const datos = (p?: Parameters<typeof DatosAbiertos>[0]) => renderToStaticMarkup(createElement<NonNullable<typeof p>>(DatosAbiertos, p ?? {}))
// Ejemplo de prueba: vive solo aquí, no en la app
const COMPLETA = { id: 'suelo_desnudo', valor: 0.5, intervalo: [0.4, 0.6] as [number, number], linea_base: 0.3, n: 120 }

describe('ciencia', () => {
  it('sin archivos carga: tres métricas "dato no disponible", un solo estado', () => {
    const h = ciencia()
    expect((h.match(/data-metrica=/g) ?? []).length).toBe(3)
    expect(h).toContain('Dato todavía no disponible.')
    expect((h.match(/role="status"/g) ?? []).length).toBe(1)
  })
  it('muestra PI-D1 a PI-D4, abiertas, con el texto de D-006', () => {
    const h = ciencia()
    for (const i of [1, 2, 3, 4]) expect(h).toContain(`PI-D${i}`)
    expect((h.match(/data-pregunta=/g) ?? []).length).toBe(4)
    expect((h.match(/>abierta</g) ?? []).length).toBe(4)
    expect(h).toContain('ponderando solo las celdas de cultivo')
    expect(h).toContain('HLS')
  })
  it('lista visible de limitaciones y explicación de satélite contra tierra', () => {
    const h = ciencia()
    expect((h.match(/<li[^>]*data-limitacion/g) ?? []).length).toBeGreaterThanOrEqual(4)
    expect(h).toContain('Un satélite ve un área grande')
    useModo.getState().set('tecnico')
    expect(ciencia()).toContain('error de representatividad')
  })
  it('ninguna métrica sin intervalo, línea base ni tamaño de muestra', () => {
    const h = ciencia({ metricas: [COMPLETA] })
    const bloques = h.split('data-metrica=').slice(1)
    expect(bloques).toHaveLength(3)
    for (const b of bloques) for (const c of ['valor', 'intervalo', 'linea_base', 'n']) expect(b, c).toContain(`data-campo="${c}"`)
    expect(h).toContain('120')
  })
  it('una métrica incompleta no enseña su número', () => {
    for (const falta of ['intervalo', 'linea_base', 'n'] as const) {
      const m = { ...COMPLETA, [falta]: undefined }
      const h = ciencia({ metricas: [m] })
      expect(h, falta).not.toContain('0,5')
      expect(h, falta).not.toContain('0.5')
    }
  })
  it('un resultado que no supera la línea base se muestra igual', () => {
    const h = ciencia({ metricas: [{ ...COMPLETA, valor: 0.2, intervalo: [0.1, 0.25], linea_base: 0.3 }] })
    expect(h).toContain('0,2')
    expect(h).toContain('Los resultados negativos')
  })
})

describe('datos abiertos', () => {
  it('sin archivos carga: todos los campos "dato no disponible", sin descarga ni comando falsos', () => {
    const h = datos()
    expect((h.match(/data-campo=/g) ?? []).length).toBe(7)
    expect(h).toContain('Dato todavía no disponible.')
    expect(h).not.toContain('<a ')
    expect(h).not.toContain('<code')
  })
  it('con ficha muestra valores, enlace de descarga y comando copiable', () => {
    const h = datos({ campos: { licencia: 'CC BY 4.0' }, descargas: [{ nombre: 'manifiesto', url: 'https://ejemplo.invalid/m.json' }], comando: 'make repro' })
    expect(h).toContain('CC BY 4.0')
    expect(h).toContain('href="https://ejemplo.invalid/m.json"')
    expect(h).toContain('<code')
    expect(h).toContain('make repro')
    expect(h).toMatch(/<button[^>]*>Copiar comando/)
  })
  it('solo acepta enlaces https para la descarga', () => {
    expect(datos({ descargas: [{ nombre: 'x', url: 'javascript:alert(1)' }] })).not.toContain('<a ')
  })
})

describe('textos de las tres secciones', () => {
  const claves = Object.keys(en).filter((k) => /^(gemelo|ciencia|datos)\./.test(k))
  it('hay claves de las tres secciones en los dos idiomas', () => {
    expect(claves.length).toBeGreaterThan(40)
    for (const k of claves) expect((es as Record<string, string>)[k], k).toBeTruthy()
  })
  it('ningún dígito escrito a mano en sus textos', () => {
    for (const k of claves) {
      expect((en as Record<string, string>)[k], k).not.toMatch(/\d/)
      expect((es as Record<string, string>)[k], k).not.toMatch(/\d/)
    }
  })
})
