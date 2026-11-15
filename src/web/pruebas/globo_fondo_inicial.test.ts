// asistido por SI: Claude Code (Anthropic), prueba: la vista inicial no pide teselas GIBS del fondo de detalle (plan v1 §a, presupuesto)
import { describe, expect, it } from 'vitest'
import { construirEstilo } from '../src/globo/config'
import { ZOOM_DETALLE } from '../src/globo/fondos'

describe('fondo en la vista inicial', () => {
  it('el detalle lleva minzoom en su umbral de fundido: bajo él MapLibre no pide sus teselas', () => {
    const capas = (construirEstilo('http://x', true) as { layers: { id: string; minzoom?: number }[] }).layers
    expect(capas.find((c) => c.id === 'detalle')!.minzoom).toBe(ZOOM_DETALLE[0])
    // el zoom inicial del globo (1,6) queda debajo
    expect(1.6).toBeLessThan(ZOOM_DETALLE[0])
  })
})
