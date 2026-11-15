// asistido por SI: Claude Code (Anthropic), pruebas de la alerta de helada: avisos siempre junto al estado y datos de la estación
import { createElement as h } from 'react'
import { renderToStaticMarkup } from 'react-dom/server'
import { describe, expect, it } from 'vitest'
import { AlertaHelada, type AlertaHeladaGemelo } from '../src/secciones/rotaciones/AlertaHelada'
import type { EstrategiaGemelo } from '../src/secciones/rotaciones/gemelo'
import { formatoNum } from '../src/secciones/rotaciones/textosGemelo'

// Forma de alertas.helada_etapa_sensible de DEMO-COL-01 en origin/gemelo; valores de prueba
const CAT = {
  'alert.frost.name': 'Frost in a sensitive stage (past climate, not a forecast)',
  'alert.frost.warm_bias': 'Bias {sesgo:+.2f} °C (CI {lo:+.2f} to {hi:+.2f}). The station recorded {dias_estacion} days at or below 0 °C.',
  'alert.frost.provisional': 'Provisional alert for this plot.',
  'alert.frost.unresolved': 'Watch: the series never reaches {umbral} °C ({fraccion:.0%} of seasons).',
}
const ALERTA: AlertaHeladaGemelo = {
  clave_nombre: 'alert.frost.name',
  validacion: { estacion: 'EST-X', periodo: ['2001-01-01', '2024-12-31'], n_dias: 4321, estacion_dias_le_0c: 13 },
  avisos: [{ clave: 'alert.frost.warm_bias', parametros: { sesgo: 1.0366, lo: 0.9266, hi: 1.1781, dias_estacion: 13 } }, { clave: 'alert.frost.provisional', parametros: {} }],
  estrategias: { A: { estado: 'vigilancia', clave: 'alert.frost.unresolved', parametros: { umbral: 0, fraccion: 0 } } },
}
const EST = [{ id: 'A', nombre: 'Papa continua' } as EstrategiaGemelo]
const pintar = (alerta?: AlertaHeladaGemelo, catalogo: Record<string, string> | undefined = CAT) => renderToStaticMarkup(h(AlertaHelada, { alerta, estrategias: EST, catalogo }))

describe('alerta de helada', () => {
  it('formatea .0% y +.2f como Python', () => {
    expect([formatoNum(0, '.0%'), formatoNum(0.4167, '.0%'), formatoNum(1.0366, '+.2f'), formatoNum(-0.5, '+.2f')]).toEqual(['0%', '42%', '+1.04', '-0.50'])
  })
  it('muestra los avisos antes que el estado y, en el mismo bloque, las heladas de la estación con su cobertura de días', () => {
    const s = pintar(ALERTA)
    expect(s.indexOf('data-testid="avisos-alerta"')).toBeLessThan(s.indexOf('data-estado="vigilancia"'))
    expect(s).toContain('Bias +1.04 °C (CI +0.93 to +1.18)')
    expect(s).toContain('Provisional alert for this plot.')
    expect(s).toMatch(/data-testid="alerta-estacion">[^<]*EST-X[^<]*13[^<]*4321[^<]*2001-01-01[^<]*2024-12-31/)
    expect(s).toContain('Watch: the series never reaches 0 °C (0% of seasons).')
  })
  it('sin avisos, sin catálogo o sin bloque no muestra ningún estado', () => {
    const sinCatalogo = renderToStaticMarkup(h(AlertaHelada, { alerta: ALERTA, estrategias: EST }))
    for (const s of [pintar({ ...ALERTA, avisos: [] }), sinCatalogo, pintar(undefined)]) {
      expect(s).not.toContain('data-estado=')
      expect(s).toContain('sin-dato')
    }
  })
})
