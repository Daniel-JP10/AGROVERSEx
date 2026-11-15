// asistido por SI: Claude Code (Anthropic), prueba de que Tierra aplica unidad, variable y mes de la ruta (contrato web_componentes §3, D-037 C2)
import { describe, expect, it, vi } from 'vitest'

vi.stubGlobal('localStorage', { getItem: () => null, setItem: () => {} })
// el índice real es un archivo estático: aquí se llena a mano y cargarFilas no descarga nada
vi.mock('../src/datos/indice', async (orig) => ({ ...(await orig<typeof import('../src/datos/indice')>()), cargarFilas: async () => [] }))

const { aplicarParams } = await import('../src/secciones/tierra/aplicarRuta')
const { leerRuta } = await import('../src/app/ruta')
const { useEstado } = await import('../src/app/estado')
const { porClave } = await import('../src/datos/indice')

const IPIALES = 'COL-ADM2-7082276B52108893597118'
porClave.set(`2:${IPIALES}`, { id: IPIALES, nivel: 2, nombre: 'Ipiales', pais: 'Colombia' })

describe('aplicarParams', () => {
  it('la ruta de aceptación aplica los tres: unidad, variable y mes', async () => {
    const { params } = leerRuta(`#/tierra?unidad=${IPIALES}&variable=t2m&mes=2015-01`)
    expect(await aplicarParams(params)).toBe(true)
    const e = useEstado.getState()
    expect(e.seleccion?.id).toBe(IPIALES)
    expect(e.capa).toBe('t2m')
    expect(e.mes).toBe(15 * 12)
  })
  it('un cambio de hash vuelve a aplicar y lo que no viene en la ruta no se toca', async () => {
    await aplicarParams({ variable: 'ndvi', mes: '2020-06' })
    const e = useEstado.getState()
    expect(e.capa).toBe('ndvi')
    expect(e.mes).toBe(20 * 12 + 5)
    expect(e.seleccion?.id).toBe(IPIALES)
  })
  it('valores inválidos se ignoran y la unidad desconocida devuelve false', async () => {
    const antes = { ...useEstado.getState() }
    expect(await aplicarParams({ variable: 'inventada', mes: '2020-13' })).toBe(true)
    expect(useEstado.getState().capa).toBe(antes.capa)
    expect(useEstado.getState().mes).toBe(antes.mes)
    expect(await aplicarParams({ unidad: 'COL-ADM2-NOEXISTE' })).toBe(false)
    expect(await aplicarParams({ unidad: 'basura' })).toBe(false)
  })
})
