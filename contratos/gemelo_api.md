# Contrato del Gemelo · v1 (2026-11-14)

Estado: v1 redactada por el Gemelo, pendiente de congelar por Daniel. Después de congelada, solo cambios aditivos (campos nuevos opcionales). La versión va en `version_contrato` de la entrada y en `metadatos.version_contrato` de la salida.

## Qué entrega el Gemelo

Una biblioteca de Python (`src/gemelo`) y una línea de comandos. Integración decide si la expone por HTTP; el Gemelo no levanta servidor.

| Uso | Biblioteca | Consola |
|-|-|-|
| Simular estrategias | `gemelo.simular(escenario)` | `python -m gemelo simular escenario.yaml -o salida.json [--sqlite base.sqlite]` |
| Buscar rotaciones (NSGA-II) | `gemelo.optimizar_rotacion(escenario)` | `python -m gemelo optimizar escenario.yaml -o salida.json [--sqlite base.sqlite]` |
| Catálogo de cultivos | `gemelo.parametros.cargar_catalogo()` | `python -m gemelo cultivos [--json]` |
| Definiciones (indicadores, objetivos, cultivos) | `gemelo.definiciones()` | `python -m gemelo definiciones` |

`escenario` es la ruta a un YAML o un `dict` con el mismo esquema. La salida es un `dict` serializable a JSON sin `NaN` (los valores no finitos salen como `null`). Requisitos: Python 3.12 y `requirements-gemelo.txt`; `src` en `PYTHONPATH` (igual que `pytest.ini`).

Errores: la biblioteca lanza `ValueError`, `KeyError` o `gemelo.procedencia.ParametroPendiente` (subclase de `ValueError`) con un mensaje en español para el usuario. La consola los imprime en `stderr` y sale con código 2.

## Entrada: escenario

Ejemplos completos: `ejemplos/escenario_ames.yaml` y `ejemplos/escenario_ipiales.yaml`.

| Clave | Obligatoria | Contenido |
|-|-|-|
| `version_contrato` | no (1) | Entero. Una versión mayor que la del Gemelo es error |
| `lote` | sí | `id`, `nombre`, `lat`, `lon`, `unidad_id` (formato de `unidades.md`), `clima_tipo` (`templado` o `tropical`, elige las reglas de sucesión), opcionales `finca_id`, `geometria_wkt`, `area_ha`, `zona_demo` |
| `clima` | sí | `fuente: power_csv` con `archivo` (CSV diario de NASA POWER, comunidad AG), o `fuente: sqlite_mensual` con `ruta`, `unidad_id`, `elevacion_m` (tabla `mensual` de la rama datos, desagregada a diario) |
| `suelo` | sí | `fuente: soilgrids_json` con `archivo` (respuesta REST de SoilGrids 2.0) y opcional `profundidad_m`, o `fuente: manual` con `arena`, `arcilla` (kg/kg), `mo_pct` (%), `cos_t_ha` (t C/ha, 0-30 cm), opcionales `cn_suelo`, `profundidad_m` |
| `escenario` | no | `tipo`: `historico` (por defecto), `seco`, `normal`, `humedo` o `personalizado`; `anios` (horizonte, 3); `max_miembros`, `n_miembros`, `anio_inicio`, `semilla`; solo en `personalizado`: `delta_precip_pct`, `delta_temp_c` |
| `simulacion` | no | `n_parametros` (8), `semilla` (42), `n_sub` (1), `equilibrio` (`completo`, `joven` o `ninguno`), `referencia` (id de la estrategia que representa el manejo actual; por defecto la primera) |
| `calibracion` | no | `{clave: valor}` con datos locales; ver claves abajo. Cada valor calibrado pasa a `FUENTE`, naturaleza `observado` y sin rango |
| `costos` | no | `moneda`, `riego_por_mm`, `n_por_kg`, `labranza`, `semilla: {cultivo: precio}`. Sin esta sección, el costo sale `PENDIENTE` |
| `estrategias` | sí para simular | Lista de `{id, nombre, etiqueta, descripcion, temporadas}` |
| `optimizacion` | sí para optimizar | Ver más abajo |

Las rutas relativas se resuelven primero desde la carpeta del YAML y luego desde el directorio de trabajo.

### Temporada

| Campo | Por defecto | Significado |
|-|-|-|
| `cultivo` | | id del catálogo (`maiz`, `soya`, `papa`, ...) |
| `siembra` | | Fecha nominal `A<año>-MM-DD`, p. ej. `A2-05-15` (año 2 del horizonte, 15 de mayo). Calendario de 365 días, sin 29 de febrero |
| `etapas` | FAO-56 Tabla 11 | `[inicial, desarrollo, media, final]` en días. Obligatoria para cultivos con etapas `PENDIENTE` |
| `etapas_variante` | primera | Texto de la variante FAO-56, p. ej. `"centro EE. UU."`, `Europa` |
| `riego` | `{modo: ninguno}` | `modo: automatico` repone a capacidad de campo al agotar `umbral` x RAW; `tope_mm` es la lámina bruta máxima en la temporada |
| `fertilizacion` | `[]` | `[{dia: días después de siembra, kg_n}]` |
| `cosechar` | `true` | `false`: cultivo de cobertura, no exporta producto y todo queda como residuo |
| `residuos` | `superficie` | `superficie` (protege el suelo) o `incorporar` |
| `labranza_siembra` | `false` | Labranza al sembrar: entierra el residuo superficial |

Las temporadas de una estrategia no pueden solaparse ni pasar del horizonte; un cultivo no apto o con parámetros `PENDIENTE` es error con el motivo.

### Claves de calibración

- Suelo: `suelo.arena`, `suelo.arcilla`, `suelo.mo_pct` (recalculan la hidráulica de Saxton y Rawls), `suelo.cos_t_ha`, `suelo.cn_suelo`, `suelo.profundidad_perfil_m`, `suelo.theta_cc`, `suelo.theta_pmp`, `suelo.theta_sat`, `suelo.ksat_mm_h`.
- Agua: `agua.<nombre>` de `src/gemelo/referencias/agua_suelo.yaml`, p. ej. `agua.fraccion_humedad_inicial`, `agua.eficiencia_riego`.
- Carbono y nitrógeno: `cn.<nombre>` de `carbono_nitrogeno.yaml`, p. ej. `cn.n_mineral_inicial_kg_ha` (análisis de suelo).
- Cultivo: `cultivo.<id>.<parametro>` con `kc_ini`, `kc_mid`, `kc_end`, `zr_max`, `p`, `altura_m`, `rue`, `t_base`, `t_opt`, `t_max`, `indice_cosecha`, `n_biomasa`, `indice_cosecha_n`, `ndfa`.

Una clave desconocida es error.

### Sección `optimizacion`

| Campo | Significado |
|-|-|
| `linea_base` | id de la estrategia actual; con ella se equilibra el carbono y se explican los compromisos |
| `campanias` | `[{nombre, fecha: "MM-DD", opciones: [ids]}]`: una ranura por campaña y año |
| `opciones` | `{id: {cultivo, cosechar, residuos, labranza_siembra, fertilizacion, etapas, etapas_variante}}` |
| `desfases_dias` | Desfases de siembra permitidos dentro de la campaña, p. ej. `[0, 14]` |
| `riego` | `{permitido, tope_mm_temporada, tope_mm_anio}` |
| `sucesion` | `{usar_reglas: true, clima, archivo, reglas}`. Por defecto usa las reglas `FUENTE` con intervalo numérico de `regla_sucesion` (copia en `src/gemelo/referencias/sucesion.yaml`) para `lote.clima_tipo` |
| `exigidos` | Cultivos que deben aparecer al menos una vez |
| `min_cosechas_por_anio` | 1 por defecto |
| `objetivos` | Subconjunto de `produccion`, `riesgo_produccion`, `carbono`, `exposicion_erosiva`, `lixiviacion`, `riego`, `costo` (este exige `costos`). Por defecto los cinco primeros, más `riego` si está permitido |
| `busqueda` | `poblacion` (24), `generaciones` (15), `miembros_clima` (4), `muestras_parametros` (3), `miembros_final` (8), `muestras_final` (8), `max_soluciones` (10) |

## Salida: documento JSON

Claves de primer nivel comunes:

| Clave | Contenido |
|-|-|
| `metadatos` | `version_contrato`, `version_modelo`, `tipo` (`simulacion` u `optimizacion`), `generado_utc`, `commit`, `semilla`, `huella_parametros` (sha256 de todos los parámetros con su procedencia, 16 caracteres), `naturaleza: simulado`, `paso_tiempo`, `horizonte_anios`, `miembros {estrategias, clima, parametros, total}`, `metodo_eto`, `umbral_lluvia_intensa_mm_dia`, `umbral_cobertura_protectora`, `carbono` (diagnóstico del equilibrio), `archivo_entrada` |
| `lote` | Lo recibido, más `clima_tipo` |
| `clima` | `fuente`, `anios`, `lat`, `elevacion_m`, `naturaleza` (`estimado` para POWER, `derivado` si viene de mensual), lluvia anual media y p10-p90, temperatura media, huecos rellenados |
| `escenario` | `tipo`, `anios_horizonte`, `n_miembros`, `anios_por_miembro` (años reales usados), deltas, `aviso` y, en seco/normal/húmedo, los años análogos |
| `suelo` | `fuente`, `avisos` y cada propiedad como parámetro con procedencia |
| `parametros` | Lista de todos los parámetros del modelo: `clave`, `valor`, `unidad`, `etiqueta` (FUENTE, INFERENCIA o SUPUESTO), `referencia`, `ficha` (EV-*), `rango`, `distribucion`, `contexto`, `naturaleza` |
| `comparacion_p50` | `{indicador: {estrategia_id: p50}}` para tablas rápidas |
| `avisos` | Textos para mostrar tal cual al usuario. El primero siempre aclara que los resultados son simulados |

### Estrategia simulada (`estrategias[]` en simulación; `linea_base` y `frente[]` en optimización)

| Campo | Contenido |
|-|-|
| `id`, `nombre`, `descripcion`, `etiqueta`, `secuencia` | Identificación; `secuencia` es `"maiz -> soya -> maiz"` |
| `temporadas[]` | La temporada de entrada más `siembra_legible`, `cosecha`, `cosecha_legible`, `etapas_dias` y `indicadores` de temporada |
| `indicadores` | `{nombre: {p10, p50, p90, unidad, definicion, explicacion}}` sobre todos los miembros (clima x parámetros) |
| `trayectoria_mensual` | `{variable: {p10: [...], p50: [...], p90: [...]}}`, 12 x horizonte meses. Estados (media del mes): `W` mm, `agua_raiz` fracción, `N` kg N/ha, `C` t C/ha, `B` kg MS/ha, `V` fracción, `desnudo` fracción. Flujos (suma del mes, mm o kg N/ha): `P`, `ETa`, `I_bruto`, `D`, `R`, `L_lix` |
| `estado_final_p50` | `[W mm, N kg N/ha, C t C/ha, B kg MS/ha, V]` |
| `n_miembros` | Miembros del ensamble de esta estrategia |

Indicadores de horizonte (las definiciones completas salen en el JSON y en `gemelo.definiciones()`):

| Indicador | Unidad |
|-|-|
| `produccion_relativa_anio` | temporadas equivalentes/año |
| `rendimiento_relativo`, `indice_productivo`, `deficit_relativo`, `cobertura_media` | adimensional |
| `riego_mm_anio`, `et_real_mm_anio`, `drenaje_mm_anio`, `escorrentia_mm_anio`, `exposicion_erosiva_mm_anio` | mm/año |
| `dias_estres_anio`, `dias_suelo_desnudo_anio` | días/año |
| `lixiviacion_n_kg_ha_anio`, `volatilizacion_n_kg_ha_anio`, `fijacion_n_kg_ha_anio`, `fertilizante_n_kg_ha_anio`, `exportacion_n_kg_ha_anio` | kg N/ha/año |
| `balance_n_mineral_kg_ha` | kg N/ha |
| `cambio_carbono_t_ha`, `cambio_carbono_t_ha_anio` | t C/ha, t C/ha/año |
| `costo_anio` | moneda/ha/año; `p50: null` y `etiqueta: PENDIENTE` sin precios |
| `cierre_balance_agua_mm` | mm (control numérico, ~1e-13) |

Indicadores de temporada: `rendimiento_kg_ha`, `rendimiento_pot_kg_ha`, `biomasa_kg_ha` (kg MS/ha), `rendimiento_relativo`, `aptitud_termica`, `deficit_relativo`, `lluvia_mm`, `riego_mm`, `et_real_mm`, `et_cultivo_mm`, `dias_estres`, `absorcion_n_kg_ha`, `fijacion_n_kg_ha`, `lixiviacion_n_kg_ha`.

### Solo en optimización

| Clave | Contenido |
|-|-|
| `objetivos` | `[{id, indicador, sentido (max o min), texto}]` |
| `restricciones` | Nombres de las restricciones g <= 0 |
| `linea_base` | Estrategia simulada, más `objetivos` en unidades naturales |
| `frente[]` | Estrategias candidatas (`P01`, ...), más `objetivos`, `frente_a_linea_base {gana, cede, similar}` (textos), `no_dominada_en_evaluacion_final`, `domina_a_linea_base` |
| `compromisos` | `mejor_por_objetivo {objetivo: id}`, `compromiso_equilibrado` (id), `explicacion` (textos). Nunca se presenta una solución como "óptima" |
| `busqueda` | Algoritmo, tamaños, evaluaciones, factibles, `historial` por generación, `semilla` |
| `reglas_sucesion` | Reglas aplicadas: `familia`, `cultivos`, `intervalo_anios`, `referencia` (EV-*) |

## SQLite (opcional, `--sqlite`)

Tablas `corrida` (documento completo en `documento`), `indicador (corrida_id, estrategia_id, indicador, unidad, p10, p50, p90)` y `trayectoria_mensual (corrida_id, estrategia_id, variable, mes, p10, p50, p90)`. Cada ejecución añade una corrida; no se borra nada.

## Reglas que Web debe respetar

- Mostrar siempre p10-p90 junto al p50 y el primer aviso (resultados simulados).
- Mostrar la `etiqueta` de cada estrategia y de los parámetros que se muestren (FUENTE, INFERENCIA, SUPUESTO).
- En optimización, presentar el frente como compromisos con `frente_a_linea_base`, no como recomendación única.
- Los cambios de carbono son diferencias frente al equilibrio con la estrategia de referencia (ver `metadatos.carbono`).
