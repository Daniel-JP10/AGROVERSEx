// asistido por SI: Claude Code (Anthropic), pruebas de la interfaz del globo (contrato web_componentes §4)
import { describe, expect, it, vi } from 'vitest'

// el almacén lee localStorage al importarse; en node no existe
vi.stubGlobal('localStorage', { getItem: () => null, setItem: () => {} })

const { irAUnidad, cambiarVariable, cambiarMes, activarComparador, alSeleccionar, abrirPestana, claveDeUnidadId } = await import('../src/secciones/tierra/interfaz')
const { useEstado } = await import('../src/app/estado')
const { porClave } = await import('../src/datos/indice')

describe('interfaz del globo', () => {
  it('cambiarVariable cambia la capa', () => {
    cambiarVariable('t2m')
    expect(useEstado.getState().capa).toBe('t2m')
  })
  it('cambiarMes acepta AAAA-MM y fija el índice desde 2000-01', () => {
    cambiarMes('2000-03')
    expect(useEstado.getState().mes).toBe(2)
    cambiarMes('2024-02')
    expect(useEstado.getState().mes).toBe(24 * 12 + 1)
  })
  it('cambiarMes rechaza otros formatos', () => {
    for (const malo of ['2024-2', '2024-13', '2024-00', '202402', 'marzo', '2024-02-01', '']) {
      expect(() => cambiarMes(malo), malo).toThrow()
    }
  })
  it('activarComparador y abrirPestana pasan por el almacén', () => {
    activarComparador(true)
    expect(useEstado.getState().herramienta).toBe('comparar')
    activarComparador(false)
    expect(useEstado.getState().herramienta).toBe('')
    abrirPestana('series')
    expect(useEstado.getState().pestana).toBe('series')
  })
  it('claveDeUnidadId acepta el unidad_id tal cual y rechaza el formato inválido', () => {
    expect(claveDeUnidadId('COL-ADM2-7082276B52108893597118')).toBe('2:COL-ADM2-7082276B52108893597118')
    expect(claveDeUnidadId('COL-ADM1-13589884B81785725414319')).toBe('1:COL-ADM1-13589884B81785725414319')
    expect(claveDeUnidadId('COL-ADM0')).toBe('0:COL-ADM0')
    expect(() => claveDeUnidadId('1.2_1')).toThrow()
  })
  it('alSeleccionar avisa al cambiar y devuelve la desuscripción', () => {
    const u = { id: 'COL-ADM2-X', nivel: 2, nombre: 'X', pais: 'COL' }
    porClave.set('2:COL-ADM2-X', u)
    const fn = vi.fn()
    const baja = alSeleccionar(fn)
    irAUnidad('COL-ADM2-X')
    expect(fn).toHaveBeenCalledTimes(1)
    expect(fn).toHaveBeenCalledWith('COL-ADM2-X')
    baja()
    useEstado.getState().seleccionar(null)
    expect(fn).toHaveBeenCalledTimes(1)
  })
})
