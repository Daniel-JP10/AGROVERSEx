// asistido por SI: Claude Code (Anthropic), sección Rotaciones: lote por la ruta y salida del gemelo v1.1 con sus textos por clave
import { useState } from 'react'
import { irA, useRuta } from '../../app/ruta'
import { idioma, t } from '../../textos/i18n'
import type { ClaveTexto } from '../../textos/en'
import { Avisos } from './Avisos'
import { ComparadorEstrategias } from './ComparadorEstrategias'
import { AlertaHelada } from './AlertaHelada'
import { Compromisos } from './Compromisos'
import { FrentePareto } from './FrentePareto'
import { Deslizadores } from './Deslizadores'
import { ordenDelDocumento, PESOS_IGUALES, type Pesos } from './ordenPrioridades'
import type { Fuente, SalidaOptimizacion } from './gemelo'
import { useFuente } from './lector'
import { traducir, type Catalogo } from './textosGemelo'
import './rotaciones.css'

// Partes aún sin conectar: solo título y estado, ningún cálculo propio en Web
const PENDIENTES: ClaveTexto[] = ['rotaciones.escenarios', 'rotaciones.calibracion']

// Con catálogo, los textos salen de sus claves v1.1; sin él, de los textos en español de la v1
function textos(doc: SalidaOptimizacion, cat?: Catalogo) {
  const avisos = cat && doc.avisos_claves?.length ? doc.avisos_claves.map((a) => traducir(cat, a.clave, a.parametros)) : doc.avisos
  const objetivos = doc.objetivos.map((o) => (cat && o.texto_clave ? { ...o, texto: traducir(cat, o.texto_clave) } : o))
  return { avisos, objetivos }
}

// Rótulo: un ejemplo se ve SIMULADO; una corrida del modelo muestra metadatos.rotulo del gemelo (v1.1 §1)
function rotulo(f: Extract<Fuente, { estado: 'listo' }>): string {
  if (f.origen === 'ejemplo') return t('aviso.simulado')
  const r = f.doc.metadatos.rotulo
  return r?.[idioma()] ?? (r && f.catalogo ? traducir(f.catalogo, r.clave, r.parametros) : t('etiqueta.simulacion_modelo'))
}

export function VistaRotaciones({ fuente }: { fuente: Fuente }) {
  const [pesos, setPesos] = useState<Pesos>(PESOS_IGUALES)
  return (
    <main className="seccion rotaciones">
      <h1>{t('seccion.rotaciones')}</h1>
      <p>{t('rotaciones.descripcion')}</p>
      <p className="aviso-apoyo" role="note">{t('aviso.apoyo')}</p>
      {fuente.estado === 'sin_lote' && (
        <>
          <p>{t('rotaciones.sin_lote')}</p>
          <p><a href="#/tierra" onClick={(e) => { e.preventDefault(); irA('tierra') }}>{t('rotaciones.ir_tierra')}</a></p>
        </>
      )}
      {fuente.estado === 'cargando' && <p role="status">{t('rotaciones.cargando')}</p>}
      {(fuente.estado === 'sin_lote' || fuente.estado === 'sin_dato') && <p className="sin-dato" role="status">{t('aviso.sin_dato')}</p>}
      {fuente.estado === 'listo' && (
        <>
          {/* El rótulo lo decide el origen de los datos, no metadatos.naturaleza (en el gemelo siempre vale simulado) */}
          <p className="rotulo" data-testid="rotulo"><strong data-texto-gemelo="">{rotulo(fuente)}</strong></p>
          <Avisos avisos={textos(fuente.doc, fuente.catalogo).avisos} />
          <Deslizadores pesos={pesos} alCambiar={(k, v) => setPesos((p) => ({ ...p, [k]: v }))} />
          <ComparadorEstrategias linea_base={fuente.doc.linea_base} frente={fuente.doc.frente} tarjetas={fuente.doc.tarjetas} catalogo={fuente.catalogo} orden={ordenDelDocumento(fuente.doc, pesos)} />
          <FrentePareto objetivos={textos(fuente.doc, fuente.catalogo).objetivos} linea_base={fuente.doc.linea_base} frente={fuente.doc.frente} />
          <Compromisos frente={fuente.doc.frente} compromisos={fuente.doc.compromisos} />
          <section className="alertas" aria-labelledby="h-alertas">
            <h2 id="h-alertas">{t('rotaciones.alertas')}</h2>
            <AlertaHelada alerta={fuente.doc.alertas?.helada_etapa_sensible} estrategias={[fuente.doc.linea_base, ...fuente.doc.frente]} catalogo={fuente.catalogo} />
          </section>
          {PENDIENTES.map((k) => (
            <section key={k} className="pendiente">
              <h2>{t(k)}</h2>
              {k === 'rotaciones.escenarios' && <p>{t('aviso.escenario')}</p>}
              <p className="sin-dato">{t('rotaciones.pendiente_gemelo')}</p>
            </section>
          ))}
        </>
      )}
    </main>
  )
}

export function Rotaciones() {
  const { params } = useRuta()
  return <VistaRotaciones fuente={useFuente(params.lote)} />
}
