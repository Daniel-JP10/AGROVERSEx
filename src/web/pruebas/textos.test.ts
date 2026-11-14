// asistido por SI: Claude Code (Anthropic), escritura y revisión de código; base del prototipo migrada en el hackatón
import { createElement } from 'react'
import { renderToStaticMarkup } from 'react-dom/server'
import { describe, expect, it } from 'vitest'
import { Cabecera } from '../src/app/Cabecera'
import { en } from '../src/textos/en'
import { es } from '../src/textos/es'
import { GLOSARIO } from '../src/textos/glosario'
import { AVISO_N7, BANDA, LICENCIAS_NC } from '../src/textos/avisos'
import { alternar, idioma, t } from '../src/textos/i18n'
import { detalle } from '../src/textos/modos'

describe('textos', () => {
  it('toda clave de es existe en en y viceversa, sin textos vacíos', () => {
    expect(Object.keys(en).sort()).toEqual(Object.keys(es).sort())
    for (const v of [...Object.values(es), ...Object.values(en)]) expect(v.trim().length).toBeGreaterThan(0)
  })
  it('t() cambia con el idioma', () => {
    const antes = t('ayuda.titulo')
    alternar()
    expect(idioma()).toBe('en')
    expect(t('ayuda.titulo')).not.toBe(antes)
    alternar()
  })
  it('glosario con términos reales, definición bilingüe y fuente', () => {
    const ids = GLOSARIO.map((g) => g.termino)
    for (const k of ['SMAP', 'IMERG', 'GRACE', 'NDVI', 'Condición de la tierra']) expect(ids).toContain(k)
    for (const g of GLOSARIO) expect(g.es && g.en && g.fuente).toBeTruthy()
  })
  it('avisos obligatorios y licencias NC', () => {
    expect(BANDA).toContain('SIMULADO · DEMO')
    expect(AVISO_N7).toContain('no reemplaza el criterio del agricultor ni del técnico')
    for (const l of ['GADM', 'EOX', 'WorldClim', 'Köppen']) expect(LICENCIAS_NC.join(' ')).toContain(l)
  })
  it('ningún texto menciona Google Earth', () => {
    expect(JSON.stringify([es, en, GLOSARIO]).toLowerCase()).not.toContain('google')
  })
  it('modo técnico agrega detalle; agricultor no', () => {
    expect(detalle('agricultor', 'x', 'y')).toBe('x')
    expect(detalle('tecnico', 'x', 'y')).toBe('x y')
  })
  it('cabecera: ayuda e idioma son botones con nombre y banda visibles', () => {
    const h = renderToStaticMarkup(createElement(Cabecera))
    expect(h).toContain('SIMULADO · DEMO')
    expect(h).toMatch(/<button[^>]*aria-label="Ayuda[^"]*"/)
    expect(h).toMatch(/<button[^>]*aria-label="Idioma[^"]*"/)
  })
})
