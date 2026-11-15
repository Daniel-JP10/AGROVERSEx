// asistido por SI: Claude Code (Anthropic), sección Datos abiertos: una tarjeta por archivo del manifiesto, licencia por archivo y notas D-038 y D-040 (plan v2 §6)
import { useEffect, useState } from 'react'
import { idioma, t, useIdioma, type ClaveTodo } from '../../textos/i18n'
import { enTodo } from '../../textos/indice'
import { cargarManifiesto, type ArchivoAbierto, type DatosManifiesto } from './manifiesto'
import './datos.css'

// Repositorio público de las teselas (D-040)
export const REPO_TESELAS = 'https://github.com/Daniel-JP10/agroversex-teselas'

const f = (clave: ClaveTodo, v: Record<string, string | number>) => t(clave).replace(/\{(\w+)\}/g, (m, k: string) => (k in v ? String(v[k]) : m))
const bytes = (n: number) => new Intl.NumberFormat(idioma(), { style: 'unit', unit: n >= 1e6 ? 'megabyte' : 'kilobyte', maximumFractionDigits: 1 }).format(n >= 1e6 ? n / 1e6 : n / 1e3)
const NoDisponible = () => <span className="sin-dato">{t('datos.a.no_disponible')}</span>
// Una clave que no existe (variable o nivel nuevos en el manifiesto) muestra el identificador tal cual
const tSi = (clave: string, crudo: string) => (clave in enTodo ? t(clave as ClaveTodo) : crudo)

function Fila({ etiqueta, children }: { etiqueta: ClaveTodo; children: React.ReactNode }) {
  return <div><dt>{t(etiqueta)}</dt><dd>{children ?? <NoDisponible />}</dd></div>
}

export function TarjetaArchivo({ a }: { a: ArchivoAbierto }) {
  const s = a.serie
  return (
    <article className="tarjeta-hoja" data-archivo={a.ruta}>
      <h2><code>{a.ruta}</code></h2>
      <dl>
        {s && <Fila etiqueta="datos.a.variable">{tSi(`datos.a.var.${s.variable}`, s.variable)} · {s.pais}</Fila>}
        {s && <Fila etiqueta="datos.a.nivel">{tSi(`datos.a.nivel.${s.nivel}`, String(s.nivel))}</Fila>}
        {s && <Fila etiqueta="datos.a.meses">{s.desde && s.hasta && s.meses !== undefined ? f('datos.a.meses_valor', { desde: s.desde, hasta: s.hasta, n: s.meses }) : null}</Fila>}
        {s && <Fila etiqueta="datos.a.producto">{s.productos.length ? s.productos.map((p) => <span key={`${p.producto}${p.version}`} className="linea">{[p.producto, p.version, p.estado].filter(Boolean).join(' · ')}</span>) : null}</Fila>}
        <Fila etiqueta="datos.a.bytes">{a.bytes !== undefined ? bytes(a.bytes) : null}</Fila>
        <Fila etiqueta="datos.a.sha">{a.sha256 ? <code className="sha">{a.sha256}</code> : null}</Fila>
        <Fila etiqueta="datos.a.licencia">{t(`datos.a.lic.${a.tipo}`)}</Fila>
      </dl>
      <a className="boton" href={a.url} download aria-label={f('datos.a.descargar', { ruta: a.ruta })}>{f('datos.a.descargar', { ruta: a.ruta.split('/').pop() ?? a.ruta })}</a>
    </article>
  )
}

/** Vista con el manifiesto ya leído; `null` = no se pudo leer, `undefined` = cargando. */
export function DatosAbiertos({ datos }: { datos: DatosManifiesto | null | undefined }) {
  useIdioma()
  return (
    <main className="seccion datos">
      <h1>{t('marco.nav.datos')}</h1>
      <p>{t('datos.a.intro')}</p>
      <div className="tarjetas notas">
        <article className="tarjeta-hoja" data-nota="gemelo">
          <h2>{t('datos.a.gemelo.titulo')}</h2>
          <p><span className="etiqueta-evidencia">{t('datos.a.gemelo.rotulo')}</span></p>
          <p>{t('datos.a.gemelo.texto')}</p>
        </article>
        <article className="tarjeta-hoja" data-nota="teselas">
          <h2>{t('datos.a.teselas.titulo')}</h2>
          <p>{t('datos.a.teselas.texto')}</p>
          <p><a href={REPO_TESELAS} rel="noreferrer">{t('datos.a.teselas.enlace')}</a></p>
        </article>
        <article className="tarjeta-hoja" data-nota="ghcn">
          <h2>{t('datos.a.ghcn.titulo')}</h2>
          <p>{t('datos.a.ghcn.texto')}</p>
        </article>
      </div>
      <h2 className="subtitulo">{t('datos.a.archivos')}</h2>
      {datos === undefined && <p role="status">{t('datos.a.cargando')}</p>}
      {datos === null && <p className="sin-dato" role="status">{t('datos.a.sin_manifiesto')}</p>}
      {datos && <>
        {datos.generado && <p className="generado">{f('datos.a.generado', { fecha: datos.generado.replace('T', ' ').replace(/Z$/, '') })}</p>}
        <div className="tarjetas">{datos.archivos.map((a) => <TarjetaArchivo key={a.ruta} a={a} />)}</div>
      </>}
    </main>
  )
}

/** Sección montada en la ruta: lee el manifiesto público en tiempo de ejecución. */
export function DatosAbiertosSeccion() {
  const [datos, setDatos] = useState<DatosManifiesto | null | undefined>(undefined)
  useEffect(() => {
    let vivo = true
    void cargarManifiesto().then((d) => { if (vivo) setDatos(d) })
    return () => { vivo = false }
  }, [])
  return <DatosAbiertos datos={datos} />
}
