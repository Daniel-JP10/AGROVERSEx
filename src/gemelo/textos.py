# asistido por SI: Cursor (agente), escritura y revisión de código; núcleo del gemelo digital en el hackatón
"""Textos del gemelo como claves con parámetros, en inglés (idioma de la entrega) y español (contrato v1.1).

Cada clave tiene una plantilla con `{parametro}` en `en` y `es`. Los documentos llevan `{clave, parametros}` y Web
redacta con el catálogo (`catalogo()`, exportado en el paquete estático como textos/en.json y textos/es.json).
Los avisos que el núcleo sigue generando en español se traducen a clave con `clave_de_aviso`.
"""
import re

import yaml

from gemelo import indicadores as ind
from gemelo.optimizacion import OBJETIVOS
from gemelo.procedencia import REFERENCIAS

IDIOMAS = ("en", "es")

_BASE: dict[str, tuple[str, str]] = {
    # Rótulo de procedencia (metadatos.rotulo)
    "label.model_simulation": ("Model simulation with {fuentes} data", "Simulación del modelo con datos {fuentes}"),
    "source.nasa_power": ("NASA POWER", "NASA POWER"),
    "source.soilgrids": ("SoilGrids 2.0", "SoilGrids 2.0"),
    "source.agroversex_monthly": ("AGROVERSEx monthly table (disaggregated to daily)",
                                  "tabla mensual de AGROVERSEx (desagregada a diario)"),
    "source.user_soil": ("local soil analysis", "análisis de suelo local"),
    "source.datos_forcings": ("AGROVERSEx daily forcings", "forzantes diarios de AGROVERSEx"),
    "source.datos_soil": ("AGROVERSEx soil parameters", "parámetros de suelo de AGROVERSEx"),
    "joiner.and": ("and", "y"),
    # Avisos
    "warning.simulated": ("All results are simulated (nature 'simulado'): they estimate trends and trade-offs between "
                          "strategies; they are not measurements or harvest guarantees.",
                          "Todos los resultados son simulados (naturaleza 'simulado'): estiman tendencias y "
                          "compromisos entre estrategias, no son mediciones ni garantías de cosecha."),
    "warning.carbon_equilibrium": ("Carbon: the soil is assumed to be in equilibrium with the reference strategy "
                                   "(SUPUESTO); carbon changes read as differences from that management, not as an "
                                   "absolute trend.",
                                   "Carbono: se supone que el suelo está en equilibrio con la estrategia de referencia "
                                   "(SUPUESTO); los cambios de carbono se leen como diferencias frente a ese manejo, "
                                   "no como tendencia absoluta."),
    "warning.climate_gaps": ("Climate: short gaps filled by interpolation {huecos}",
                             "Clima: huecos cortos rellenados por interpolación {huecos}"),
    "warning.climate_nature": ("Climate of nature '{naturaleza}' ({fuente})", "Clima de naturaleza '{naturaleza}' ({fuente})"),
    "warning.scenario_hypothetical": ("Hypothetical scenario built from real historical years; it is not a forecast "
                                      "or an official climate projection.",
                                      "Escenario hipotético construido con años históricos reales; no es un pronóstico "
                                      "ni una proyección climática oficial."),
    "warning.scenario_historical": ("Real historical climate in multi-year windows: it describes the past variability "
                                    "of the site, it does not guarantee the future one.",
                                    "Clima histórico real en ventanas de varios años: describe la variabilidad pasada "
                                    "del lugar, no garantiza la futura."),
    "warning.soil_cn_fallback": ("Soil C:N missing from SoilGrids: the SUPUESTO fallback is used",
                                 "C:N del suelo sin dato de SoilGrids: se usa el respaldo SUPUESTO"),
    "warning.initial_n": ("Initial mineral N without soil analysis (SUPUESTO 10-60 kg N/ha): the N balance is indicative",
                          "N mineral inicial sin análisis de suelo (SUPUESTO 10-60 kg N/ha): el balance de N es "
                          "orientativo"),
    "warning.initial_moisture": ("Initial soil moisture SUPUESTO (20-80 % of available water); SMAP L4 or a local "
                                 "measurement reduces the uncertainty of the first cycle",
                                 "Humedad inicial del suelo SUPUESTO (20-80 % del agua disponible); con SMAP L4 o "
                                 "medición local se reduce la incertidumbre del primer ciclo"),
    "warning.saxton_rawls_domain": ("Saxton and Rawls out of domain ({excede}); inputs clipped to the limit. Soils with "
                                    "high organic matter or volcanic soils (Andisols) usually hold more water than "
                                    "estimated: measure field capacity in a laboratory.",
                                    "Saxton y Rawls fuera de dominio ({excede}); entradas recortadas al límite. Los "
                                    "suelos con mucha materia orgánica o volcánicos (Andisoles) suelen retener más "
                                    "agua de la estimada: medir capacidad de campo en laboratorio."),
    "warning.succession_pending": ("Succession rule {familia} / {enfermedad} PENDIENTE: not applied",
                                   "Regla de sucesión {familia} / {enfermedad} PENDIENTE: no se aplica"),
    "warning.succession_family": ("Family {familia} has no match in the catalogue: rule not applied",
                                  "Familia {familia} sin correspondencia en el catálogo: regla no aplicada"),
    "warning.succession_none": ("The lot's climate has no succession rules with a numeric interval (INV-ROT §5.2): "
                                "succession does not restrict the search; review with the local agronomist",
                                "Clima del lote sin reglas de sucesión con intervalo numérico (INV-ROT §5.2): la "
                                "sucesión no restringe la búsqueda; revisar con el agrónomo local"),
    "warning.monthly_context_only": ("Monthly climate disaggregated to daily: context only. Splitting monthly rain "
                                     "into days erases storms, so heavy-rain and erosion indicators lose meaning.",
                                     "Clima mensual desagregado a diario: solo contexto. Al partir la lluvia mensual "
                                     "en días se borran las tormentas, y los indicadores de lluvia intensa y erosión "
                                     "pierden sentido."),
    "warning.enso_interim": ("ENSO phase derived from NOAA ONI (±0.5 °C, crop-year mean) as INFERENCIA while the "
                             "Datos classification is not delivered.",
                             "Fase ENSO derivada del ONI de NOAA (±0,5 °C, media del año) como INFERENCIA mientras "
                             "Datos no entrega su clasificación."),
    "warning.untranslated": ("{texto}", "{texto}"),
    # Escenarios
    "scenario.historico": ("Historical", "Histórico"),
    "scenario.seco": ("Dry", "Seco"),
    "scenario.normal": ("Normal", "Normal"),
    "scenario.humedo": ("Wet", "Húmedo"),
    "scenario.personalizado": ("Custom: rain {delta_precip_pct:+g} %, temperature {delta_temp_c:+g} °C",
                               "Personalizado: lluvia {delta_precip_pct:+g} %, temperatura {delta_temp_c:+g} °C"),
    "scenario.enso_nino": ("El Niño years", "Años El Niño"),
    "scenario.enso_nina": ("La Niña years", "Años La Niña"),
    "scenario.enso_neutra": ("ENSO-neutral years", "Años neutros ENSO"),
    # Deslizadores de prioridades de Web
    "priority.agua": ("Water", "Agua"),
    "priority.suelo": ("Soil", "Suelo"),
    "priority.insumos": ("Inputs", "Insumos"),
    "priority.estabilidad_climatica": ("Climate stability", "Estabilidad climática"),
    "priority.formula": ("Score = sum over sliders of weight x mean normalised objective of the slider, divided by "
                         "the sum of weights; 1 = best among the compared strategies",
                         "Puntaje = suma sobre deslizadores de peso x media de los objetivos normalizados del "
                         "deslizador, dividida por la suma de pesos; 1 = el mejor entre las estrategias comparadas"),
    # Compromisos de la optimización
    "tradeoff.no_single_best": ("No rotation is best at everything: the front gathers options where improving one "
                                "objective forces giving up another. The choice depends on the farmer's priorities.",
                                "Ninguna rotación es la mejor en todo: el frente reúne opciones donde mejorar un "
                                "objetivo obliga a ceder en otro. La elección depende de las prioridades del "
                                "productor."),
    "tradeoff.best_for": ("Best for {objetivo}: {id}", "Mejor en {objetivo}: {id}"),
    "tradeoff.balanced": ("Balanced trade-off (closest to the ideal with all objectives normalised and equal weight, "
                          "SUPUESTO): {id}",
                          "Compromiso equilibrado (más cercano al ideal con todos los objetivos normalizados y peso "
                          "igual, SUPUESTO): {id}"),
    "tradeoff.none_dominates": ("No candidate improves on the baseline in every objective at once.",
                                "Ninguna candidata mejora a la línea base en todos los objetivos a la vez."),
    # Tarjeta de cinco secciones
    "card.section.por_que": ("Why it is suggested", "Por qué se sugiere"),
    "card.section.evidencia": ("Supporting evidence", "Qué evidencia la respalda"),
    "card.section.beneficios": ("Benefits", "Beneficios"),
    "card.section.vacios": ("Information gaps", "Vacíos de información"),
    "card.section.riesgos": ("Risks for local review", "Riesgos para revisión local"),
    "card.why.is_baseline": ("This is the current management ({id}); the others are compared against it.",
                             "Es el manejo actual ({id}); las demás se comparan contra él."),
    "card.why.improves": ("Improves {objetivo}: {base} -> {valor} {unidad} (mean of the ensemble)",
                          "Mejora {objetivo}: {base} -> {valor} {unidad} (media del ensamble)"),
    "card.why.no_improvement": ("It does not improve any objective by more than {tolerancia_pct} % against the "
                                "baseline.",
                                "No mejora ningún objetivo en más de {tolerancia_pct} % frente a la línea base."),
    "card.why.front_member": ("Non-dominated candidate of the NSGA-II search (trade-off, not a single recommendation).",
                              "Candidata no dominada de la búsqueda NSGA-II (compromiso, no recomendación única)."),
    "card.evidence.label": ("Strategy label: {etiqueta}", "Etiqueta de la estrategia: {etiqueta}"),
    "card.evidence.parameters": ("{n_fuente} FUENTE, {n_inferencia} INFERENCIA and {n_supuesto} SUPUESTO parameters "
                                 "for the crops of this strategy",
                                 "{n_fuente} parámetros FUENTE, {n_inferencia} INFERENCIA y {n_supuesto} SUPUESTO "
                                 "para los cultivos de esta estrategia"),
    "card.evidence.references": ("Evidence sheets: {fichas}", "Fichas de evidencia: {fichas}"),
    "card.evidence.succession": ("Succession rule {familia}: {intervalo_anios} years ({referencia})",
                                 "Regla de sucesión {familia}: {intervalo_anios} años ({referencia})"),
    "card.evidence.model": ("Daily water, nitrogen, carbon and biomass simulation over {n_miembros} ensemble members "
                            "(climate x parameters)",
                            "Simulación diaria de agua, nitrógeno, carbono y biomasa sobre {n_miembros} miembros del "
                            "ensamble (clima x parámetros)"),
    "card.benefit.delta": ("{indicador}: {delta:+.3g} {unidad} against the baseline (p50; p10 {p10:.3g}, p90 {p90:.3g})",
                           "{indicador}: {delta:+.3g} {unidad} frente a la línea base (p50; p10 {p10:.3g}, p90 "
                           "{p90:.3g})"),
    "card.benefit.none": ("No indicator improves on the baseline beyond the tolerance.",
                          "Ningún indicador mejora a la línea base más allá de la tolerancia."),
    "card.gap.changes_order": ("SUPUESTO parameter {parametro} (range {lo} to {hi} {unidad}) changes this "
                               "strategy's position: {central} at the central value, {bajo} at the low end, "
                               "{alto} at the high end",
                               "El parámetro SUPUESTO {parametro} (rango {lo} a {hi} {unidad}) cambia la posición "
                               "de esta estrategia: {central} con el valor central, {bajo} en el extremo bajo, "
                               "{alto} en el extremo alto"),
    "card.gap.not_evaluated": ("Sensitivity of SUPUESTO parameters not evaluated in this document.",
                               "Sensibilidad de los parámetros SUPUESTO no evaluada en este documento."),
    "card.gap.none_changes": ("No SUPUESTO parameter changes this strategy's position within its range.",
                              "Ningún parámetro SUPUESTO cambia la posición de esta estrategia dentro de su rango."),
    "card.gap.cost_pending": ("Cost PENDIENTE: no prices; inputs are measured as applied nitrogen (D-007).",
                              "Costo PENDIENTE: sin precios; los insumos se miden como nitrógeno aplicado (D-007)."),
    "card.risk.gives_up": ("Gives up {objetivo}: {base} -> {valor} {unidad}",
                           "Cede en {objetivo}: {base} -> {valor} {unidad}"),
    "card.risk.worse_p10": ("In bad years (p10) {indicador} is {valor:.3g} {unidad} against {base:.3g} for the baseline",
                            "En años malos (p10) {indicador} es {valor:.3g} {unidad} frente a {base:.3g} de la línea "
                            "base"),
    "card.risk.not_modelled": ("Pests, diseases and weeds are not modelled; rotations that repeat a crop may look "
                               "better than they are.",
                               "Plagas, enfermedades y malezas no están representadas; las rotaciones que repiten un "
                               "cultivo pueden verse mejor de lo que son."),
    "card.risk.local_review": ("Review with a local agronomist before applying.",
                               "Revisar con un agrónomo local antes de aplicar."),
}


def _indicadores() -> dict[str, tuple[str, str]]:
    """Nombre y explicación de indicadores y objetivos: en del catálogo EN_INDICADORES, es de indicadores.py."""
    out = {}
    for k, (_, _, es) in ind.DEFINICIONES.items():
        en_nombre, en_expl = EN_INDICADORES.get(k, (k, es))
        out[f"indicator.{k}.name"] = (en_nombre, k.replace("_", " "))
        out[f"indicator.{k}.explanation"] = (en_expl, es)
    for k, meta in OBJETIVOS.items():
        out[f"objective.{k}"] = (EN_OBJETIVOS.get(k, k), meta["texto"])
    return out


EN_INDICADORES = {
    "riego_mm_anio": ("Irrigation", "Irrigation water applied (gross, includes application losses)"),
    "et_real_mm_anio": ("Actual evapotranspiration", "Water used by crop and soil (actual evapotranspiration)"),
    "drenaje_mm_anio": ("Drainage", "Water lost below the soil profile"),
    "escorrentia_mm_anio": ("Runoff", "Water that runs off the surface"),
    "deficit_relativo": ("Relative water deficit", "How much water the crop lacked against its demand (0 = none)"),
    "dias_estres_anio": ("Water-stress days", "Days with water stress"),
    "lixiviacion_n_kg_ha_anio": ("Nitrate leaching", "Nitrogen washed out with drainage"),
    "volatilizacion_n_kg_ha_anio": ("N volatilisation", "Fertiliser nitrogen lost to the air"),
    "fijacion_n_kg_ha_anio": ("N fixation", "Nitrogen fixed by legumes"),
    "fertilizante_n_kg_ha_anio": ("N fertiliser", "Nitrogen applied"),
    "exportacion_n_kg_ha_anio": ("N export", "Nitrogen removed with the harvest"),
    "balance_n_mineral_kg_ha": ("Mineral N balance", "Change of available nitrogen in the soil"),
    "cambio_carbono_t_ha": ("Soil carbon change", "Change of soil organic carbon (0-30 cm)"),
    "cambio_carbono_t_ha_anio": ("Soil carbon change per year", "Annual change of soil carbon"),
    "cobertura_media": ("Mean cover", "How much soil the vegetation covers on average"),
    "dias_suelo_desnudo_anio": ("Bare-soil days", "Days with unprotected soil"),
    "lluvia_intensa_sobre_suelo_desnudo_mm_anio": ("Heavy rain on bare soil", "Heavy rain falling on unprotected soil"),
    "exposicion_erosiva_mm_anio": ("Heavy rain on bare soil (obsolete name)",
                                   "Obsolete alias of lluvia_intensa_sobre_suelo_desnudo_mm_anio"),
    "rendimiento_relativo": ("Relative yield", "Harvest achieved against the possible one without water or N limits"),
    "indice_productivo": ("Productive index", "Harvest achieved against what the site's sunlight would allow; "
                                              "includes cold or heat effects"),
    "produccion_relativa_anio": ("Relative production per year",
                                 "Harvested production per year, in full-yield seasons (1 = one harvest at the site's "
                                 "radiation potential); allows comparing different crops"),
    "costo_anio": ("Direct cost", "Direct cost estimated with the user's prices"),
    "cierre_balance_agua_mm": ("Water balance closure", "Numerical error of the water balance (should be ~0)"),
}

EN_OBJETIVOS = {
    "produccion": "Harvested production (ensemble mean)",
    "riesgo_produccion": "Production in the worst 10 % of cases (CVaR 90 %): robustness to bad years",
    "carbono": "Soil carbon change (ensemble mean)",
    "lluvia_intensa_suelo_desnudo": "Heavy rain on unprotected soil (ensemble mean)",
    "exposicion_erosiva": "Heavy rain on unprotected soil (obsolete name)",
    "lixiviacion": "Leached nitrogen (ensemble mean)",
    "riego": "Irrigation water (ensemble mean)",
    "costo": "Direct cost (ensemble mean)",
    "deficit": "Relative water deficit (ensemble mean)",
    "fertilizante": "Applied nitrogen fertiliser (ensemble mean)",
}


# Unidades: español del núcleo -> inglés (orden: frases largas primero)
_UNIDAD_EN = (("temporadas equivalentes", "equivalent seasons"), ("fracción del agua disponible",
              "fraction of available water"), ("fracción del COS", "fraction of SOC"), ("fracción", "fraction"),
              ("adimensional", "dimensionless"), ("moneda", "currency"), ("percentil", "percentile"),
              ("índice 0=A..3=D", "index 0=A..3=D"), ("días", "days"), ("día", "day"), ("año", "yr"),
              ("MS", "DM"))
UNIDADES_FIJAS = ("%", "m³/m³", "mm/h", "kg/kg", "m", "mm", "kg C/kg N", "t C/ha", "índice 0=A..3=D")


def unidad_en(u: str) -> str:
    for es, en in _UNIDAD_EN:
        u = u.replace(es, en)
    return u


def _unidades() -> set[str]:
    us = {u for u, _, _ in ind.DEFINICIONES.values()} | {u for u, _ in ind.DEFINICIONES_TEMPORADA.values()}
    us |= set(UNIDADES_FIJAS)

    def recorrer(x):
        if isinstance(x, dict):
            if isinstance(x.get("unidad"), str):
                us.add(x["unidad"])
            for v in x.values():
                recorrer(v)
        elif isinstance(x, list):
            for v in x:
                recorrer(v)
    for f in REFERENCIAS.glob("*.yaml"):
        recorrer(yaml.safe_load(f.read_text(encoding="utf-8")))
    return us


def clave_unidad(u: str) -> dict:
    return {"clave": f"unit.{u}"}


_CATALOGO: dict | None = None


def catalogo() -> dict[str, dict[str, str]]:
    """{idioma: {clave: plantilla}} con todas las claves del gemelo."""
    global _CATALOGO
    if _CATALOGO is None:
        todo = {**_BASE, **_indicadores(), **{f"unit.{u}": (unidad_en(u), u) for u in _unidades()}}
        _CATALOGO = {idioma: {k: v[i] for k, v in sorted(todo.items())} for i, idioma in enumerate(IDIOMAS)}
    return _CATALOGO


def texto(c: str, idioma: str = "en", /, **parametros) -> str:
    """Plantilla de la clave `c` llena con los parámetros; un parámetro {"clave": ...} se traduce antes."""
    cat = catalogo()[idioma]
    llenos = {}
    for k, v in parametros.items():
        if isinstance(v, dict) and "clave" in v:
            llenos[k] = texto(v["clave"], idioma, **v.get("parametros", {})) if v["clave"] in cat else \
                v["clave"].split(".", 1)[-1]
        elif isinstance(v, list) and all(isinstance(x, str) and x in cat for x in v):
            llenos[k] = lista_fuentes(v, idioma)
        else:
            llenos[k] = v
    plantilla = cat[c]
    try:
        return plantilla.format(**llenos)
    except (KeyError, ValueError, IndexError):
        return plantilla


def clave(c: str, **parametros) -> dict:
    return {"clave": c, "parametros": parametros}


# Avisos en español que todavía genera el núcleo -> clave con parámetros
_PATRONES = [
    (r"^Todos los resultados son simulados", "warning.simulated", ()),
    (r"^Carbono: se supone que el suelo está en equilibrio", "warning.carbon_equilibrium", ()),
    (r"^Clima: huecos cortos rellenados por interpolación (?P<huecos>.+)$", "warning.climate_gaps", ("huecos",)),
    (r"^Clima de naturaleza '(?P<naturaleza>[^']+)' \((?P<fuente>.+)\)$", "warning.climate_nature",
     ("naturaleza", "fuente")),
    (r"^Escenario hipotético construido", "warning.scenario_hypothetical", ()),
    (r"^Clima histórico real en ventanas", "warning.scenario_historical", ()),
    (r"^C:N del suelo sin dato de SoilGrids", "warning.soil_cn_fallback", ()),
    (r"^N mineral inicial sin análisis de suelo", "warning.initial_n", ()),
    (r"^Humedad inicial del suelo SUPUESTO", "warning.initial_moisture", ()),
    (r"^Saxton y Rawls fuera de dominio \((?P<excede>[^)]*)\)", "warning.saxton_rawls_domain", ("excede",)),
    (r"^Regla de sucesión (?P<familia>.+) / (?P<enfermedad>.+) PENDIENTE", "warning.succession_pending",
     ("familia", "enfermedad")),
    (r"^Familia '?(?P<familia>[^']+)'? sin correspondencia", "warning.succession_family", ("familia",)),
    (r"^Clima del lote sin reglas de sucesión", "warning.succession_none", ()),
    (r"^Clima mensual desagregado a diario: solo contexto", "warning.monthly_context_only", ()),
    (r"^Fase ENSO derivada del ONI", "warning.enso_interim", ()),
]


def clave_de_aviso(aviso: str) -> dict:
    for patron, c, nombres in _PATRONES:
        m = re.search(patron, aviso)
        if m:
            return clave(c, **{n: m.group(n) for n in nombres})
    return clave("warning.untranslated", texto=aviso)


def lista_fuentes(claves_fuente: list[str], idioma: str) -> str:
    nombres = [catalogo()[idioma][c] for c in claves_fuente]
    if len(nombres) <= 1:
        return "".join(nombres)
    return f"{', '.join(nombres[:-1])} {texto('joiner.and', idioma)} {nombres[-1]}"
