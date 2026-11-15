// asistido por SI: Claude Code (Anthropic), sección Datos abiertos: ficha y descargas leídas del manifiesto de web_datos v0
import { useEffect, useState } from 'react'
import { t, useIdioma } from '../../textos/i18n'
import type { ClaveTexto } from '../../textos/en'
import { cargarManifiesto } from './manifiesto'
import './datos.css'

const CAMPOS = ['contenido', 'periodo', 'variables', 'cobertura', 'licencia', 'atribuciones', 'cita'] as const
type Campo = (typeof CAMPOS)[number]
// La ficha la arma manifiesto.ts desde datos/manifiesto.json; lo que no esté ahí queda sin dato
export type FichaDatos = { campos?: Partial<Record<Campo, string>>; descargas?: { nombre: string; url: string; sha256?: string }[]; comando?: string }

// Enlace https o archivo del mismo sitio bajo datos/: un dato mal formado no puede ejecutar nada
const enlaceSeguro = (u: string) => /^https:\/\//.test(u) || (u.startsWith(`${import.meta.env.BASE_URL}datos/`) && !u.includes('..') && !/^\/\//.test(u))

const SinDato = () => <span className="sin-dato">{t('aviso.sin_dato')}</span>

function Comando({ comando }: { comando: string }) {
  const [copiado, setCopiado] = useState(false)
  const copiar = () => { void navigator.clipboard?.writeText(comando).then(() => setCopiado(true), () => setCopiado(false)) }
  return (
    <>
      <pre><code>{comando}</code></pre>
      <button type="button" onClick={copiar}>{copiado ? t('datos.copiado') : t('datos.copiar')}</button>
    </>
  )
}

export function DatosAbiertos({ campos = {}, descargas = [], comando }: FichaDatos = {}) {
  useIdioma()
  const enlaces = descargas.filter((d) => enlaceSeguro(d.url))
  const vacia = !CAMPOS.some((c) => campos[c]) && enlaces.length === 0 && !comando
  return (
    <main className="seccion datos">
      <h1>{t('seccion.datos')}</h1>
      <p>{t('datos.descripcion')}</p>
      {vacia && <p className="sin-dato" role="status">{t('aviso.sin_dato')}</p>}
      <section aria-labelledby="d-campos">
        <h2 id="d-campos">{t('datos.campos_titulo')}</h2>
        <dl>
          {CAMPOS.map((c) => <div key={c} data-campo={c}><dt>{t(`datos.campo_${c}` as ClaveTexto)}</dt><dd>{campos[c] ?? <SinDato />}</dd></div>)}
        </dl>
      </section>
      <section aria-labelledby="d-descarga">
        <h2 id="d-descarga">{t('datos.descarga_titulo')}</h2>
        {enlaces.length
          ? <ul className="descargas">{enlaces.map((d) => <li key={d.url}><a className="boton" href={d.url} download rel="noopener">{d.nombre}</a>{d.sha256 && <> <small>{t('datos.huella')} <code>{d.sha256}</code></small></>}</li>)}</ul>
          : <p><SinDato /></p>}
      </section>
      <section aria-labelledby="d-comando">
        <h2 id="d-comando">{t('datos.comando_titulo')}</h2>
        {comando ? <Comando comando={comando} /> : <p><SinDato /></p>}
      </section>
    </main>
  )
}

/** Sección montada en la ruta: lee el manifiesto público; si no llega, todo queda "dato no disponible". */
export function DatosAbiertosSeccion() {
  const [ficha, setFicha] = useState<FichaDatos>({})
  useEffect(() => {
    let vivo = true
    void cargarManifiesto().then((f) => { if (vivo) setFicha(f) })
    return () => { vivo = false }
  }, [])
  return <DatosAbiertos {...ficha} />
}
