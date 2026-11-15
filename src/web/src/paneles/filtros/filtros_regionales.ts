// asistido por SI: Claude Code (Anthropic), escritura y revisión de código; base del prototipo migrada en el hackatón
import type { AtributosUnidad } from '../../datos/filtrar'
import { idioma, t } from '../../textos/i18n'
import type { ClaveTexto } from '../../textos/en'

export interface FiltroRegional { id: string; nombre: string; evidencia: string }
// El nombre de cada filtro es la clave filtros.reg.<id>; la evidencia se compone con claves sin cifras y las citas van tal cual

const TROPICO = 23.44
const PH_ACIDO = 5.5 // umbral SUPUESTO de acidez
const PENDIENTE_MIN = 7 // % de pendiente desde la que la erosión en laderas pide revisión
const z = (u: AtributosUnidad, ...claves: string[]) => !!u.zona && claves.some((c) => u.zona!.toLowerCase().includes(c))
const MACRO_SAL = ['cercano oriente', 'norte de áfrica', 'asia', 'europa', 'eurasia', 'latinoamérica']

// Condiciones de INICIAR §10.2 (SUPUESTO de diseño). Un atributo ausente nunca activa el filtro.
const REGLAS: [{ id: string; evidencia: () => string }, (u: AtributosUnidad) => boolean][] = [
  [{ id: 'piso_termico', evidencia: () => `NASADEM; ${t('filtros.reg.piso_termico.ev')} [INV-CLI §8.2]` },
    (u) => u.lat !== undefined && Math.abs(u.lat) <= TROPICO && u.elevMin !== undefined && u.elevMax !== undefined && u.elevMax - u.elevMin > 1000],
  [{ id: 'heladas', evidencia: () => 'POWER FROST_DAYS' }, (u) => u.heladas === true],
  [{ id: 'riego', evidencia: () => 'MIRCA2000, CC BY 4.0 [INV-ROT §7]' }, (u) => u.riego !== undefined],
  [{ id: 'agua_subterranea', evidencia: () => 'Rodell 2018 [INV-CLI §5]' }, (u) => u.grace === true],
  [{ id: 'salinidad', evidencia: () => `FAO/ITPS 2015 ${t('filtros.reg.y')} FAO 2024 [INV-SUE §5]` },
    (u) => !!u.macro && MACRO_SAL.includes(u.macro.toLowerCase())],
  [{ id: 'acidez', evidencia: () => `FAO/ITPS 2015; ${t('filtros.reg.acidez.ev')} < ${PH_ACIDO.toLocaleString(idioma())} ${t('filtros.reg.supuesto')}` },
    (u) => (u.ph !== undefined && u.ph < PH_ACIDO) || z(u, 'suroeste del pacífico')],
  [{ id: 'erosion_laderas', evidencia: () => `Borrelli 2017; ${t('filtros.reg.erosion_laderas.ev')} > ${PENDIENTE_MIN} % [INV-ROT §4.3]` },
    (u) => u.pendiente !== undefined && u.pendiente > PENDIENTE_MIN && u.cultivo === true],
  [{ id: 'safrinha', evidencia: () => `Embrapa ${t('filtros.reg.y')} ${t('filtros.reg.safrinha.ev')} [INV-ROT §6]` }, (u) => z(u, 'cerrado')],
  [{ id: 'kharif_rabi', evidencia: () => '[INV-ROT §6]' }, (u) => z(u, 'indogang', 'indo_gang')],
  [{ id: 'lluvia_unica', evidencia: () => t('filtros.reg.lluvia_unica.ev') }, (u) => u.unimodal === true && z(u, 'sahel', 'sabana')],
  [{ id: 'nematodo_papa', evidencia: () => `Globodera pallida, 57 % ${t('filtros.reg.nematodo_papa.resumen')} ${t('filtros.reg.y')} 60 % ${t('filtros.reg.nematodo_papa.discusion')} [INV-ROT §5.2]` }, (u) => z(u, 'andina_colombia')],
  [{ id: 'siembra_enso', evidencia: () => 'MacCarthy 2017' }, (u) => z(u, 'norte_ghana', 'ghana')],
  [{ id: 'fechas_reguladas', evidencia: () => `${t('filtros.reg.fechas_reguladas.ev')} [INV-ROT §6]; ${t('filtros.reg.fechas_reguladas.pdf')}` }, (u) => z(u, 'meta', 'llanos')],
  [{ id: 'hueco_alta_latitud', evidencia: () => t('filtros.reg.hueco_alta_latitud.ev') }, (u) => u.lat !== undefined && u.lat > 60],
]

export function filtrosRegionalesPara(u: AtributosUnidad): FiltroRegional[] {
  return REGLAS.filter(([, cond]) => cond(u)).map(([f]) => ({ id: f.id, nombre: t(`filtros.reg.${f.id}` as ClaveTexto), evidencia: f.evidencia() }))
}
