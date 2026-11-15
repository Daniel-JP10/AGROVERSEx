# Contrato de forzantes de los lotes DEMO para el Gemelo · v1 (2026-11-14, actualizado con D-027 y Prioridades 3 y 4)

Estado: v1 actualizada por Datos (T-D5 y T-D6, Prioridades 3A, 3B, 3C y 4) conforme a la decisión **D-027** de `decisiones/registro.md`. Totalmente retrocompatible con `contratos/gemelo_api.md` (rama `gemelo`): ninguna clave existente se rompe y se verificó mediante ejecución directa de `gemelo.clima.cargar_power` y `gemelo.suelo.perfil_desde_parametros_datos` (`origin/gemelo`). Rótulos: `VERIFICADO`, `FUENTE`, `INFERENCIA`, `SUPUESTO`, `PENDIENTE`.

## 1. Dónde están los archivos y regla de `lotes_demo.json` (D-027)

Los datos pesados viven fuera del control de versiones en `C:/NASA/AGROVERSEx/datos/procesados/lotes/<lote_id>/` (en WSL `/mnt/c/NASA/AGROVERSEx/datos/procesados/lotes/<lote_id>/`) y se entregan copiados con sus sumas SHA256 en `C:/NASA/compartir/forzantes/`. Lotes: `DEMO-USA-01` (Saunders, Nebraska) y `DEMO-COL-01` (Ipiales, Nariño). Lo versionado y liviano vive en `datos/lotes/`.

| Archivo | Ubicación versionada / procesada | Copia en `C:/NASA/compartir/forzantes/` | Contenido |
|-|-|-|-|
| `lotes_demo.json` | `datos/lotes/lotes_demo.json` (versionado en repo) | `lotes_demo.json` | Lista canónica de lotes DEMO (`lote_id`, `unidad_id`, `nombre`, `etiqueta: "DEMO"`, `clima_tipo`, `lat`, `lon` a 3 decimales, `area_ha`, `estacion_referencia`, `geometria` GeoJSON). **Por D-027 vive en `datos/lotes/lotes_demo.json` y T-D7 lo copia a los archivos públicos de Web.** |
| `power_diario.csv` | `<lote>/power_diario.csv` | `power_DEMO-USA-01_diario.csv`, `power_DEMO-COL-01_diario.csv` | Forzante diario principal de lotes (D-027), 2001-2024 (`8766` días), con las columnas crudas (`T2M`, `T2M_MAX`, `T2M_MIN`) **y** las corregidas por altitud (`T2M_CORR`, `T2M_MAX_CORR`, `T2M_MIN_CORR`). |
| `imerg_diario.csv` | `<lote>/imerg_diario.csv` | `imerg_DEMO-USA-01_diario.csv`, `imerg_DEMO-COL-01_diario.csv` | Serie diaria completa GPM IMERG Final Run V07B (`GPM_3IMERGDF.07`, `0,1°`, día UTC `00:00-23:59:59`), 2001-2024 (`8766` días, `0` faltantes). |
| `parametros_suelo.json` | `<lote>/parametros_suelo.json` | `parametros_suelo_DEMO-USA-01.json`, `parametros_suelo_DEMO-COL-01.json` | Parámetros de suelo SoilGrids 2.0 REST con escalares en la **raíz** (`arena`, `arcilla`, `mo_pct`, `cos_t_ha`, `profundidad_m`) para `gemelo.suelo.perfil_desde_parametros_datos` y diccionario `"parametros"` con rangos `[Q0.05, Q0.95]`. |
| `soilgrids_rest.json` | `<lote>/soilgrids_rest.json` | `soilgrids_DEMO-USA-01.json`, `soilgrids_DEMO-COL-01.json` | Respuesta cruda REST de SoilGrids 2.0, compatible con `gemelo.suelo.perfil_desde_soilgrids`. |
| `validacion_temperatura_ipiales.json` | `datos/lotes/validacion_temperatura_ipiales.json` | `validacion_temperatura_ipiales.json` | Validación de `T2M`, `T2M_MAX`, `T2M_MIN` (crudas y corregidas por altura) de POWER en `DEMO-COL-01` contra la estación terrestre GHCN-Daily `COM00080370` (Aeropuerto San Luis, Ipiales) en 2001-2024. |
| `comparacion_power_imerg.json` | `datos/lotes/comparacion_power_imerg.json` | `comparacion_power_imerg.json` | Alineación horaria UTC y correlaciones de Pearson y Spearman diaria (`lag = -1, 0, +1` y ponderada UTC), de 5 días (`pentadal`) y mensual entre POWER e IMERG en ambos lotes. |
| `exposicion_erosiva_lotes.json` | `datos/lotes/exposicion_erosiva_lotes.json` | `exposicion_erosiva_lotes.json` | Umbrales semanales P90 de tormentas (IMERG), relieve NASADEM 30 m (`S` de McCool et al., 1987), erodabilidad `K` de Williams (1995) e índice `exposicion_erosiva` (`combinacion_propia`) para ambos lotes. |

## 2. Entrada del Gemelo y compatibilidad verificada

```yaml
lote: {id: DEMO-USA-01, nombre: "Lote DEMO Saunders (Nebraska)", lat: 41.165, lon: -96.477,
       unidad_id: USA-ADM2-52423323B480079355264, clima_tipo: templado}
clima: {fuente: power_csv, archivo: C:/NASA/AGROVERSEx/datos/procesados/lotes/DEMO-USA-01/power_diario.csv}
suelo: {fuente: parametros_datos, archivo: C:/NASA/AGROVERSEx/datos/procesados/lotes/DEMO-USA-01/parametros_suelo.json}
```

Para `DEMO-COL-01`: `lat: 0.842`, `lon: -77.661`, `unidad_id: COL-ADM2-7082276B52108893597118`, `clima_tipo: tropical`.

`VERIFICADO` por ejecución directa del código de `origin/gemelo`:
- `gemelo.clima.cargar_power` lee los `power_diario.csv` actualizados (con las 3 columnas nuevas `T2M_CORR,T2M_MAX_CORR,T2M_MIN_CORR`) de ambos lotes sin romperse, extrayendo `anios = [2001..2024]`, `elevacion_m = 357.8 m` (`DEMO-USA-01`, `t2m_media_c = 11.1686 °C`) y `elevacion_m = 2553.24 m` (`DEMO-COL-01`, `t2m_media_c = 13.1831 °C`), `huecos_rellenos = {}`.
- `gemelo.suelo.perfil_desde_parametros_datos` lee los `parametros_suelo.json` actualizados de ambos lotes sin error, poblando `arena`, `arcilla`, `mo_pct`, `cos_t_ha`, `profundidad_perfil_m = 1.0 m` y completando `theta_pmp`, `theta_cc`, `theta_sat` y `ksat_mm_h` mediante Saxton y Rawls (2006) (`avisos = []`).

## 3. Forzante diario principal de lotes: NASA POWER diario (D-027)

- **Decisión D-027 (`VERIFICADO`)**: Para los lotes DEMO, NASA POWER diario (`power_diario.csv`, comunidad `AG`, fuentes internas MERRA-2 y CERES SYN1deg) es la **fuente principal** de forzantes meteorológicos diarios (excepción explícita a D-012 acotada exclusivamente a lotes), porque entrega en serie diaria continua (2001-2024, `8766` días, `0` huecos) las seis variables requeridas por Penman-Monteith FAO-56 (`PRECTOTCORR`, `T2M`, `T2M_MAX`, `T2M_MIN`, `RH2M`, `ALLSKY_SFC_SW_DWN`, `WS2M`).
- **Columnas del CSV (`VERIFICADO`)**:
  `YEAR,DOY,PRECTOTCORR,T2M,T2M_MAX,T2M_MIN,RH2M,ALLSKY_SFC_SW_DWN,WS2M,T2M_CORR,T2M_MAX_CORR,T2M_MIN_CORR`
  Las columnas crudas (`T2M`, `T2M_MAX`, `T2M_MIN`) **no se borran**; las corregidas por altitud (`T2M_CORR`, `T2M_MAX_CORR`, `T2M_MIN_CORR`) se añaden al final de cada fila.

## 4. Corrección de temperatura por altitud en Ipiales (`DEMO-COL-01`) y validación contra `COM00080370` (Prioridad 3A)

### 4.1 Gradiente térmico vertical y fuentes primarias verificadas
- **Desfase de altitud (`VERIFICADO`)**:
  - En `DEMO-COL-01` (Ipiales), la cabecera de `power_diario.csv` declara para la celda MERRA-2 (`0,5° x 0,625°`) una elevación media de `2553,24 m`. El lote `DEMO-COL-01` está a `2934,0 m` (`delta_z = +380,76 m`; la media de los 961 píxeles de NASADEM 30 m dentro del polígono es `2945,2 m`, p10-p90 `[2929, 2966] m`). La estación meteorológica cercana `COM00080370` (Aeropuerto San Luis, Ipiales, lat `0.862`, lon `-77.672`) está a `2961,0 m` según la ficha de referencia OMM/IDEAM (`delta_z = +407,76 m`) y a `2976,4 m` según la cabecera de GHCN-Daily (`delta_z = +423,16 m`).
  - En `DEMO-USA-01` (Saunders, Nebraska), la celda MERRA-2 está a `357,8 m` y el lote a `355,0 m` (`delta_z = -2,80 m`, `delta_T = +0,0182 °C`).
- **Tasa de enfriamiento vertical estándar (`-6,5 °C/km = -0,0065 °C/m`, `VERIFICADO` por tres fuentes primarias independientes)**:
  1. **NOAA, NASA y USAF (1976)**: *U.S. Standard Atmosphere, 1976* (NOAA-S/T 76-1562, Washington, D.C.), Part 1, Table I, p. 3: define en la capa troposférica `h = 0` a `11 km` el gradiente vertical estándar de temperatura molecular $L_{M,0} = -6{,}5\text{ K/km} = -0{,}0065\,^\circ\text{C/m}$.
  2. **FAO-56 (Allen, Pereira, Raes y Smith, 1998)**: *Crop evapotranspiration: Guidelines for computing crop water requirements*, FAO Irrigation and Drainage Paper No. 56 (ISBN 92-5-104219-5), Eq. 7 y Annex 3 Eq. 3-2: adopta la tasa constante de enfriamiento vertical troposférico $\alpha_1 = 0{,}0065\text{ K/m}$ para ajustar variables psicrométricas y atmosféricas con la elevación $z$.
  3. **OACI / ISO (1993 / 1975)**: *Manual of the ICAO Standard Atmosphere* (ICAO Doc 7488/3, 3.ª ed., coincidente con ISO 2533:1975): gradiente estándar troposférico de $-6{,}5\,^\circ\text{C/km}$.
  - **Contraste en literatura climatológica de los Andes colombianos (`FUENTE`)**: Eslava, J. A. (1993, *Rev. Acad. Colomb. Cienc. Exact. Fís. Nat.*, 18(71):507-538) y Pabón-Caicedo et al. (IDEAM / Univ. Nacional de Colombia) reportan para los Andes de Colombia un gradiente térmico vertical medio de $-6{,}13\,^\circ\text{C/km}$ ($-0{,}00613\,^\circ\text{C/m}$, rango $-5{,}5$ a $-6{,}5\,^\circ\text{C/km}$). Con $-6{,}5\,^\circ\text{C/km}$, el ajuste a la altitud del lote (`2934 m`) es $\Delta T = -2{,}4749\,^\circ\text{C}$; con $-6{,}13\,^\circ\text{C/km}$ es $-2{,}3341\,^\circ\text{C}$ (diferencia de solo $0{,}14\,^\circ\text{C}$).

### 4.2 Validación contra la estación GHCN-Daily `COM00080370` (2001-2024)
Se descargó la serie diaria real de `COM00080370` (`datos/crudos/ghcn/COM00080370.csv`, SHA256 `b2dca61c6f63748daa21bf876815b402e6c2f60ed9710f302202152db93f94b5`, ficha en `datos/fichas/ghcn_daily.md`). Resultados completos con intervalo de confianza bootstrap al 95 % por bloques anuales (2000 réplicas, semilla `42`) en `datos/lotes/validacion_temperatura_ipiales.json` (`VERIFICADO`):

| Comparación (2001-2024) | $n$ días válidos (% de 8766) | Serie evaluada | Elevación ref. (m) | Sesgo medio (°C) [IC95 bootstrap] | MAE (°C) [IC95 bootstrap] | RMSE (°C) [IC95 bootstrap] |
|-|-|-|-|-|-|-|
| `T2M_MIN` vs `TMIN` | `5184` (`59,14 %`) | Cruda (`T2M_MIN`) | `2553,24` | `+3,5116` `[+3,4015, +3,6530]` | `3,5233` `[3,4130, 3,6652]` | `4,0872` `[3,9699, 4,2353]` |
| `T2M_MIN` vs `TMIN` | `5184` (`59,14 %`) | **Corregida lote (`T2M_MIN_CORR`)** | **`2934,0`** | **`+1,0366` `[+0,9266, +1,1781]`** | **`1,7928` `[1,7323, 1,8718]`** | **`2,3343` `[2,2451, 2,4469]`** |
| `T2M_MIN` vs `TMIN` | `5184` (`59,14 %`) | Corregida estación OMM | `2961,0` | `+0,8611` `[+0,7511, +1,0026]` | `1,7534` `[1,6960, 1,8265]` | `2,2618` `[2,1763, 2,3690]` |
| `T2M_MIN` vs `TMIN` | `5184` (`59,14 %`) | Corregida cabecera GHCN | `2976,4` | `+0,7610` `[+0,6510, +0,9025]` | `1,7368` `[1,6811, 1,8076]` | `2,2256` `[2,1428, 2,3293]` |
| `T2M` vs `TAVG` | `6338` (`72,30 %`) | **Cruda (`T2M`)** | **`2553,24`** | **`+0,7995` `[+0,7128, +0,8944]`** | **`1,0350` `[0,9739, 1,1041]`** | **`1,3002` `[1,2261, 1,3809]`** |
| `T2M` vs `TAVG` | `6338` (`72,30 %`) | Corregida lote (`T2M_CORR`) | `2934,0` | `-1,6755` `[-1,7622, -1,5805]` | `1,7352` `[1,6531, 1,8116]` | `1,9643` `[1,8833, 2,0343]` |
| `T2M` vs `TAVG` | `6338` (`72,30 %`) | Corregida estación OMM | `2961,0` | `-1,8510` `[-1,9377, -1,7560]` | `1,8945` `[1,8088, 1,9744]` | `2,1160` `[2,0338, 2,1883]` |
| `T2M_MAX` vs `TMAX` | `17` (`0,19 %`) | Cruda (`T2M_MAX`) | `2553,24` | `+1,1241` `[+0,2390, +1,6821]` | `1,5512` `[1,1316, 2,0488]` | `1,9138` `[1,4039, 2,3822]` |
| `T2M_MAX` vs `TMAX` | `17` (`0,19 %`) | Corregida lote (`T2M_MAX_CORR`) | `2934,0` | `-1,3508` `[-2,2360, -0,7928]` | `1,6591` `[1,2180, 2,4050]` | `2,0552` `[1,4375, 3,0163]` |

### 4.3 Regla de uso de columnas de temperatura para el Gemelo (`INFERENCIA` sustentada en validación)
1. **Para heladas, estrés por frío nocturno y mínimas diarias en `DEMO-COL-01` usar obligatoriamente `T2M_MIN_CORR`**: la columna cruda `T2M_MIN` tiene un sesgo cálido de `+3,51 °C` (mínimo absoluto de `+4,42 °C` en 24 años, con `0` días $\le 4\,^\circ\text{C}$), ocultando por completo el riesgo de heladas en el altiplano de Ipiales (donde `COM00080370` registra `17` días $\le 0\,^\circ\text{C}$, `260` días $\le 2\,^\circ\text{C}$ y `924` días $\le 4\,^\circ\text{C}$, con mínimo de `-1,4 °C`). `T2M_MIN_CORR` reduce el MAE a la mitad (`3,52 °C -> 1,79 °C`) y el sesgo a `+1,04 °C` (a `2934 m`) o `+0,86 °C` (a `2961 m`).
2. **Para temperatura media diaria (`T2M`) y suma térmica / ET0**: la columna cruda `T2M` tiene menor sesgo (`+0,80 °C`, MAE `1,04 °C`) frente a `TAVG` de GHCN que `T2M_CORR` (`-1,68 °C`, MAE `1,74 °C`), porque en el altiplano ecuatorial el calentamiento radiativo diurno de la superficie y el peso de las horas diurnas en la media sinóptica GTS (`TAVG_ATTRIBUTES = "H,,S"`) compensan el enfriamiento adiabático durante el día. Por eso `gemelo.clima.cargar_power` sigue leyendo por defecto `T2M`, `T2M_MAX`, `T2M_MIN`, y dispone en el mismo CSV de `T2M_CORR`, `T2M_MAX_CORR`, `T2M_MIN_CORR` para el indicador de heladas o pruebas de sensibilidad por altitud.

## 5. Lluvia en UTC y correlaciones 1d, 5d y mensual entre POWER e IMERG (Prioridad 3B)

- **Regla de alineación horaria UTC (`VERIFICADO`)**:
  - `imerg_diario.csv` está fechado en día UTC (`00:00:00` a `23:59:59 UTC`, columna `FECHA_UTC`).
  - `power_diario.csv` está fechado en día solar local (`LST`, cabecera de POWER: `UTC-5,18 h` en Ipiales `lon = -77.661°`; `UTC-6,43 h` en Nebraska `lon = -96.477°`).
  - Una tormenta vespertina en Ipiales (por ejemplo entre las `19:00` y las `23:59` hora local de Colombia, `UTC-5`) ocurre el **día `t`** para NASA POWER pero cae entre las `00:00` y las `04:59 UTC` del **día `t+1`** para IMERG (`POWER(t-1) LST` frente a `IMERG(t) UTC`, es decir `lag = +1` día).
- **Métricas verificadas en `datos/lotes/comparacion_power_imerg.json` (2001-2024, `8766` días, `VERIFICADO`)**:

| Lote | Escala / Alineación | $n$ | Pearson $r$ | Spearman $\rho$ | Sesgo POWER − IMERG | MAE | RMSE |
|-|-|-|-|-|-|-|-|
| `DEMO-USA-01` | Diaria `lag = -1` (`POWER(t+1)` vs `IMERG(t)`) | `8765` | `0,1179` | `0,2163` | — | — | — |
| `DEMO-USA-01` | Diaria `lag = 0` (mismo día calendario) | `8766` | `0,6736` | `0,6229` | `-0,1726 mm/d` (`-7,57 %`) | `1,8892 mm/d` | `5,1580 mm/d` |
| `DEMO-USA-01` | Diaria `lag = +1` (`POWER(t-1)` vs `IMERG(t)`) | `8765` | `0,4156` | `0,3563` | — | — | — |
| `DEMO-USA-01` | Diaria ponderada UTC (`6/24·P(t-1) + 18/24·P(t)`) | `8765` | **`0,7194`** (`0,7205` solar) | `0,5825` | — | — | — |
| `DEMO-USA-01` | **Acumulada 5 días (pentadal)** | `1754` | **`0,8670`** | **`0,8321`** | `-0,863 mm/5d` | `5,190 mm/5d` | `8,889 mm/5d` |
| `DEMO-USA-01` | **Mensual** (anomalías: $r = 0{,}9403$) | `288` | **`0,9641`** | **`0,9574`** | `-5,25 mm/mes` | `11,493 mm/mes` | `15,298 mm/mes` |
| `DEMO-COL-01` | Diaria `lag = -1` (`POWER(t+1)` vs `IMERG(t)`) | `8765` | `0,1263` | `0,2321` | — | — | — |
| `DEMO-COL-01` | Diaria `lag = 0` (mismo día calendario) | `8766` | `0,2754` | `0,3946` | `-1,2320 mm/d` (`-29,34 %`) | `4,3167 mm/d` | `9,0262 mm/d` |
| `DEMO-COL-01` | **Diaria `lag = +1` (`POWER(t-1)` vs `IMERG(t)`)** | `8765` | **`0,3399`** | **`0,3958`** | — | — | — |
| `DEMO-COL-01` | **Diaria ponderada UTC (`5/24·P(t-1) + 19/24·P(t)`)** | `8765` | **`0,3226`** (`0,3242` solar) | **`0,4284`** (`0,4291` solar) | — | — | — |
| `DEMO-COL-01` | **Acumulada 5 días (pentadal)** | `1754` | **`0,5180`** | **`0,5685`** | `-6,161 mm/5d` | `13,492 mm/5d` | `20,980 mm/5d` |
| `DEMO-COL-01` | **Mensual** (anomalías: $r = 0{,}5451$) | `288` | **`0,6623`** | **`0,6697`** | `-37,50 mm/mes` | `48,171 mm/mes` | `60,390 mm/mes` |

- **Explicación verificada del desfase en Ipiales (`VERIFICADO`)**:
  1. Tal como anticipó el director, en `DEMO-COL-01` la correlación diaria en `lag = +1` (`r = 0,3399`, Spearman `0,3958`) supera a la del mismo día `lag = 0` (`r = 0,2754`), y la combinación ponderada a UTC (`5/24` de `t-1` + `19/24` de `t`) eleva Spearman a `0,4284`.
  2. Al agregar a **5 días** (escala en la que se diluye el desfase horario y que gobierna la humedad del suelo del Gemelo), la correlación en Ipiales sube a **`r = 0,5180` (Spearman `0,5685`)**, y en escala **mensual** a **`r = 0,6623` (Spearman `0,6697`)**.
  3. **Contraste contra el pluviómetro terrestre `COM00080370` (`VERIFICADO`, cifras en `datos/lotes/comparacion_power_imerg.json`, bloque `contraste_estacion_ghcn_com00080370`)**: en los `4374` días comunes con medición de lluvia en el Aeropuerto San Luis (49,9 % de los 8.766 días de 2001 a 2024; temperatura mínima 59,1 %, media 72,3 %, máxima 0,2 %), la estación da `933,4 mm/año` equivalentes, NASA POWER `1162,5` (sesgo `+24,5 %`) e IMERG `0,1°` `1598,9` (sesgo `+71,3 %`). **Equivalente** = media diaria de los días comunes con dato × 365,25. **Sin relleno**: los días sin dato se excluyen, lo que supone que se parecen a los días con dato. Los huecos son parejos entre meses (43 % a 54 % con dato), por eso la suma por climatología mensual da casi lo mismo (`919,3`); entre años no lo son (2008-2009 ~1 %, 2015-2019 > 90 %), así que el valor pesa más la década 2010. POWER queda más cerca de la estación que IMERG, lo que respalda D-027 y D-033f. La causa del exceso de IMERG (por ejemplo, desborde de lluvia convectiva del piedemonte oriental) es INFERENCIA sin evidencia propia.

## 6. Estructura de `parametros_suelo.json` con claves en la raíz y en `"parametros"` (Prioridad 3C)

Para que `gemelo.suelo.perfil_desde_parametros_datos` lea directamente el archivo sin adaptadores intermedios y al mismo tiempo se conserven los intervalos `[Q0.05, Q0.95]` de SoilGrids 2.0, `parametros_suelo.json` expone **ambos niveles** (`VERIFICADO`):

1. **En la raíz del JSON (escalares numéricos leídos directamente por el Gemelo)**:
   - `"profundidad_m"`: `1.0` (m, perfil 0-100 cm)
   - `"arena"`: fracción másica `kg/kg` (0-100 cm; `0.1063` en `DEMO-USA-01`, `0.3921` en `DEMO-COL-01`)
   - `"arcilla"`: fracción másica `kg/kg` (0-100 cm; `0.4122` en `DEMO-USA-01`, `0.2833` en `DEMO-COL-01`)
   - `"mo_pct"`: materia orgánica en `%` (0-100 cm, `MO = COS / 0,58`; `1.4845` en `DEMO-USA-01`, `7.4793` en `DEMO-COL-01`)
   - `"cos_t_ha"`: stock de carbono orgánico del suelo 0-30 cm en `t C/ha` (`76.365` en `DEMO-USA-01`, `186.999` en `DEMO-COL-01`)
   - `"k_erodabilidad_williams"`: factor `K` de Williams (1995) en 0-30 cm en unidades SI `t·ha·h/(ha·MJ·mm)` (`0.023554` en `DEMO-USA-01`, `0.016384` en `DEMO-COL-01`)
2. **En `"parametros"` (diccionario detallado con incertidumbre y metadatos)**:
   - Contiene `"arena"`, `"arcilla"`, `"limo"`, `"densidad_aparente"`, `"mo_pct"`, `"cos_t_ha"` y `"agua_disponible_mm_m"`, cada uno con `{"valor": ..., "rango": [q05, q95], "unidad": ..., "etiqueta": ..., "profundidad_cm": ...}`.

## 7. Función `exposicion_erosiva` y umbrales P90 de tormentas (T-D6, Prioridad 4)

Implementada en `src/lotes_demo/erosion.py` (exportada en `src/lotes_demo/__init__.py`) y probada con TDD en `pruebas/lotes/test_erosion.py` (evidencia del fallo inicial RED en `datos/evidencia/T-D6_erosion_red.txt`, `7/7` pruebas en GREEN). Resumen de ambos lotes en `datos/lotes/exposicion_erosiva_lotes.json`:

- **Firma compatible con `origin/gemelo` (`gemelo.indicadores`) y con desglose explicable**:
  - `umbral_p90_semanal(precip_mm, fechas, fecha_corte=None, min_mm_dia_lluvioso=1.0)`: calcula el percentil 90 de los días lluviosos ($\ge 1{,}0\text{ mm}$) por semana del año (`1..52`), usando exclusivamente fechas $\le \text{fecha\_corte}$ cuando se evalúan alertas o validaciones temporales (**cero fuga temporal**, `VERIFICADO` por prueba unitaria).
  - `exposicion_erosiva(precip_mm, fechas, desnudo, pendiente_m_m, k_erodabilidad, ...)`: devuelve el índice aditivo/multiplicativo rotulado como `"combinacion_propia"` (`etiqueta: "INFERENCIA"`) junto con todos sus componentes por separado:
    - `indice_exposicion_erosiva` y `rango_indice` `[cota_baja, cota_alta]`
    - `n_tormentas_suelo_desnudo`, `n_tormentas_suelo_desnudo_anio`, `rango_n_tormentas_suelo_desnudo`
    - `lluvia_tormentas_suelo_desnudo_mm`, `lluvia_tormentas_suelo_desnudo_mm_anio`, `rango_lluvia_tormentas_mm_anio`
    - `dias_desnudos_totales` y `dias_desnudos_anio` con `{"valor", "cota_baja", "cota_alta"}`
    - `pendiente_m_m`, `factor_pendiente_s` (McCool et al., 1987, USDA AH-703) y `k_erodabilidad` (Williams, 1995 EPIC, SI)
    - `umbrales_p90_semanal_mm_dia`
- **Valores calculados para los dos lotes DEMO (2001-2024, `VERIFICADO`)**:
  - **`DEMO-USA-01` (Saunders, NE)**: pendiente media NASADEM 30 m (`EPSG:32614`) `0,0313 m/m` (`3,13 %`, p10-p90 `[1,62 %, 5,38 %]`, factor `S = 0,3680`); erodabilidad `K = 0,023554 t·ha·h/(ha·MJ·mm)`; lluvia en tormentas $\ge P_{90}$: `619,6 mm/año` (`37,0` tormentas/año); índice potencial (100 % desnudo) = `5,370`; índice acotado por visibilidad satelital HLS (`fracción válida media = 0,57`) = **`4,303` con rango `[3,236, 5,370]`** (`dias_desnudos_anio` cota baja `208,0` a cota alta `365,25`).
  - **`DEMO-COL-01` (Ipiales, Nariño)**: pendiente media NASADEM 30 m (`EPSG:32618`) `0,0881 m/m` (`8,81 %`, p10-p90 `[3,25 %, 16,00 %]`, `41,6 %` del lote con pendiente $\ge 9\,\%$, factor `S = 0,9776`); erodabilidad `K = 0,016384 t·ha·h/(ha·MJ·mm)` (amortiguada por alto carbono orgánico `SOC = 54,47 g/kg`); lluvia en tormentas $\ge P_{90}$: `930,0 mm/año` (`37,0` tormentas/año); índice potencial (100 % desnudo) = `14,895` (`2,77x` el de Nebraska por pendiente y lluvia); índice acotado por visibilidad HLS (`fracción válida media = 0,089`) = **`8,089` con rango `[1,283, 14,895]`** (`dias_desnudos_anio` cota baja `32,5` a cota alta `365,25`).

## 8. Reproducir

Desde `C:/NASA/wt/t-d5-lotes` con `PYTHONPATH=src` y `AGRO_DATOS=C:/NASA/AGROVERSEx/datos`:
- `C:/NASA/AGROVERSEx/.venv/Scripts/python.exe src/lotes_demo/suelo.py C:/NASA/AGROVERSEx/datos/procesados/lotes`
- `C:/NASA/AGROVERSEx/.venv/Scripts/python.exe src/lotes_demo/resumen_forzantes.py C:/NASA/AGROVERSEx/datos/procesados/lotes 2001-01-01 2024-12-31 datos/lotes/comparacion_power_imerg.json`
- `C:/NASA/AGROVERSEx/.venv/Scripts/python.exe src/lotes_demo/erosion.py C:/NASA/AGROVERSEx/datos/procesados/lotes C:/NASA/AGROVERSEx/datos/crudos datos/lotes/lotes_demo.json datos/lotes/exposicion_erosiva_lotes.json`
- Pruebas (`31 passed`): `C:/NASA/AGROVERSEx/.venv/Scripts/pytest.exe pruebas/lotes`
