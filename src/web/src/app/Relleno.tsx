// asistido por SI: Claude Code (Anthropic), pinta un texto con huecos: valores marcados y "dato no disponible" donde falta
import { dato, rellenar, type Resolver } from '../textos/huecos'
import { t } from '../textos/i18n'

export function Relleno({ texto, resolver = dato }: { texto: string; resolver?: Resolver }) {
  return (
    <>
      {rellenar(texto, resolver).partes.map((p, i) =>
        p.t === 'texto' ? p.v : p.t === 'valor'
          ? <span key={i} data-dato="">{p.v}</span>
          : <span key={i} className="hueco" role="img" aria-label={t('aviso.sin_dato')}>—</span>)}
    </>
  )
}
