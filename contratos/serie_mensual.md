# Contrato serie_mensual · v0 (2026-11-14, T-D2)

Estado: v0 con el esquema real de la primera corrida (Colombia). Origen del esquema: `Docu/01_IDEA_AGROVERSEx.md` §5.2. Lo congela el integrador; las columnas marcadas "añadida" son aditivas y las propone T-D2.

## Una fila = una unidad, una variable, un mes, una ponderación

| Columna | Tipo | Significado |
|-|-|-|
| `unidad_id` | texto | El de `contratos/unidades.md` |
| `nivel` | entero 0, 1, 2 | Añadida. Nivel de la unidad, para filtrar sin unir |
| `variable` | texto | `precipitacion`, `t2m`, `humedad_radicular`, `ndvi` |
| `mes` | texto AAAA-MM | UTC. En MOD13C2 es el mes de inicio del compuesto (día juliano del nombre del archivo) |
| `valor` | real | Media ponderada de las celdas válidas; vacío si no hay valor (ver `motivo`) |
| `p10`, `p90` | real | Percentiles 10 y 90 ponderados de las celdas válidas dentro de la unidad (cuantil ponderado interpolado: cada celda en la posición peso acumulado menos la mitad de su peso, acotado al mínimo y al máximo; una celda sola da p10 = p90 = valor) |
| `tipo_rango` | texto | Siempre `espacial`: dispersión entre celdas de la unidad, no incertidumbre del producto |
| `frac_valida` | real 0 a 1 | Peso de las celdas válidas sobre el peso total de la unidad (en `cultivo`, sobre el peso de cultivo) |
| `ponderacion` | texto | `area` (cobertura exacta de la celda por la unidad por área de celda según latitud) o `cultivo` (lo anterior por fracción de cultivo) |
| `producto` | texto | Producto y tipo de dato; GLDAS lleva la palabra MODELO |
| `version` | texto | Versión del producto |
| `estado` | texto | `final` o `provisional` (IMERG Late) |
| `unidad` | texto | Añadida. Unidad física del `valor`, la del producto, sin convertir |
| `motivo` | texto | Añadida. Vacío si hay valor; `frac_valida_bajo_umbral`, `sin_celdas_validas`, `sin_cobertura` o `sin_cultivo` |

## Reglas de la agregación

- Umbral de `frac_valida`: 0,5 (SUPUESTO de T-D2, revisable). Debajo, `valor`, `p10` y `p90` salen vacíos con `motivo`; nunca se rellena. `frac_valida` se conserva siempre.
- Calidad aplicada antes de agregar: relleno de cada producto; MOD13C2 solo `pixel_reliability` 0 y 1 y rango válido del NDVI (-2000 a 10000, escala 1/10000); IMERG Late con D-011 (80 % de los días del calendario por celda, mes en curso no se emite). IMERG Final y MERRA-2 sin bandera de exclusión además del relleno; `precipitationQualityIndex` no se usa como máscara.
- Pesos: fracción exacta de cada celda cubierta por la unidad (exactextract) por `sin(lat sup) - sin(lat inf)` de la fila. Las unidades diminutas y las que cruzan 180 grados quedan con pesos (prueba).
- Unidades físicas: IMERG Final en mm/hr y Late en mm/day (el cambio de unidad ocurre en 2025-10; el consumidor debe convertir, 1 mm/hr = 24 mm/day). T2M en K, humedad radicular en kg m-2, NDVI sin unidad.

## Formato de archivo (provisional)

Parquet particionado por variable es lo pedido; el entorno no tiene pyarrow, así que la corrida escribe `serie_mensual_<variable>_<ponderacion>.csv.gz` (CSV con gzip, UTF-8, vacío = ausente). `precipitacion` va en dos archivos (`precipitacion_final` y `precipitacion_late`) que se concatenan. Propuesta: pyarrow, versión a fijar y revisar por el director.
