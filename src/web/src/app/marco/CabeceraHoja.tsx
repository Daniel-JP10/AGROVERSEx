// asistido por SI: Claude Code (Anthropic), cabecera hoja del marco común: marca, seis secciones, idioma, modo y ayuda
import { useEffect, useRef, useState } from 'react'
import { GLOSARIO } from '../../textos/glosario'
import { alternar, t, useIdioma } from '../../textos/i18n'
import { detalle, useModo, type Modo } from '../../textos/modos'
import { Navegacion } from '../Navegacion'
import { useRuta } from '../ruta'

// Contorno de hoja con puntas; solo decoración
function ContornoHoja() {
  return (
    <svg className="cabecera-contorno" viewBox="0 0 1000 64" preserveAspectRatio="none" aria-hidden="true" focusable="false">
      <path d="M0 0 H1000 C 975 6 965 30 940 46 C 920 60 900 64 870 64 H130 C 100 64 80 60 60 46 C 35 30 25 6 0 0 Z" />
    </svg>
  )
}

export function CabeceraHoja() {
  const lang = useIdioma()
  const { seccion } = useRuta()
  const { modo, set } = useModo()
  const [abierta, setAbierta] = useState(false)
  const cerrar = useRef<HTMLButtonElement>(null)
  useEffect(() => { if (abierta) cerrar.current?.focus() }, [abierta])
  return (
    <header className="cabecera-hoja" onKeyDown={(e) => e.key === 'Escape' && setAbierta(false)}>
      <ContornoHoja />
      {/* Sin SIMULADO ni DEMO en la cabecera (director, plan v2 §1) */}
      <a className="marca" href="#/" aria-label={t('marco.inicio')} aria-current={seccion === 'portada' ? 'page' : undefined}>AGROVERSEx</a>
      <Navegacion actual={seccion} />
      <div className="acciones">
        <div className="selector" role="group" aria-label={t('marco.modo.grupo')}>
          {(['agricultor', 'tecnico'] as Modo[]).map((m) => (
            <button key={m} type="button" aria-pressed={modo === m} onClick={() => set(m)}>{t(`marco.modo.${m}`)}</button>
          ))}
        </div>
        <button type="button" className="idioma" lang={lang} aria-label={t('idioma.etiqueta')} title={t('idioma.etiqueta')} onClick={alternar}>
          <span data-activo={lang === 'en' || undefined}>EN</span><span aria-hidden="true">/</span><span data-activo={lang === 'es' || undefined}>ES</span>
        </button>
        <button type="button" className="ayuda-boton" aria-label={t('ayuda.abrir')} aria-expanded={abierta} title={t('ayuda.abrir')} onClick={() => setAbierta(!abierta)}>?</button>
      </div>
      {abierta && (
        <section className="ayuda" role="dialog" aria-label={t('ayuda.titulo')}>
          <button type="button" ref={cerrar} onClick={() => setAbierta(false)}>{t('ayuda.cerrar')}</button>
          <h2>{t('ayuda.titulo')}</h2>
          <p>{t('ayuda.intro')}</p>
          <div className="modo-ayuda">
            <h3>{t('marco.modo.ayuda.titulo')}</h3>
            <p>{t('marco.modo.ayuda.texto')}</p>
          </div>
          <h3>{t('ayuda.glosario')}</h3>
          <dl>
            {GLOSARIO.map((g) => (
              <div key={g.termino}>
                <dt>{g.termino}</dt>
                <dd>{detalle(modo, g[lang], lang === 'en' ? g.tecnico_en : g.tecnico)} <small>({g.fuente})</small></dd>
              </div>
            ))}
          </dl>
          <p><a href="#/fuentes">{t('marco.nav.fuentes')}</a></p>
          <p className="aviso-n7">{t('aviso.apoyo')}</p>
        </section>
      )}
    </header>
  )
}
