// asistido por SI: Claude Code (Anthropic), escritura y revisión de código; base del prototipo migrada en el hackatón
import { useEffect, useRef, useState } from 'react'
import { AVISO_N7, BANDA, FUENTES_AYUDA } from '../textos/avisos'
import { GLOSARIO } from '../textos/glosario'
import { alternar, t, useIdioma } from '../textos/i18n'
import { detalle, useModo, type Modo } from '../textos/modos'

export function Cabecera() {
  const lang = useIdioma()
  const { modo, set } = useModo()
  const [abierta, setAbierta] = useState(false)
  const cerrar = useRef<HTMLButtonElement>(null)
  useEffect(() => { if (abierta) cerrar.current?.focus() }, [abierta])
  return (
    <header className="banda" onKeyDown={(e) => e.key === 'Escape' && setAbierta(false)}>
      <span>{BANDA}</span>
      <div className="acciones">
        <button type="button" aria-label={t('ayuda.abrir')} aria-expanded={abierta} title={t('ayuda.abrir')} onClick={() => setAbierta(!abierta)}>?</button>
        <button type="button" lang={lang} aria-label={t('idioma.etiqueta')} title={t('idioma.etiqueta')} onClick={alternar}>{t('idioma.boton')}</button>
      </div>
      {abierta && (
        <section className="ayuda" role="dialog" aria-label={t('ayuda.titulo')}>
          <button type="button" ref={cerrar} onClick={() => setAbierta(false)}>{t('ayuda.cerrar')}</button>
          <h2>{t('ayuda.titulo')}</h2>
          <p>{t('ayuda.intro')}</p>
          <fieldset>
            <legend>{t('ayuda.modo')}</legend>
            {(['agricultor', 'tecnico'] as Modo[]).map((m) => (
              <label key={m}><input type="radio" name="modo" checked={modo === m} onChange={() => set(m)} /> {t(`modo.${m}`)}</label>
            ))}
            <p>{t('modo.nota')}</p>
          </fieldset>
          <h3>{t('ayuda.glosario')}</h3>
          <dl>
            {GLOSARIO.map((g) => (
              <div key={g.termino}>
                <dt>{g.termino}</dt>
                <dd>{detalle(modo, g[lang], g.tecnico)} <small>({g.fuente})</small></dd>
              </div>
            ))}
          </dl>
          <h3>{t('ayuda.fuentes')}</h3>
          <ul>{FUENTES_AYUDA.map((l) => <li key={l}>{l}</li>)}</ul>
          <p className="aviso-n7">{AVISO_N7}</p>
        </section>
      )}
    </header>
  )
}
