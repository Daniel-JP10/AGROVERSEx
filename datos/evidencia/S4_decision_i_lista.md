# Decisión i: lista final de borrado del generador simulado, con evidencia (no se borró nada)

Reproduce: `cd C:\NASA\wt\f2-s4-analisis && C:\NASA\AGROVERSEx\.venv\Scripts\python.exe datos/evidencia/S4_grafo_importaciones.py` (escribe `S4_grafo_importaciones.txt`).
Base: worktree f2-s4-analisis sobre 8bf8370; 145 módulos Python (src, pruebas, datos, ejemplos, herramientas); análisis estático con `ast` (imports absolutos y relativos) más búsqueda de llamadas dinámicas y de referencias de texto en .py, .ts, .tsx, .mjs, .js, .json, .yaml, .sh y .sql.
Etiqueta: VERIFICADO como ejecución propia reproducible; el verificador distinto del autor falta.

## Resultado en una frase

Ningún módulo que se queda (src/simulacion/geo, src/gemelo, src/lotes_demo, src/mapa_estatico, src/web con server/ y .mjs) importa un módulo del generador, con UNA excepción: `src/simulacion/config.py`, que importan 7 módulos de geo (descargas, estaticos, extraer, gmted_tierra, indice_busqueda, teselas, unidades) y 4 pruebas de pruebas/geo. Va fuera de la lista de borrado. Y una dependencia que no es import: `src/simulacion/esquema_agroversex.sql` lo lee `src/web/pruebas/fixture.ts:19`, así que tampoco se borra.

## Lista archivo por archivo (src/simulacion, fuera de geo/)

| Archivo | Quién lo importa de lo que se queda | Decisión propuesta |
|-|-|-|
| `src/simulacion/config.py` | geo/descargas, geo/estaticos, geo/extraer, geo/gmted_tierra, geo/indice_busqueda, geo/teselas, geo/unidades; pruebas/geo/test_config_datos, test_estaticos_reales, test_teselas, test_unidades_reales | SE QUEDA (no borrar). Opcional: quitar de él lo solo del generador (SEMILLA, N_MESES, FECHA_INICIO, FECHA_FIN_DIARIA, GEO_SQLITE_RESPALDO), que ni geo/ ni pruebas/geo/ usan (grep de esos nombres sin resultados en ellos) |
| `src/simulacion/__init__.py` | es el paquete de `simulacion.geo` y `simulacion.config` | SE QUEDA |
| `src/simulacion/esquema_agroversex.sql` | `src/web/pruebas/fixture.ts:19` (DDL de las pruebas del servidor de Web) y variables.py (generador) | SE QUEDA o se mueve junto con un cambio de ruta en fixture.ts (decisión del director) |
| `src/simulacion/agua.py` | nadie | borrar |
| `src/simulacion/azar.py` | nadie | borrar |
| `src/simulacion/clima.py` | nadie | borrar |
| `src/simulacion/cobertura.py` | nadie | borrar |
| `src/simulacion/condicion.py` | nadie | borrar |
| `src/simulacion/escribir_sqlite.py` | nadie | borrar (ver dependencia de datos abajo) |
| `src/simulacion/incertidumbre.py` | nadie | borrar |
| `src/simulacion/lotes.py` | nadie | borrar |
| `src/simulacion/productos.py` | nadie | borrar |
| `src/simulacion/rotaciones.py` | nadie | borrar (ver dependencia de datos abajo) |
| `src/simulacion/suelo.py` | nadie | borrar |
| `src/simulacion/tiempo.py` | nadie | borrar |
| `src/simulacion/variables.py` | nadie (la lista de la bitácora lo daba como del generador y se confirma) | borrar |
| `src/simulacion/vegetacion.py` | nadie | borrar |
| `src/simulacion/referencias/cargar.py` y `__init__.py` | nadie (src/gemelo tiene su propia carpeta `referencias/` con copias; sus YAML solo citan la ruta en comentarios) | borrar |
| `src/simulacion/referencias/*.yaml` (13: berkeley, enso, eventos, eventos_iso3, faostat, fao56, gistemp, iso3_a_region, kluger, rodell, sistemas_rotacion, sucesion, teleconexiones) | nadie por ruta (la búsqueda de texto en código que se queda solo da comentarios y las copias propias del Gemelo) | borrar |
| `src/simulacion/zonas_agroversex.yaml` | nadie (solo lotes.py:23) | borrar |

Módulos de la lista de la bitácora que aparecen como "solo del generador" además de los 10 iniciales: azar, condicion, incertidumbre, productos, rotaciones y referencias (cargar y YAML). De los 10 iniciales, `config` NO es solo del generador; los otros 9 (clima, vegetacion, agua, cobertura, suelo, lotes, escribir_sqlite, variables, tiempo) sí.

## Cosas que no son imports y el director debe ver antes de aprobar

1. Dependencia de datos en `src/web/server/`: lee de agroversex.sqlite las tablas `sistema_rotacion`, `efecto_antecesor`, `cultivo`, `regla_sucesion`, `zona_demo`, `mensual`, `variable` y `unidad` (rutas_rotaciones.ts, rutas_serie.ts, etc.). Esa base solo la produce `escribir_sqlite`/`rotaciones` del generador. Sin import, pero al borrarlo el servidor de desarrollo no tiene de dónde leer salvo sus fixtures. La versión pública no usa server/ (D-014).
2. Pruebas de pruebas/sim: los 19 archivos importan módulos del generador y salen con él, pero tres no son solo del generador: `test_clim_normal_geo.py` prueba `geo.clim_normal.escribir` y relee con `clima.cargar_normales`; `test_anclas.py` importa también `geo.teselas`; `test_referencias.py` y `test_esquema.py` prueban datos y esquema. Se reescriben o se mueven a pruebas/geo si se quiere conservar lo que cubren de geo.
3. `pruebas/geo/test_estaticos_reales.py` importa solo `config` (se queda, coherente con D-037.2).
4. Llamadas dinámicas: solo `importlib.reload` en pruebas/geo (test_config_datos, test_teselas) sobre config y teselas, y un `__import__("hashlib")`. Ninguna importa módulos del generador.
5. Limitación: un análisis estático no ve imports construidos con cadenas calculadas ni ejecuciones por `subprocess`; la búsqueda de texto no encontró ninguna invocación `python -m simulacion.<módulo del generador>` fuera de la propia `escribir_sqlite` (su `prog=`).
