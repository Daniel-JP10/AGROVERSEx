# Contrato de forzantes de los lotes DEMO para el Gemelo · v0 (2026-11-14)

Estado: v0 redactada por Datos (T-D5 Parte B), pendiente de que el compañero A y el director la congelen. Compatible con la entrada v1 de `contratos/gemelo_api.md` (rama `gemelo`): no se cambia ninguna clave existente. Rótulos: VERIFICADO, FUENTE, INFERENCIA, SUPUESTO, PENDIENTE.

## Dónde están los archivos

Los datos pesados están fuera del control de versiones, en `C:/NASA/AGROVERSEx/datos/procesados/lotes/<lote_id>/` (en WSL `/mnt/c/NASA/AGROVERSEx/datos/procesados/lotes/<lote_id>/`). Lotes: `DEMO-USA-01` y `DEMO-COL-01`. Lo versionado y pequeño está en `datos/lotes/`.

| Archivo | Contenido |
|-|-|
| `datos/lotes/lotes_demo.json` (repo) | Lista de lotes para Web y Gemelo: `lote_id`, `unidad_id`, `nombre`, `etiqueta` DEMO, `clima_tipo`, `lat`, `lon`, `area_ha`, `estacion_referencia`, `geometria` GeoJSON. `web_componentes.md` solo dice "archivo estático `lotes_demo.json`" sin ruta: se propone esta y que Web la copie a su carpeta pública. PENDIENTE acuerdo con Web |
| `<lote>/power_diario.csv` | NASA POWER diario 2001-2024 tal cual lo entrega la API, formato `power_csv` del Gemelo. Copia para el Gemelo: `C:/NASA/compartir/forzantes/` |
| `<lote>/imerg_diario.csv` | Fuente nueva aditiva `imerg_csv`, ver abajo |
| `<lote>/imerg_diario.jsonl` | Crudo de la lectura OPeNDAP, una línea por día |
| `<lote>/soilgrids_rest.json` | Respuesta REST de SoilGrids 2.0, compatible con `suelo.fuente: soilgrids_json` |
| `<lote>/parametros_suelo.json` | Parámetros con rango y procedencia, ver abajo |
| `<lote>/hls_validez.json` y `datos/lotes/hls_validez_*.json` | Evidencia de PI-D2, no es forzante |

## Entrada del Gemelo, sin cambios

```yaml
lote: {id: DEMO-USA-01, nombre: "Lote DEMO Saunders (Nebraska)", lat: 41.165, lon: -96.477,
       unidad_id: USA-ADM2-52423323B480079355264, clima_tipo: templado}
clima: {fuente: power_csv, archivo: C:/NASA/AGROVERSEx/datos/procesados/lotes/DEMO-USA-01/power_diario.csv}
suelo: {fuente: soilgrids_json, archivo: C:/NASA/AGROVERSEx/datos/procesados/lotes/DEMO-USA-01/soilgrids_rest.json}
```

Para `DEMO-COL-01`: `lat: 0.842`, `lon: -77.661`, `unidad_id: COL-ADM2-7082276B52108893597118`, `clima_tipo: tropical`.

VERIFICADO por ejecución: `gemelo.clima.cargar_power` y `gemelo.suelo.perfil_desde_soilgrids` de `origin/gemelo` leen los archivos de ambos lotes sin error; el primero ve los años 2001-2024 completos y sin huecos; el segundo reproduce a 4 decimales arena, arcilla, MO, COS y densidad aparente de `parametros_suelo.json` (comprobación independiente de mi código). No se corrió una simulación completa del Gemelo.

`clima_tipo`: EE. UU. `templado`. Ipiales `tropical`, igual que `ejemplos/escenario_ipiales.yaml` del Gemelo (FUENTE) y por estar a 0,842 grados N sin estaciones marcadas; la altitud lo hace fresco (T2M media 13,2 °C, VERIFICADO sobre POWER). INFERENCIA; decide el Gemelo si sus reglas lo permiten.

## Forzante principal: NASA POWER diario

- Fuente: NASA POWER, comunidad AG, resolución nativa (MERRA-2 y CERES SYN1deg), consulta exacta en `datos/fichas/power_diario.md`. Descargado el 2026-11-14. Se elige como principal porque el Gemelo ya lo lee sin cambios, trae las seis variables de Penman-Monteith y cubre el periodo completo.
- Periodo: 2001-01-01 a 2024-12-31, 8766 días, 24 años completos. Coincide con el periodo común con IMERG Final V07 diario y da años completos al Gemelo (exige años de 365 días). POWER llega a 1981; más años son posibles bajo pedido. SUPUESTO: 24 años bastan para ventanas de 3 años.
- Columnas y unidades (VERIFICADO por la cabecera): `YEAR`, `DOY`, `PRECTOTCORR` mm/día, `T2M`, `T2M_MAX`, `T2M_MIN` °C, `RH2M` %, `ALLSKY_SFC_SW_DWN` MJ/m2/día, `WS2M` m/s. Son los insumos de Penman-Monteith FAO-56; el ET0 lo calcula el Gemelo, Datos no entrega ET0.
- Zona horaria: el CSV declara "LST" (día de hora solar local) y POWER no publica horario; no se convirtió a UTC. Limitación declarada. Agregación: la nativa de POWER.
- Huecos: ningún valor -999 en las dos series (VERIFICADO por conteo); el Gemelo no rellenó nada (`huecos_rellenos: {}`).
- Pruebas que pasan (`pruebas/lotes/test_forzantes.py`): Tmin <= Tmax, precipitación >= 0, sin NaN de precipitación, 8766 filas. Un día faltante nunca se convierte en cero.
- Rango y confianza: POWER no publica incertidumbre y no se inventa. Es reanálisis de una celda de 0,5 x 0,625 grados: contexto del lote, nunca medición del lote.

Lo que carga el Gemelo (VERIFICADO por ejecución): EE. UU., lluvia anual media 769 mm (p10-p90 567-952), T2M media 11,2 °C, elevación de celda 357,8 m. Colombia, lluvia anual media 1083 mm (p10-p90 800-1376), T2M media 13,2 °C, elevación de celda 2553,2 m.

## Fuente nueva aditiva `imerg_csv` (contraste de lluvia)

No rompe la v1: es un archivo aparte que el Gemelo puede ignorar. Se propone una clave opcional `clima.precipitacion_alterna: {fuente: imerg_csv, archivo: ...}`; hoy el Gemelo no la implementa (PENDIENTE del compañero A).

- Producto: GPM IMERG Final Run diario V07 (GPM_3IMERGDF.07), celda de 0,1 grados que contiene el centro del lote. Ficha `datos/fichas/imerg_diario.md`.
- Columnas: `FECHA_UTC` (día UTC), `YEAR`, `DOY`, `IMERG_PRECIP_MM_DIA` (mm/día), `IMERG_N_MUESTRAS` (conteo de muestras del producto). Vacío significa sin dato; nunca 0.
- Zona horaria: UTC (3B-DAY es 00:00 a 23:59:59 UTC). POWER es LST, así que hay un desfase de varias horas (EE. UU. cerca de 6 h, Colombia 5 h): un día de lluvia puede caer en el día contiguo y baja la correlación diaria.
- Periodo: 2001-01-01 a 2024-12-31, 8766 días, igual que POWER
- Huecos: ningún día faltante ni con conteo de muestras cero en las dos series (VERIFICADO por conteo)
- Contraste con POWER en el periodo común (INFERENCIA; sin pluviómetro propio no se sabe cuál acierta; ejecución en `datos/lotes/comparacion_power_imerg.json`): 2001-2024, lluvia anual media IMERG 833 mm contra POWER 770 mm en EE. UU. (correlación diaria 0,67, mensual 0,96) y IMERG 1534 mm contra POWER 1084 mm en Colombia (diaria 0,28, mensual 0,66); POWER queda 8 % y 29 % por debajo. En Ipiales las dos fuentes difieren mucho: el Gemelo no debe tomar la lluvia de POWER como cierta allí

## Parámetros de suelo: `parametros_suelo.json`

- Fuente: SoilGrids 2.0 por la API REST `rest.isric.org/soilgrids/v2.0/properties/query`, no los rasters locales de 1000 m (que solo traen la media). Capas 0-5, 5-15, 15-30, 30-60 y 60-100 cm; estadísticos mean, Q0.05, Q0.5 y Q0.95. Respuesta cruda en `soilgrids_rest.json`. Consulta del 2026-11-14.
- Propiedades: arena y arcilla en kg/kg; densidad aparente en kg/dm3; MO en %; COS 0-30 cm en t C/ha. Cada una con `valor`, `rango` [Q0.05, Q0.95], `unidad`, `etiqueta`, `profundidad_cm` y `metodo`. Ponderación por espesor igual a la del Gemelo; MO = COS/0,58 (INFERENCIA); COS = suma(SOC x BD x espesor) sin fragmentos gruesos.
- Agua disponible: `agua_disponible_mm_m` = media(wv0033) menos media(wv1500) de SoilGrids, 0-100 cm (capacidad de campo menos punto de marchitez). Contraste del cálculo de Saxton y Rawls del Gemelo, no lo reemplaza. Su rango es una cota amplia con cuantiles cruzados, no cuantiles de la diferencia. INFERENCIA.
- Valores con rango entre corchetes. EE. UU.: arena 0,106 [0,018-0,347], arcilla 0,412 [0,009-0,913], densidad aparente 1,61 [1,36-1,88], MO 1,48 % [0,54-2,95], COS 76,4 [24,5-176,9] t C/ha. Colombia: arena 0,392 [0,140-0,633], arcilla 0,283 [0,034-0,696], densidad aparente 1,18 [0,58-1,66], MO 7,48 % [0,48-23,8], COS 187,0 [8,7-770,2] t C/ha. VERIFICADO por ejecución: dos implementaciones concuerdan.
- Los rangos son muy anchos: son los cuantiles del mapa de SoilGrids en un píxel de 250 m, incertidumbre del mapa y no variación del lote. Un análisis de suelo del lote lo sustituye con `fuente: manual` y `calibracion`.
- Colombia: MO de 7,5 % y COS de 187 t/ha concuerdan con suelos de altura de origen volcánico (INFERENCIA, sin análisis local); el Gemelo debe tratarlos con el rango y no con el valor central.
- No se usó SSURGO en EE. UU.: PENDIENTE, solo si el director lo pide.

## Limitaciones declaradas

1. Todo dato de 0,1 o 0,5 grados es contexto del lote.
2. Elevación en DEMO-COL-01 (orden del director): la celda MERRA-2/POWER tiene 2553 m de elevación media (VERIFICADO en la cabecera del CSV) y el lote unos 2934 m según el orquestador (FUENTE: mensaje del orquestador, no medido por mí), unos 380 m de diferencia, que pesa más que los 42 m de la estación de referencia. T2M, T2M_MAX y T2M_MIN de POWER NO están corregidos por altura: no se citó una fuente verificable del gradiente. Queda sin corregir y anotado; las temperaturas del lote real serán más bajas que las del CSV. Las estaciones GHCN-Daily (USC00255362 y COM00080370) solo figuran como referencia de elección; no se descargaron sus datos y su licencia sigue PENDIENTE.
3. Sin verdad de terreno de lluvia: POWER contra IMERG no dice cuál es correcta.
4. No se entrega parquet: `pyarrow` no está fijado en el entorno y no se instaló; los forzantes van en CSV. Si el Gemelo pide `forzantes.parquet` hay que aprobar el paquete.
5. No se clasificaron años por fase ENSO (paso 7 de T-D5): depende del índice de T-D3.
6. No se descargó NASADEM, SMAP, ECOSTRESS, CDL, SSURGO ni NAIP: fuera de este alcance de v0.
7. El área de los polígonos con coordenadas a 3 decimales es 74,6 ha (EE. UU.) y 78,9 ha (Colombia), no las 64 ha de la Parte A, que usaba más decimales. `lotes_demo.json` declara el área recalculada y la de la Parte A.

## Evidencia de PI-D2: fracción HLS válida

Tabla y distribución en `datos/lotes/hls_validez_resumen.md`; método en `datos/fichas/hls_v2.md`. No cambia la elección del lote. VERIFICADO por ejecución propia, falta verificador distinto. Tabla pendiente de revisión en el archivo citado: fracción válida media de los 36 meses 0,09 en DEMO-COL-01 (33 de 36 meses con media < 0,25) y 0,57 en DEMO-USA-01.

## Reproducir

Entorno `C:/NASA/AGROVERSEx/.venv` (Windows) y `wsl -d Ubuntu-24.04` con `~/venvs/agroversex_geo` para HLS. Desde `src/`: `python -m lotes_demo.construir_lotes`; `python -m lotes_demo.imerg_diario <lote> <lat> <lon> <ini> <fin> <salida.jsonl>`; `python -m lotes_demo.suelo <raiz>`; `python -m lotes_demo.resumen_forzantes <raiz> <ini> <fin> <salida.json>`; en WSL `python -m lotes_demo.hls_validez <lote> 2022-01-01 2024-12-31 <T14|T18> <salida.json>`. Pruebas: `python -m pytest pruebas/lotes`.
