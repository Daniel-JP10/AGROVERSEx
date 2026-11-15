# T-D2 · Respuesta preliminar de PI-D1 en Colombia (area frente a cultivo)

Etiqueta general: INFERENCIA preliminar; solo Colombia, 2019, nivel 2 (1122 municipios), cultivo = GFSAD1KCM clases 1 a 3 (SUPUESTO, ver ficha). No sale al pitch. La respuesta mundial va en T-D8.
Fuente de cada cifra: `datos/evidencia/T-D2_pi_d1_colombia_2019_4var.json` (generado por `src/simulacion/geo/pi_d1_colombia.py` sobre los csv.gz de `datos/procesados/series/COL`, sha256 en `T-D2_sha256_series_COL.txt`).

Unidad de conteo: pares unidad-mes (no unidades distintas) con valor en ambas ponderaciones; se excluyen los que no tienen cultivo o valor.

Fracción de pares unidad-mes cuya diferencia relativa |cultivo - area| / |area| supera el umbral. El umbral de materialidad es SUPUESTO: decide el director; se muestran 2 %, 5 %, 10 % y 20 %.

| variable | pares | >2 % | >5 % | >10 % | >20 % | diferencia absoluta media | correlación |
|---|---|---|---|---|---|---|---|
| precipitacion_final | 13032 | 58.0% | 31.6% | 13.5% | 3.9% | 0.01065 | 0.9934 |
| ndvi | 12674 | 49.6% | 20.7% | 7.3% | 1.5% | 0.02314 | 0.92279 |
| t2m | 13188 | 0.0% | 0.0% | 0.0% | 0.0% | 0.25929 | 0.99328 |
| humedad_radicular | 13104 | 48.2% | 26.8% | 12.4% | 2.2% | 19.65415 | 0.97361 |

Lectura (INFERENCIA):
- Lluvia, NDVI y humedad radicular: con el umbral de 5 % cambia entre una quinta parte y un tercio de los pares; con 10 %, entre 7 % y 14 %; la ponderación sí importa para una fracción no despreciable de municipios.
- T2M: la diferencia relativa sobre kelvin es 0 por construcción (290 K); no sirve como criterio. Su diferencia absoluta media es 0,26 K; PI-D1 para temperatura debe medirse en diferencia absoluta (por ejemplo 0,5 K): umbral aparte, PENDIENTE de decisión.
- Limitaciones: un año; los valores de area y cultivo de celdas gruesas (IMERG 0,1 grados, GLDAS 0,25) dependen de la fracción de cultivo sobre una celda mucho mayor que el municipio; la sensibilidad a clases 1 a 5 no se corrió (PENDIENTE).
- Sin intervalo de incertidumbre para estas fracciones: PENDIENTE (no se mostraría a un agricultor).

## Actualización tras D-023 (umbral y sensibilidades)

- Umbral de materialidad: 5 % (SUPUESTO, registrado a las 15:24), con 2 % y 10 % a la vista. Con clases 1 a 3 y 5 %: lluvia 31,6 %, NDVI 20,7 %, humedad radicular 26,8 % de los pares unidad-mes (tabla de arriba).
- Sensibilidad a las clases de cultivo (GFSAD1KCM 1-3 frente a 1-5), fuente `T-D2_sensibilidades_COL.json`: con clases 1 a 5 la fracción de pares >5 % baja a lluvia 20,3 %, NDVI 12,1 %, humedad 21,5 % (y >10 %: 7,6 %, 3,3 %, 8,3 %). Es decir, la diferencia área-cultivo depende de qué clases cuentan como cultivo (INFERENCIA: al sumar clases 4 y 5 la máscara se parece más al área). Además, el valor de cultivo mismo cambia entre 1-3 y 1-5 en >5 % de los pares: lluvia 22,6 %, NDVI 14,4 %, humedad 19,8 %. La conclusión de PI-D1 NO es robusta a esa elección: PENDIENTE de decisión del director sobre las clases.
- NDVI con `pixel_reliability` solo 0 (frente a 0 y 1): `frac_valida` media cae de 0,99 a 0,49 en área y de 0,94 a 0,48 en cultivo; con solo 0 salen sin valor 7164 unidades-mes de 2019 en área (32 con 0 y 1) por el umbral de 0,5. Donde ambos tienen valor, el NDVI cambia >5 % en 3,3 % (área) y 2,0 % (cultivo) de los pares: aceptar la clase 1 apenas mueve el valor, pero sin ella Colombia queda sin dato la mitad del tiempo (INFERENCIA, nubosidad).
