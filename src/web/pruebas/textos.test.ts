// asistido por SI: Claude Code (Anthropic), escritura y revisión de código; base del prototipo migrada en el hackatón
import { createElement } from 'react'
import { renderToStaticMarkup } from 'react-dom/server'
import { describe, expect, it } from 'vitest'
import { Cabecera } from '../src/app/Cabecera'
import { en } from '../src/textos/en'
import { FALTANTES_ES, es } from '../src/textos/es'
import { GLOSARIO } from '../src/textos/glosario'
import { BANDA } from '../src/textos/avisos'
import * as avisos from '../src/textos/avisos'
import { alternar, idioma, t } from '../src/textos/i18n'
import { detalle } from '../src/textos/modos'

describe('textos', () => {
  it('es tiene todas las claves de en salvo las listadas en FALTANTES_ES, sin textos vacíos', () => {
    expect([...Object.keys(es), ...FALTANTES_ES].sort()).toEqual(Object.keys(en).sort())
    for (const f of FALTANTES_ES) expect(es).not.toHaveProperty(f)
    for (const v of [...Object.values(es), ...Object.values(en)]) expect(v!.trim().length).toBeGreaterThan(0)
  })
  it('claves de sección y avisos del glosario §2 en los dos idiomas', () => {
    for (const k of ['aviso.apoyo', 'aviso.sin_dato', 'aviso.simulado', 'seccion.portada', 'seccion.fuentes'] as const) {
      expect(en[k]).toBeTruthy()
      expect(es[k]).toBeTruthy()
    }
  })
  it('t() cambia con el idioma', () => {
    const antes = t('ayuda.titulo')
    alternar()
    expect(idioma()).toBe('es')
    expect(t('ayuda.titulo')).not.toBe(antes)
    alternar()
  })
  it('glosario con términos reales, definición bilingüe y fuente', () => {
    const ids = GLOSARIO.map((g) => g.termino)
    for (const k of ['SMAP', 'IMERG', 'GRACE', 'NDVI', 'Condición de la tierra']) expect(ids).toContain(k)
    for (const g of GLOSARIO) expect(g.es && g.en && g.fuente).toBeTruthy()
  })
  it('avisos obligatorios y ninguna licencia NC listada en los avisos', () => {
    // web_componentes §9: SIMULADO va por variable o por valor, nunca en la cabecera
    expect(BANDA).not.toContain('SIMULADO')
    expect(es['aviso.apoyo']).toContain('no reemplaza el criterio del agricultor ni del técnico')
    // EOX y Köppen-Geiger salieron por decisión del director; GADM y WorldClim antes (D-002, D-004)
    expect(JSON.stringify(avisos)).not.toMatch(/EOX|K[öo]ppen/i)
  })
  it('el glosario de la ayuda no lleva ninguna cifra escrita a mano', () => {
    // El nombre del término (ADM1 / ADM2) es un código, no una cifra; definiciones y fuentes no llevan dígitos
    for (const g of GLOSARIO) expect([g.es, g.en, g.tecnico, g.fuente].join(' '), g.termino).not.toMatch(/\d/)
  })
  it('GADM y WorldClim ya no aparecen en nada visible de los textos', () => {
    const visible = JSON.stringify([es, en, GLOSARIO, avisos])
    for (const fuera of ['GADM', 'WorldClim']) expect(visible).not.toContain(fuera)
    expect(GLOSARIO.find((g) => g.termino === 'ADM1 / ADM2')?.tecnico).toContain('CGAZ')
  })
  it('ningún texto menciona Google Earth', () => {
    expect(JSON.stringify([es, en, GLOSARIO]).toLowerCase()).not.toContain('google')
  })
  it('modo técnico agrega detalle; agricultor no', () => {
    expect(detalle('agricultor', 'x', 'y')).toBe('x')
    expect(detalle('tecnico', 'x', 'y')).toBe('x y')
  })
  it('cabecera: ayuda e idioma son botones con nombre y la marca sin SIMULADO ni DEMO', () => {
    const h = renderToStaticMarkup(createElement(Cabecera))
    expect(h).not.toContain('SIMULADO')
    expect(h).not.toContain('DEMO')
    expect(h).toContain('>AGROVERSEx<')
    expect(h).toMatch(/<button[^>]*aria-label="Help[^"]*"/)
    expect(h).toMatch(/<button[^>]*aria-label="Language[^"]*"/)
  })
})
