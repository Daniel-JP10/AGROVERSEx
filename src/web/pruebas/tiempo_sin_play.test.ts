// asistido por SI: Claude Code (Anthropic), la línea de tiempo pública sin reproducción automática (director 16:54; medición en prueba_reproduccion_tiempo.json)
import { createElement } from 'react'
import { renderToStaticMarkup } from 'react-dom/server'
import { describe, expect, it, vi } from 'vitest'
import { t } from '../src/textos/i18n'

describe('línea de tiempo sin Play', () => {
  it('no ofrece Play ni Pause; el mes se elige con el deslizador y los pasos', async () => {
    // El almacén lee localStorage al importarse: se simula antes del import dinámico
    vi.stubGlobal('localStorage', { getItem: () => null, setItem: () => {}, removeItem: () => {} })
    const { LineaTiempo, REPRODUCCION_AUTOMATICA } = await import('../src/tiempo/LineaTiempo')
    expect(REPRODUCCION_AUTOMATICA).toBe(false)
    const h = renderToStaticMarkup(createElement(LineaTiempo))
    expect(h).not.toContain(`aria-label="${t('tiempo.reproducir')}"`)
    expect(h).not.toContain(`aria-label="${t('tiempo.pausar')}"`)
    expect(h).toContain(`aria-label="${t('tiempo.anterior')}"`)
    expect(h).toContain(`aria-label="${t('tiempo.siguiente')}"`)
    expect(h).toContain('type="range"')
    vi.unstubAllGlobals()
  })
})
