// asistido por SI: Claude Code (Anthropic), pruebas de Ciencia y validación (plan v2 §6): cifras leídas de los archivos, campos completos, PI-D1 mundial oculto
import { readdirSync, readFileSync, statSync } from 'node:fs'
import { join } from 'node:path'
import { createElement } from 'react'
import { renderToStaticMarkup } from 'react-dom/server'
import { afterEach, describe, expect, it } from 'vitest'
import { Ciencia, TarjetaPiD1Mundo } from '../src/secciones/ciencia/Ciencia'
import { CAMPOS_BANDA_HLS, UMBRALES_PI_D1, VARIABLES_PI_D1, hls, rangoPiD1Mundo, temperatura } from '../src/secciones/ciencia/datos'
import { alternar, idioma } from '../src/textos/i18n'
import * as textos from '../src/textos/secciones/ciencia'

const RAIZ = join(__dirname, '..', '..', '..')
const leer = (r: string) => JSON.parse(readFileSync(join(RAIZ, r), 'utf8'))
const html = () => renderToStaticMarkup(createElement(Ciencia))
const texto = (h: string) => h.replace(/<svg[\s\S]*?<\/svg>/g, ' ').replace(/<[^>]+>/g, ' ').replace(/&#x27;/g, "'").replace(/\s+/g, ' ')
const tarjeta = (h: string, id: string) => h.split(`data-tarjeta="${id}"`)[1]?.split('</article>')[0] ?? ''
const en2 = (x: number, d = 2) => new Intl.NumberFormat('en', { minimumFractionDigits: d, maximumFractionDigits: d, signDisplay: 'always' }).format(x)

afterEach(() => { if (idioma() !== 'en') alternar() })

describe('ciencia: una tarjeta por afirmación', () => {
  it('cada tarjeta tiene cifra, intervalo, periodo, fuente y etiqueta', () => {
    const h = html()
    const ids = [...h.matchAll(/data-tarjeta="(\w+)"/g)].map((m) => m[1])
    expect(ids).toEqual(['estacion', 'temperatura', 'hls', 'lluvia_2026', 'pi_d1_colombia', 'pi_d1_mundo', 'erosion', 'confianza'])
    for (const id of ids) for (const c of ['cifra', 'intervalo', 'periodo', 'fuente', 'etiqueta']) expect(tarjeta(h, id), `${id}.${c}`).toContain(`data-campo="${c}"`)
  })
  it('la Tmín corregida muestra el sesgo, el MAE y su IC leídos del archivo, con la línea base cruda', () => {
    const v = leer('datos/lotes/validacion_temperatura_ipiales.json').comparaciones.T2M_MIN_vs_TMIN
    const t = texto(tarjeta(html(), 'temperatura'))
    expect(t).toContain(`bias ${en2(v.corregida_lote_2934m.sesgo_c)} °C`)
    expect(t).toContain(`Bias ${en2(v.corregida_lote_2934m.sesgo_c_ic95_bootstrap_anual[0])} to ${en2(v.corregida_lote_2934m.sesgo_c_ic95_bootstrap_anual[1])} °C`)
    expect(t).toContain(`bias ${en2(v.cruda_2553m.sesgo_c)} °C`)
    expect(t).toContain('WMO Resolution 40')
  })
  it('el nivel del intervalo (95) sale del nombre del campo que se usa, no del texto', () => {
    const v = leer('datos/lotes/validacion_temperatura_ipiales.json').comparaciones.T2M_MIN_vs_TMIN.corregida_lote_2934m
    expect(Object.keys(v)).toContain(`sesgo_c_ic${temperatura.nivel}_bootstrap_anual`)
    expect(texto(tarjeta(html(), 'temperatura'))).toContain(`(${temperatura.nivel} % bootstrap by year)`)
  })
  it('la banda de HLS usa los campos q05 y q95 que existen en cada mes', () => {
    for (const l of hls) for (const m of l.meses) for (const c of CAMPOS_BANDA_HLS) expect(typeof m[c], `${l.lote} ${m.mes} ${c}`).toBe('number')
    expect(texto(tarjeta(html(), 'hls'))).toMatch(/from the 5th to the 95th percentile/)
  })
  it('sesgos de lluvia frente a la estación, del archivo y sin intervalo inventado', () => {
    const c = leer('datos/lotes/comparacion_power_imerg.json').find((l: { lote_id: string }) => l.lote_id === 'DEMO-COL-01').contraste_estacion_ghcn_com00080370
    const t = texto(tarjeta(html(), 'estacion'))
    const p = (x: number) => new Intl.NumberFormat('en', { style: 'percent', minimumFractionDigits: 1, maximumFractionDigits: 1, signDisplay: 'always' }).format(x)
    expect(t).toContain(`NASA POWER ${p(c.sesgo_relativo_power_vs_ghcn)}, IMERG ${p(c.sesgo_relativo_imerg_vs_ghcn)}`)
    expect(tarjeta(html(), 'estacion')).toMatch(/data-campo="intervalo"><dt>Interval<\/dt><dd><span class="sin-dato">Not available yet</)
  })
  it('PI-D1 Colombia: umbrales y fracciones de las claves del archivo', () => {
    const d = leer('datos/evidencia/T-D2_pi_d1_colombia_2019_4var.json')
    const t = texto(tarjeta(html(), 'pi_d1_colombia'))
    for (const v of VARIABLES_PI_D1) for (const u of UMBRALES_PI_D1) {
      const fr = new Intl.NumberFormat('en', { style: 'percent', minimumFractionDigits: 1, maximumFractionDigits: 1 }).format(d[v].fraccion_unidades_con_dif_relativa_mayor_a[u])
      expect(t, `${v} ${u}`).toContain(`${fr} `)
    }
  })
  it('PI-D1 mundial se lee del informe (S1w) y sigue sabiendo leer el formato anterior', () => {
    const h = tarjeta(html(), 'pi_d1_mundo')
    expect(h).not.toContain('Not available yet')
    const informe = { precip: { total: { fraccion_mayor_a: { '10%': 0.2, '2%': 0.5 } } }, ndvi: { total: { fraccion_mayor_a: { '10%': 0.1, '2%': 0.4 } } } }
    expect(rangoPiD1Mundo(informe)).toEqual({ min: 0.1, max: 0.5, umbralAlto: 10, umbralBajo: 2 })
    expect(texto(renderToStaticMarkup(createElement(TarjetaPiD1Mundo, { informe })))).toContain('Between 10.0 and 50.0 % of unit-month pairs change with the definition (PI-D1).')
  })
  it('confianza por unidad dice "Not available yet" y ninguna cifra de carbono aparece', () => {
    const h = html()
    expect((tarjeta(h, 'confianza').match(/Not available yet/g) ?? []).length).toBe(5)
    expect(texto(h)).not.toMatch(/carbon|carbono|t C\b|C\/ha/i)
  })
  it('ningún hueco queda sin llenar y el español se pinta completo', () => {
    expect(texto(html())).not.toMatch(/\{\w+\}/)
    alternar()
    const t = texto(html())
    expect(t).not.toMatch(/\{\w+\}/)
    expect(t).toContain('Todavía no disponible')
    expect(t).toContain('Temperatura mínima corregida frente a la estación')
  })
  it('los textos de ciencia no llevan cifras escritas a mano, salvo nombres propios (PI-D1, MOD13C2, MERRA-2, Resolución 40 de la OMM)', () => {
    // "p10 a p90" es el nombre del rango del campo que se lee (D-039 punto 3): se ata al campo
    const erosion = leer('datos/lotes/exposicion_erosiva_lotes.json').lotes
    for (const l of Object.values(erosion) as { relieve_nasadem_30m: object }[]) expect(Object.keys(l.relieve_nasadem_30m)).toContain('pendiente_p10_p50_p90_m_m')
    for (const v of [...Object.values(textos.en), ...Object.values(textos.es)]) expect(v.replace(/\{\w+\}|PI-D1|MOD13C2|MERRA-2|Resolution 40|Resolución 40|p10|p90/g, ''), v).not.toMatch(/\d/)
  })
})

// Con PROHIBIDOS_DIST: de S4 solo llegan los agregados, ninguna estación del contraste
describe.runIf(!!process.env.PROHIBIDOS_DIST)('ciencia en dist', () => {
  it('el bundle no lleva la lista de estaciones de S4', () => {
    const dist = process.env.PROHIBIDOS_DIST!
    const js = (d: string): string[] => readdirSync(d).flatMap((n) => { const p = join(d, n); return statSync(p).isDirectory() ? js(p) : /\.js$/.test(n) ? [p] : [] })
    const todo = js(dist).map((p) => readFileSync(p, 'utf8')).join('\n')
    expect(todo).toContain('late_mm_dia')
    for (const id of ['CO000080001', 'ghcn_vs_imerg_final_adm2', 'ghcn_ultima_fecha_prcp_por_estacion']) expect(todo, id).not.toContain(id)
  })
})
