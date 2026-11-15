// asistido por SI: Claude Code (Anthropic), pruebas del tablero de Rotaciones y de la puerta del carbono con los paquetes reales
import { readFileSync } from 'node:fs'
import { join } from 'node:path'
import { createElement as h } from 'react'
import { renderToStaticMarkup } from 'react-dom/server'
import { afterEach, describe, expect, it } from 'vitest'
import type { EstadoLote, LoteJson, Simulacion } from '../src/secciones/lote/datos'
import { MOSTRAR_CARBONO, sinCarbono } from '../src/secciones/rotaciones/carbono'
import type { SalidaOptimizacion } from '../src/secciones/rotaciones/gemelo'
import { VistaRotaciones } from '../src/secciones/rotaciones/Rotaciones'
import { ordenSimulacion, PanelNC, Tablero } from '../src/secciones/rotaciones/Tablero'
import { PESOS_IGUALES } from '../src/secciones/rotaciones/ordenPrioridades'
import { t } from '../src/textos/i18n'
import { useModo } from '../src/textos/modos'

const PUB = join(__dirname, '..', 'public')
const leer = <T,>(r: string): T => JSON.parse(readFileSync(join(PUB, r), 'utf8'))
const lote = leer<LoteJson>('gemelo/DEMO-COL-01/lote.json')
const sim = leer<Simulacion>('gemelo/DEMO-COL-01/simulacion_historico.json')
const opt = leer<SalidaOptimizacion>('gemelo/DEMO-COL-01/optimizacion_historico.json')
const cat = leer<Record<string, string>>('gemelo/textos/en.json')
const d: Extract<EstadoLote, { estado: 'listo' }> = { estado: 'listo', lote, sim, cat }
const texto = (html: string) => html.replace(/<[^>]*>/g, ' ')
afterEach(() => useModo.setState({ modo: 'agricultor' }))

describe('puerta del carbono', () => {
  it('MOSTRAR_CARBONO está en false hasta que el orquestador lo cambie', () => {
    expect(MOSTRAR_CARBONO).toBe(false)
  })
  it('oculto: el panel N y C dice Not available yet y no muestra ninguna cifra', () => {
    const s = renderToStaticMarkup(h(PanelNC, { sim, e: sim.estrategias[0], mostrar: false }))
    expect(s).toContain(t('rotaciones.nc_no_disponible'))
    expect(texto(s)).not.toMatch(/\d|t C\/ha/)
  })
  it('visible: mediana del ensamble de enero del año 1 y cambio, misma base, con rango y unidad', () => {
    const e = sim.estrategias[0]
    const s = renderToStaticMarkup(h(PanelNC, { sim, e, mostrar: true }))
    expect(s).toContain('January mean of year 1')
    expect(s).toContain('model ensemble median 277 t C/ha')
    expect(s).toMatch(/\(range \d+(\.\d+)?-\d+\)/)
    expect(s).toContain(t('rotaciones.nc_cambio'))
    expect(s).not.toContain('187')
    expect(s).not.toContain(t('rotaciones.nc_lim_rango'))
  })
  it('visible en modo técnico: las dos limitaciones, con el número de muestras leído del paquete', () => {
    useModo.setState({ modo: 'tecnico' })
    const s = renderToStaticMarkup(h(PanelNC, { sim, e: sim.estrategias[0], mostrar: true }))
    expect(s).toContain(t('rotaciones.nc_lim_rango'))
    expect(s).toContain(`With ${sim.metadatos.miembros!.parametros} parameter samples`)
  })
  it('"0-30 cm" del rótulo es la profundidad del carbono del gemelo (D-039 punto 3)', () => {
    expect(readFileSync(join(__dirname, '..', '..', 'gemelo', 'carbono.py'), 'utf8')).toContain('t C/ha en 0-30 cm')
    expect(t('rotaciones.nc_inicial')).toContain('0-30 cm')
  })
  it('sinCarbono quita indicadores, objetivos, tarjetas y textos de carbono del documento', () => {
    // Solo lo que se muestra: metadatos, parámetros y valores de prioridad siguen intactos para ordenar
    const visible = (x: SalidaOptimizacion) => JSON.stringify([x.objetivos, x.linea_base.indicadores, x.frente.map((e) => [e.indicadores, e.frente_a_linea_base]), x.tarjetas, x.compromisos])
    expect(visible(opt)).toMatch(/carbon/i)
    expect(visible(sinCarbono(opt))).not.toMatch(/carbon/i)
    expect(sinCarbono(opt, true)).toBe(opt)
  })
  it('la sección completa con datos reales no muestra carbono', () => {
    const s = renderToStaticMarkup(h(VistaRotaciones, { fuente: { estado: 'listo', origen: 'modelo', doc: opt, catalogo: cat }, lote: d }))
    // Quedan palabras sueltas de los avisos del gemelo, pero ninguna cifra ni nombre de indicador de carbono
    expect(texto(s)).not.toMatch(/t C\/ha/)
    for (const k of ['cambio_carbono_t_ha', 'cambio_carbono_t_ha_anio']) expect(s).not.toContain(cat[`indicator.${k}.name`])
    expect(s).not.toContain(cat['objective.carbono'])
  })
})

describe('tablero', () => {
  const s = renderToStaticMarkup(h(Tablero, { d, pesos: PESOS_IGUALES, escenario: 'historico', setEscenario: () => {} }))
  it('fichas de la secuencia de la primera estrategia, gráfico con banda y comparador de 2 indicadores', () => {
    expect(s).toContain(t('rotaciones.fichas'))
    expect((s.match(/class="ficha"/g) ?? []).length).toBe(sim.estrategias.find((e) => e.id === 'C')!.temporadas.length)
    expect(s).toContain('class="banda"')
    expect((s.match(/data-testid="fila-escenario"/g) ?? []).length).toBe(sim.estrategias.length)
    expect(s).toContain('Erosive exposure index')
    expect(s).toContain('Drainage')
  })
  it('rótulo del método real, sin IMERG, SMAP, CDL, GAEZ ni ENSO', () => {
    expect(s).toContain(t('rotaciones.metodo'))
    expect(texto(s)).not.toMatch(/IMERG|SMAP|CDL|GAEZ|ONI|ERA5/)
  })
  it('el orden con pesos iguales es el del paquete en los 14 archivos de simulación', () => {
    for (const l of ['DEMO-COL-01', 'DEMO-USA-01']) {
      const lj = leer<LoteJson>(`gemelo/${l}/lote.json`)
      for (const v of [...Object.values(lj.escenarios), ...Object.values(lj.escenarios_enso)]) {
        const x = leer<Simulacion>(`gemelo/${v.simulacion}`)
        expect(ordenSimulacion(x, PESOS_IGUALES), v.simulacion).toEqual(x.prioridades.pesos_iguales.orden)
      }
    }
  })
  it('los deslizadores reordenan: solo suelo pone primero a la de menor exposición erosiva entre las de más carbono', () => {
    const soloSuelo = ordenSimulacion(sim, { agua: 0, suelo: 5, insumos: 0, estabilidad_climatica: 0 })
    expect(soloSuelo[0]).toBe('D')
    expect(soloSuelo).not.toEqual(ordenSimulacion(sim, PESOS_IGUALES))
  })
})
