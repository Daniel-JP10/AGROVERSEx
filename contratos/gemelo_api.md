# Contrato del Gemelo · v1.1 (2026-11-14)

Estado: v1 congelada por Daniel el 2026-11-14. Desde entonces, solo cambios aditivos (campos nuevos opcionales). La v1.1 reúne esos cambios en la sección [v1.1](#v11-cambios-aditivos), en el orden pedido. La versión mayor va en `version_contrato` de la entrada y en `metadatos.version_contrato` de la salida (sigue siendo el entero `1`); la completa, en `metadatos.version_contrato_completa` (`"1.1"`).

## Qué entrega el Gemelo

Una biblioteca de Python (`src/gemelo`) y una línea de comandos. Integración decide si la expone por HTTP; el Gemelo no levanta servidor.

| Uso | Biblioteca | Consola |
|-|-|-|
| Simular estrategias | `gemelo.simular(escenario)` | `python -m gemelo simular escenario.yaml -o salida.json [--sqlite base.sqlite]` |
| Buscar rotaciones (NSGA-II) | `gemelo.optimizar_rotacion(escenario)` | `python -m gemelo optimizar escenario.yaml -o salida.json [--sqlite base.sqlite]` |
| Catálogo de cultivos | `gemelo.parametros.cargar_catalogo()` | `python -m gemelo cultivos [--json]` |
| Definiciones (indicadores, objetivos, cultivos) | `gemelo.definiciones()` | `python -m gemelo definiciones` |
| Paquete estático por lote (v1.1) | `gemelo.paquete.construir(yaml, lote_id, salida)` | `python -m gemelo paquete escenario.yaml --lote-id DEMO-COL-01 [--salida datos/publicos/gemelo] [--definitivo]` |

`escenario` es la ruta a un YAML o un `dict` con el mismo esquema. La salida es un `dict` serializable a JSON sin `NaN` (los valores no finitos salen como `null`). Requisitos: Python 3.12 y `requirements-gemelo.txt`; `src` en `PYTHONPATH` (igual que `pytest.ini`).

Errores: la biblioteca lanza `ValueError`, `KeyError` o `gemelo.procedencia.ParametroPendiente` (subclase de `ValueError`) con un mensaje en español para el usuario. La consola los imprime en `stderr` y sale con código 2.

## Entrada: escenario

Ejemplos completos: `ejemplos/escenario_ames.yaml` y `ejemplos/escenario_ipiales.yaml`.

| Clave | Obligatoria | Contenido |
|-|-|-|
| `version_contrato` | no (1) | Entero. Una versión mayor que la del Gemelo es error |
| `lote` | sí | `id`, `nombre`, `lat`, `lon`, `unidad_id` (formato de `unidades.md`), `clima_tipo` (`templado` o `tropical`, elige las reglas de sucesión), opcionales `finca_id`, `geometria_wkt`, `area_ha`, `zona_demo` |
| `clima` | sí | `fuente: power_csv` con `archivo` (CSV diario de NASA POWER, comunidad AG), `fuente: forzantes_diarios` (v1.1 §7), o `fuente: sqlite_mensual` con `ruta`, `unidad_id`, `elevacion_m` (tabla `mensual` de la rama datos, desagregada a diario; solo contexto) |
| `suelo` | sí | `fuente: soilgrids_json` con `archivo` (respuesta REST de SoilGrids 2.0) y opcional `profundidad_m`, o `fuente: manual` con `arena`, `arcilla` (kg/kg), `mo_pct` (%), `cos_t_ha` (t C/ha, 0-30 cm), opcionales `cn_suelo`, `profundidad_m` |
| `escenario` | no | `tipo`: `historico` (por defecto), `seco`, `normal`, `humedo`, `personalizado` o, desde v1.1, `enso_nino`, `enso_nina`, `enso_neutra` (con `enso_archivo` opcional, §8); `anios` (horizonte, 3); `max_miembros`, `n_miembros`, `anio_inicio`, `semilla`; solo en `personalizado`: `delta_precip_pct`, `delta_temp_c` |
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
| `objetivos` | Subconjunto de `produccion`, `riesgo_produccion`, `carbono`, `lluvia_intensa_suelo_desnudo` (v1: `exposicion_erosiva`, ver v1.1 §6), `lixiviacion`, `riego`, `costo` (este exige `costos`), y desde v1.1 `deficit` y `fertilizante`. Por defecto los cinco primeros, más `riego` si está permitido |
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
| `riego_mm_anio`, `et_real_mm_anio`, `drenaje_mm_anio`, `escorrentia_mm_anio`, `lluvia_intensa_sobre_suelo_desnudo_mm_anio` (alias obsoleto `exposicion_erosiva_mm_anio`, v1.1 §6) | mm/año |
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

## v1.1: cambios aditivos

Todo lo de esta sección se agrega sin quitar ni cambiar el tipo de nada de la v1. Los textos en español de la v1 (`avisos`, `explicacion`, `texto`, `frente_a_linea_base`, `compromisos.explicacion`) siguen saliendo; la v1.1 añade al lado sus claves de texto.

### 1. Paquete estático por lote

La app pública no tiene servidor: lee archivos precalculados. Carpeta fija: `datos/publicos/gemelo/`.

| Ruta (relativa a `datos/publicos/gemelo/`) | Contenido |
|-|-|
| `indice.json` | Lista de lotes con todos sus archivos, ejes de la grilla, calibraciones, `provisional`, `huella_parametros`, `rotulo`, `commit` y `generado_utc`. Web empieza siempre aquí |
| `textos/en.json`, `textos/es.json` | Catálogo de claves de texto (ver 3) |
| `<lote_id>/simulacion_<tipo>.json`, `<lote_id>/optimizacion_<tipo>.json` | `tipo` = `historico`, `seco`, `normal`, `humedo`. Documento v1 completo más los bloques v1.1 |
| `<lote_id>/simulacion_enso_<fase>.json` | `enso_nino`, `enso_nina`, `enso_neutra` (ver 8). Si una fase no tiene años en el registro, `indice.json` la marca `omitido` con el motivo |
| `<lote_id>/personalizados/simulacion_dp<±dp>_dt<±dt>.json` | Grilla de los deslizadores: `delta_precip_pct` de −30 a +30 cada 10 y `delta_temp_c` de 0 a +3 cada 1 (28 archivos; p. ej. `simulacion_dp-30_dt+0.json`, `simulacion_dp+0_dt+2.json`) |
| `<lote_id>/calibracion/<id>.json` | Ajustes de calibración típicos del lote (escenario histórico): `mo_laboratorio`, `n_inicial_bajo`, `n_inicial_alto`, `suelo_seco_al_inicio`, `suelo_humedo_al_inicio`. Valores en `indice.json` |
| `<lote_id>/lote.json` | La entrada del lote en `indice.json` |

- La grilla y las calibraciones simulan el **conjunto comparable** del lote (`indice.json` → `conjunto_comparable`): las estrategias del escenario más el frente de la optimización histórica. Así los deslizadores reordenan siempre las mismas candidatas.
- `indice.json` → `personalizados.n_parametros` dice cuántas muestras de parámetros usa la grilla (4 en lugar de 8, para que el paquete se genere en minutos).
- Se regenera con `python -m gemelo paquete <yaml> --lote-id <id>`. Mientras los lotes DEMO no estén elegidos, los ids son provisionales (`provisional: true`): Ames = `DEMO-USA-01`, Ipiales = `DEMO-COL-01`.
- **Rótulo**. `metadatos.naturaleza = "simulado"` significa salida del modelo, no SIMULADO (dato ficticio) en el sentido del proyecto. Web muestra `metadatos.rotulo`: `{clave: "label.model_simulation", parametros: {fuentes: [claves source.*]}, en, es}`, p. ej. «Model simulation with NASA POWER and SoilGrids 2.0 data».

### 2. Tarjeta de cinco secciones

`tarjetas: {estrategia_id: {por_que, evidencia, beneficios, vacios, riesgos, referencia, secciones_claves}}` en todos los documentos. Cada sección es una lista no vacía de entradas `{clave, parametros, valores, referencias}`: `clave` es una clave de texto, `parametros` llena su plantilla, `valores` trae los números sin redondear y `referencias` las fichas EV-* o fuentes.

| Sección | Contenido |
|-|-|
| `por_que` | Objetivos en que mejora a la referencia (> 2 %), con valor base y nuevo; si es candidata no dominada, lo dice; la referencia se identifica como manejo actual |
| `evidencia` | Etiqueta de la estrategia, cuántos parámetros FUENTE, INFERENCIA y SUPUESTO tienen sus cultivos, fichas EV-*, reglas de sucesión aplicadas y tamaño del ensamble |
| `beneficios` | Indicadores con p50 mejor que la referencia: delta, p10, p50, p90 y p50 de la referencia |
| `vacios` | Parámetros SUPUESTO que cambian la posición de la estrategia (orden con pesos iguales) al llevarlos a sus extremos, con las posiciones; costo PENDIENTE |
| `riesgos` | Objetivos en que cede, p10 de producción peor que la referencia, avisos de dominio (Andisoles, clima mensual, sucesión sin reglas), procesos no representados y revisión local |

- La referencia es `linea_base` en optimización y `estrategia_referencia` (nuevo, = `simulacion.referencia`) en simulación.
- `vacios` sale de `sensibilidad_supuestos` (en los documentos del paquete): uno a uno, cada parámetro SUPUESTO con rango se lleva al extremo bajo y al alto con el resto de theta en su valor central y 4 climas; se guardan el orden resultante, las posiciones y si cambia el mejor por objetivo. Fuera del paquete, `vacios` dice `card.gap.not_evaluated`.
- Un parámetro de la forma `{"clave": "objective.carbono"}` es una clave anidada: se traduce antes de insertarla.

### 3. Textos en inglés y español

- Claves con parámetros `{nombre}` (formato de Python, p. ej. `{delta:+.3g}`), mismo conjunto de claves y parámetros en `en` y `es`. La entrega va en inglés.
- Nuevos campos: `avisos_claves` (misma longitud y orden que `avisos`), `indicadores.*.nombre_clave` y `explicacion_clave`, `objetivos[].texto_clave`, `compromisos.explicacion_claves`, `prioridades.deslizadores.*.rotulo_clave` y todas las entradas de `tarjetas`.
- Familias: `label.*`, `source.*`, `warning.*`, `scenario.*`, `priority.*`, `tradeoff.*`, `card.*`, `indicator.<id>.name|explanation`, `objective.<id>`, `unit.<unidad>` (la unidad en español del núcleo es la clave; p. ej. `unit.kg N/ha/año` = "kg N/ha/yr"). Un parámetro con forma `{"clave": ...}` (p. ej. `unidad` en las tarjetas) se traduce antes de insertarlo; una lista de claves `source.*` se une con `joiner.and`. `warning.untranslated` solo aparece si el núcleo emite un aviso nuevo sin clave; las pruebas lo impiden para los avisos conocidos.

### 4. Prioridades del agricultor

Bloque `prioridades` en todos los documentos y `metricas` (valores naturales de todos los objetivos) en cada estrategia.

| Deslizador de Web | Objetivos del gemelo | Indicador | Sentido |
|-|-|-|-|
| `agua` | `riego`, `deficit` | `riego_mm_anio`, `deficit_relativo` | min, min |
| `suelo` | `carbono`, `lluvia_intensa_suelo_desnudo` | `cambio_carbono_t_ha_anio`, `lluvia_intensa_sobre_suelo_desnudo_mm_anio` | max, min |
| `insumos` | `fertilizante` | `fertilizante_n_kg_ha_anio` (D-007, mientras `costo` siga PENDIENTE) | min |
| `estabilidad_climatica` | `riesgo_produccion` | `produccion_relativa_anio`, CVaR 90 % (media del peor 10 %) | max |

Los valores son medias del ensamble (CVaR para `riesgo_produccion`), los mismos que usa la optimización. Fórmula exacta, sobre las estrategias del mismo documento (`linea_base` + `frente`, o `estrategias`):

\[
n_{o,s} = \frac{x_{o,s} - \min_o}{\max_o - \min_o}\ (\text{max}),\qquad n_{o,s} = \frac{\max_o - x_{o,s}}{\max_o - \min_o}\ (\text{min}),\qquad n_{o,s} = 0{,}5 \text{ si } \max_o = \min_o
\]

\[
S_s = \frac{\sum_k w_k\, \bar n_{k,s}}{\sum_k w_k},\qquad \bar n_{k,s} = \text{media de } n_{o,s} \text{ sobre los objetivos del deslizador } k,\qquad S_s = 0 \text{ si } \sum_k w_k = 0
\]

Orden: \(S\) descendente; empate, posición original en el documento. Pesos \(w_k \ge 0\) (Web usa 0 a 5). El documento trae `normalizados`, `por_deslizador` y el orden con pesos iguales.

Casos de prueba (`prioridades.casos_prueba` y `pruebas/gemelo/test_prioridades.py`), sobre esta tabla sintética:

| Estrategia | riego | deficit | carbono | lluvia_intensa | fertilizante | riesgo_produccion |
|-|-|-|-|-|-|-|
| X | 0 | 0,30 | −0,10 | 30 | 150 | 0,30 |
| Y | 0 | 0,20 | 0,05 | 20 | 100 | 0,25 |
| Z | 0 | 0,25 | −0,30 | 35 | 50 | 0,40 |

| Caso | Pesos (agua, suelo, insumos, estabilidad) | Puntajes X, Y, Z | Orden |
|-|-|-|-|
| Pesos iguales | 1, 1, 1, 1 | 0,258929; 0,5625; 0,625 | Z, Y, X |
| Solo suelo | 0, 5, 0, 0 | 0,452381; 1; 0 | Y, X, Z |
| Agua alta y algo de estabilidad | 5, 0, 0, 1 | 0,263889; 0,625; 0,583333 | Y, Z, X |
| Todos en cero | 0, 0, 0, 0 | 0; 0; 0 | X, Y, Z |

### 5. Identificador del lote

`lote.id` de un lote DEMO = `DEMO-{iso3}-{nn}` (regex `^DEMO-[A-Z]{3}-\d{2}$`). Se valida cuando el id empieza por `DEMO`, cuando hay `zona_demo` y siempre en el paquete; otro formato es error.

### 6. Erosión: una sola definición

- `exposicion_erosiva` es la función de Datos (T-D6: percentil 90 semanal, pendiente y erodabilidad K). El gemelo no usa ese nombre para lo suyo.
- El indicador del gemelo se llama `lluvia_intensa_sobre_suelo_desnudo_mm_anio` (misma fórmula de la v1) y el objetivo `lluvia_intensa_suelo_desnudo`.
- Por la regla aditiva, `exposicion_erosiva_mm_anio` sigue saliendo como alias con el mismo valor y `obsoleto: true, reemplazado_por`; el objetivo `exposicion_erosiva` se acepta en la entrada y se traduce. Web usa solo los nombres nuevos. Ambos alias se quitan en la v2.
- Cuando T-D6 exista, el gemelo leerá `exposicion_erosiva` de Datos como entrada (contexto del lote) en lugar de calcular otro índice con ese nombre.

### 7. Entradas de Datos

| `clima.fuente` / `suelo.fuente` | Campos | Formato esperado (`contratos/forzantes_gemelo.md`, T-D5) |
|-|-|-|
| `forzantes_diarios` | `archivo`, `lat`, `elevacion_m` | CSV o Parquet con `fecha` (AAAA-MM-DD) y `precip` mm/día, `t2m` (o `t2m_max` y `t2m_min`) °C, `rad_sw` MJ/m²/día; opcionales `rh2m` %, `ws2m` m/s. Naturaleza `estimado` |
| `parametros_suelo_json` | `archivo` | JSON con `arena`, `arcilla` (kg/kg), `mo_pct` (%), `cos_t_ha` (t C/ha, 0-30 cm); opcionales `cn_suelo`, `profundidad_m`, `fuente`. Naturaleza `estimado` |

- Formato «esperado»: si `forzantes_gemelo.md` fija otros nombres o unidades, el adaptador se ajusta a ese contrato sin cambiar estas claves.
- `sqlite_mensual` queda solo como contexto: el documento lleva el aviso `warning.monthly_context_only`, porque desagregar lluvia mensual a diaria borra las tormentas y la lluvia intensa pierde sentido.

### 8. ENSO

- `escenario.tipo` acepta `enso_nino`, `enso_nina` y `enso_neutra`: como seco/normal/húmedo, con años análogos reales de esa fase (`escenario.anios_analogos`, `fase_enso`, `clasificacion_enso`).
- `escenario.enso_archivo` (opcional): la clasificación de Datos, `{anio: "nino" | "nina" | "neutra"}` en YAML o JSON. Mientras Datos no la entrega, la fase se deriva del ONI de NOAA CPC (copia en `src/gemelo/referencias/enso.yaml`): media anual ≥ +0,5 °C El Niño, ≤ −0,5 °C La Niña, resto neutra; `clasificacion_enso.etiqueta = INFERENCIA`, `interina: true` y aviso `warning.enso_interim`.
- En el escenario histórico, `indicadores_por_fase_enso`: indicadores p10/p50/p90 por estrategia y fase, agrupando las ventanas por la fase de su primer año, con `n_miembros` y `ventanas_por_fase`.

### 9. Alertas: propuesta de recorte

Propuesta del Gemelo, pendiente de la firma de Daniel: las alertas de T-G5 quedan **fuera** de la v1.1.

- Motivo: el gemelo compara estrategias en escenarios de varios años; no tiene datos en tiempo casi real del lote ni pronóstico, así que una alerta («riego ya», «helada mañana») sería un dato que el modelo no puede respaldar.
- Lo que cubre el lugar de las alertas: `avisos_claves`, la sección `riesgos` de cada tarjeta (años malos p10, dominio del suelo, clima mensual) y los escenarios seco y ENSO.
- Si se firma lo contrario, las alertas entrarían como bloque aditivo `alertas` en una v1.2.

Firma de Daniel: pendiente.
