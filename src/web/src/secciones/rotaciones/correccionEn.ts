// asistido por SI: Claude Code (Anthropic), restos en español del catálogo y los paquetes del gemelo en la interfaz inglesa (H-F3-6, §5.3: la entrega va en inglés)
import type { Catalogo } from './textosGemelo'

// Etiquetas de evidencia del proyecto (AGENTS §6) en inglés
const EVIDENCIA: [RegExp, string][] = [[/\bSUPUESTO\b/g, 'assumed'], [/\bFUENTE\b/g, 'sourced'], [/\bINFERENCIA\b/g, 'inferred'], [/\bPENDIENTE\b/g, 'pending'], [/\bVERIFICADO\b/g, 'verified']]
const CULTIVOS: Record<string, string> = { avena_grano: 'oat (grain)', avena_cobertura: 'oat (cover)', papa: 'potato', avena: 'oat', frijol: 'bean', maiz: 'maize', soya: 'soybean' }
const RE_CULTIVO = /\b(avena_grano|avena_cobertura|papa|avena|frijol|maiz|soya)\b/g

// Cadenas planas de los paquetes, tal como vienen (inventario completo de public/gemelo, 2026-11-15)
const EXACTAS: Record<string, string> = {
  'FUENTE EV-ROT-017 (alternativa de 3 años; sin trébol rojo, que no está en el catálogo)': 'Sourced EV-ROT-017 (3-year alternative; without red clover, which is not in the crop catalogue)',
  'FUENTE EV-ROT-017 (rotación habitual del Corn Belt)': 'Sourced EV-ROT-017 (usual Corn Belt rotation)',
  'FUENTE EV-ROT-022 (alternativa de Agrosavia)': 'Sourced EV-ROT-022 (Agrosavia alternative)',
  'FUENTE EV-ROT-022 (alternativa papa-avena-arveja; frijol en lugar de arveja, que no está en el catálogo)': 'Sourced EV-ROT-022 (potato-oat-pea alternative; bean instead of pea, which is not in the crop catalogue)',
  'FUENTE EV-ROT-022 (lo común es repetir papa)': 'Sourced EV-ROT-022 (repeating potato is the common practice)',
  'candidata NSGA-II (compromiso, no recomendación única)': 'NSGA-II candidate (a trade-off, not a single recommendation)',
  ilustrativa: 'illustrative',
  estimado: 'estimated',
  'Nematodo de la avena': 'Oat nematode',
  'Nematodo del tallo, Sclerotinia': 'Stem nematode, Sclerotinia',
  'Avena y cebada': 'Oat and barley',
  'Trébol': 'Clover',
  'Papa-papa-avena': 'Potato-potato-oat',
  'Papa-avena-frijol-papa': 'Potato-oat-bean-potato',
  'Papa con avena de cobertura': 'Potato with an oat cover crop',
  'Maíz-soya (habitual)': 'Maize-soybean (usual)',
  'Maíz continuo': 'Continuous maize',
  'Maíz-soya-avena': 'Maize-soybean-oat',
  'Maíz-soya-maíz con avena de cobertura': 'Maize-soybean-maize with an oat cover crop',
}
// Parámetros de cultivo del catálogo del gemelo (cultivo.<cultivo>.<parámetro>)
const PARAMETROS: Record<string, string> = { n_biomasa: 'biomass N concentration', t_base: 'base temperature', t_max: 'maximum temperature', t_opt: 'optimum temperature', rue: 'radiation use efficiency', indice_cosecha: 'harvest index', indice_cosecha_n: 'N harvest index', ndfa: 'share of N fixed from the air (Ndfa)' }
// Unidades de los paquetes que no pasan por el catálogo
const UNIDADES: Record<string, string> = { 'índice': 'index', 'temporadas equivalentes/año': 'equivalent seasons/yr', 'kg N/ha/año': 'kg N/ha/yr', 't C/ha/año': 't C/ha/yr', 'mm/año': 'mm/yr', 'días/año': 'days/yr', 'fracción': 'fraction', adimensional: 'dimensionless' }

/** Una cadena plana del gemelo en inglés; lo que no reconoce queda igual (nunca se inventa). */
export function aIngles(s: string): string {
  if (s in EXACTAS) return EXACTAS[s]
  if (s in UNIDADES) return UNIDADES[s]
  const p = /^cultivo\.([a-z_]+)\.([a-z_]+)$/.exec(s)
  if (p && p[1] in CULTIVOS && p[2] in PARAMETROS) return `${CULTIVOS[p[1]]} ${PARAMETROS[p[2]]}`
  let r = s.replace(/NASA POWER diario \((power_[\w-]+_diario\.csv)\); MERRA-2 y CERES, celda 0,5° x 0,625°/, 'NASA POWER daily ($1); MERRA-2 and CERES, 0.5° x 0.625° cell')
  // Listas de cultivos ("avena, frijol, papa") y secuencias ("papa semestre A año 1 -> ...", "maiz principal año 1 -> ...")
  if (/^[a-z_]+(, [a-z_]+)*$/.test(r) || / (semestre [AB]|principal|otono) año \d/.test(r)) {
    r = r.replace(RE_CULTIVO, (c) => CULTIVOS[c]).replace(/semestre ([AB])/g, 'season $1').replace(/\bprincipal\b/g, 'main season').replace(/\botono\b/g, 'autumn').replace(/año (\d)/g, 'year $1')
  }
  for (const [re, en] of EVIDENCIA) r = r.replace(re, en)
  return r
}

/** Catálogo inglés con las etiquetas de evidencia en inglés y la marca para traducir parámetros planos. */
export function corregirCatalogoEn(cat: Catalogo): Catalogo {
  const out: Catalogo = { '__en': '1' }
  for (const [k, v] of Object.entries(cat)) out[k] = aIngles(v)
  out['unit.índice'] = 'index'
  return out
}
