// asistido por SI: Claude Code (Anthropic), prueba de que unidades, pestañas del panel, aria de la serie y aviso de zoom salen en inglés por defecto (C-1)
import { readFileSync } from 'node:fs'
import { describe, expect, it } from 'vitest'
import { paraMostrar } from '../src/comun/unidades'
import { capaPorId } from '../src/datos/capas'
import { en } from '../src/textos/en'
import { es } from '../src/textos/es'

// Sin fijar idioma: la app arranca en inglés (C3); nada de lo visible puede quedar en español
const fuente = (ruta: string) => readFileSync(new URL(`../src/${ruta}`, import.meta.url), 'utf8')

describe('español visible en modo inglés (C-1)', () => {
  it('las unidades de lluvia y NDVI se muestran en inglés', () => {
    expect(paraMostrar('precip', 1, 'mm/h', '2024-02').unidad).toBe(en['unidad.mmMes'])
    expect(paraMostrar('ndvi', 0.6, 'adim', '2024-01').unidad).toBe(en['unidad.adimensional'])
    expect(capaPorId('precip').unidad).toBe(en['unidad.mmMes'])
    expect(capaPorId('ndvi').unidad).toBe(en['unidad.adimensional'])
    expect([en['unidad.mmMes'], en['unidad.adimensional']]).not.toContain('mm/mes')
  })
  it('cada pestaña del panel tiene etiqueta en los dos idiomas y el panel no pinta el id', () => {
    for (const p of ['Resumen', 'Series', 'Suelo', 'Rotaciones', 'Lotes', 'Fuentes']) {
      const k = `panel.tab.${p}` as keyof typeof en
      expect(en[k], k).toBeTruthy()
      expect(es[k], k).toBeTruthy()
      expect(en[k], k).not.toBe(es[k])
    }
    expect(fuente('paneles/PanelRegion.tsx')).not.toContain('>{p}<')
  })
  it('el aria de la serie y el aviso de zoom no llevan texto en español escrito en el código', () => {
    for (const frase of ['Serie mensual de', 'meses con dato', 'huecos sin interpolar']) expect(fuente('graficos/BandaSerie.tsx')).not.toContain(frase)
    expect(fuente('herramientas/AvisoZoom.tsx')).not.toContain('el mapa pasa a 2D')
  })
})
