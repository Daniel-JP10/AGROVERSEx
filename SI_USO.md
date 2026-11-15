# Uso de SI

Registro exigido por las guías de Space Apps 2026 y AGENTS.md §5.3. Cada archivo de código asistido por SI lleva la cabecera `asistido por SI: <herramienta y uso>` y una fila aquí.

| Herramienta | Archivo | Propósito | Fecha |
|-|-|-|-|
| Claude Code (Anthropic) | `pruebas/geo/test_descargas.py` | Pruebas del backend del prototipo | 2026-11-14 |
| Claude Code (Anthropic) | `pruebas/geo/test_estaticos.py` | Pruebas del backend del prototipo | 2026-11-14 |
| Claude Code (Anthropic) | `pruebas/geo/test_estaticos_reales.py` | Pruebas del backend del prototipo | 2026-11-14 |
| Claude Code (Anthropic) | `pruebas/geo/test_indice_busqueda.py` | Pruebas del índice de búsqueda sobre unidades CGAZ (T-D1) | 2026-11-14 |
| Claude Code (Anthropic) | `pruebas/geo/test_normalizar.py` | Pruebas del backend del prototipo | 2026-11-14 |
| Claude Code (Anthropic) | `pruebas/geo/test_teselas.py` | Pruebas de teselas con unidad_id de CGAZ, reducción < 100 MB y es_disputa (T-D1, D-016, D-017) | 2026-11-14 |
| Claude Code (Anthropic) | `pruebas/geo/test_unidades.py` | Pruebas de unidades CGAZ: ids, padres, áreas, GPKG y es_disputa en GeoJSON (T-D1, D-017) | 2026-11-14 |
| Claude Code (Anthropic) | `pruebas/geo/test_unidades_reales.py` | Pruebas del backend del prototipo | 2026-11-14 |
| Claude Code (Anthropic) | `pruebas/geo/test_zonal.py` | Pruebas del backend del prototipo | 2026-11-14 |
| Claude Code (Anthropic) | `pruebas/sim/test_agua.py` | Pruebas del backend del prototipo | 2026-11-14 |
| Claude Code (Anthropic) | `pruebas/sim/test_anclas.py` | Pruebas del backend del prototipo | 2026-11-14 |
| Claude Code (Anthropic) | `pruebas/sim/test_azar.py` | Pruebas del backend del prototipo | 2026-11-14 |
| Claude Code (Anthropic) | `pruebas/sim/test_clim_normal_geo.py` | Pruebas del backend del prototipo | 2026-11-14 |
| Claude Code (Anthropic) | `pruebas/sim/test_clima.py` | Pruebas del backend del prototipo | 2026-11-14 |
| Claude Code (Anthropic) | `pruebas/sim/test_clima_normal.py` | Pruebas del backend del prototipo | 2026-11-14 |
| Claude Code (Anthropic) | `pruebas/sim/test_cobertura.py` | Pruebas del backend del prototipo | 2026-11-14 |
| Claude Code (Anthropic) | `pruebas/sim/test_condicion.py` | Pruebas del backend del prototipo | 2026-11-14 |
| Claude Code (Anthropic) | `pruebas/sim/test_correcciones_v2.py` | Pruebas del backend del prototipo | 2026-11-14 |
| Claude Code (Anthropic) | `pruebas/sim/test_escribir.py` | Pruebas del backend del prototipo | 2026-11-14 |
| Claude Code (Anthropic) | `pruebas/sim/test_esquema.py` | Pruebas del backend del prototipo | 2026-11-14 |
| Claude Code (Anthropic) | `pruebas/sim/test_incertidumbre.py` | Pruebas del backend del prototipo | 2026-11-14 |
| Claude Code (Anthropic) | `pruebas/sim/test_lotes.py` | Pruebas del backend del prototipo | 2026-11-14 |
| Claude Code (Anthropic) | `pruebas/sim/test_productos.py` | Pruebas del backend del prototipo | 2026-11-14 |
| Claude Code (Anthropic) | `pruebas/sim/test_referencias.py` | Pruebas del backend del prototipo | 2026-11-14 |
| Claude Code (Anthropic) | `pruebas/sim/test_rotaciones.py` | Pruebas del backend del prototipo | 2026-11-14 |
| Claude Code (Anthropic) | `pruebas/sim/test_suelo.py` | Pruebas del backend del prototipo | 2026-11-14 |
| Claude Code (Anthropic) | `pruebas/sim/test_tiempo.py` | Pruebas del backend del prototipo | 2026-11-14 |
| Claude Code (Anthropic) | `pruebas/sim/test_vegetacion.py` | Pruebas del backend del prototipo | 2026-11-14 |
| Claude Code (Anthropic); Cursor (agente) | `pytest.ini` | Configuración común de Datos y Gemelo: rutas, filtro de rasterio y marcadores datos_reales y lento | 2026-11-14 |
| Claude Code (Anthropic) | `requirements-geo-wsl.txt` | Configuración del entorno o de pruebas | 2026-11-14 |
| Claude Code (Anthropic) | `requirements-geo.txt` | Configuración del entorno o de pruebas | 2026-11-14 |
| Claude Code (Anthropic) | `src/simulacion/__init__.py` | Generador y utilidades del prototipo; lo simulado se migra a datos reales | 2026-11-14 |
| Claude Code (Anthropic) | `src/simulacion/agua.py` | Generador y utilidades del prototipo; lo simulado se migra a datos reales | 2026-11-14 |
| Claude Code (Anthropic) | `src/simulacion/azar.py` | Generador y utilidades del prototipo; lo simulado se migra a datos reales | 2026-11-14 |
| Claude Code (Anthropic) | `src/simulacion/clima.py` | Generador y utilidades del prototipo; lo simulado se migra a datos reales | 2026-11-14 |
| Claude Code (Anthropic) | `src/simulacion/cobertura.py` | Generador y utilidades del prototipo; lo simulado se migra a datos reales | 2026-11-14 |
| Claude Code (Anthropic) | `src/simulacion/condicion.py` | Generador y utilidades del prototipo; lo simulado se migra a datos reales | 2026-11-14 |
| Claude Code (Anthropic) | `src/simulacion/config.py` | Variable AGRO_DATOS para ubicar datos fuera del repo (T-D1) | 2026-11-14 |
| Claude Code (Anthropic) | `src/simulacion/escribir_sqlite.py` | Generador y utilidades del prototipo; lo simulado se migra a datos reales | 2026-11-14 |
| Claude Code (Anthropic) | `src/simulacion/esquema_agroversex.sql` | Generador y utilidades del prototipo; lo simulado se migra a datos reales | 2026-11-14 |
| Claude Code (Anthropic) | `src/simulacion/geo/__init__.py` | Pipeline geoespacial del prototipo | 2026-11-14 |
| Claude Code (Anthropic) | `src/simulacion/geo/clim_normal.py` | Pipeline geoespacial del prototipo | 2026-11-14 |
| Claude Code (Anthropic) | `src/simulacion/geo/descargas.py` | Pipeline geoespacial del prototipo | 2026-11-14 |
| Claude Code (Anthropic) | `src/simulacion/geo/esquema_geo.sql` | Pipeline geoespacial del prototipo | 2026-11-14 |
| Claude Code (Anthropic) | `src/simulacion/geo/estaticos.py` | Pipeline geoespacial del prototipo | 2026-11-14 |
| Claude Code (Anthropic) | `src/simulacion/geo/extraer.py` | Pipeline geoespacial del prototipo | 2026-11-14 |
| Claude Code (Anthropic) | `src/simulacion/geo/gmted_tierra.py` | Pipeline geoespacial del prototipo | 2026-11-14 |
| Claude Code (Anthropic) | `src/simulacion/geo/indice_busqueda.py` | Índice de búsqueda sobre unidades CGAZ y nombres de Natural Earth (T-D1) | 2026-11-14 |
| Claude Code (Anthropic) | `src/simulacion/geo/normalizar.py` | Pipeline geoespacial del prototipo | 2026-11-14 |
| Claude Code (Anthropic) | `src/simulacion/geo/teselas.py` | Teselas y simplificación sobre unidad_id de CGAZ, reducción < 100 MB y es_disputa (T-D1, D-016, D-017) | 2026-11-14 |
| Claude Code (Anthropic) | `src/simulacion/geo/unidades.py` | Migración de límites a CGAZ (D-002): lectura, ids, jerarquía, áreas, GPKG y es_disputa en GeoJSON (T-D1, D-017) | 2026-11-14 |
| Claude Code (Anthropic) | `src/simulacion/geo/zonal.py` | Pipeline geoespacial del prototipo | 2026-11-14 |
| Claude Code (Anthropic) | `src/simulacion/incertidumbre.py` | Generador y utilidades del prototipo; lo simulado se migra a datos reales | 2026-11-14 |
| Claude Code (Anthropic) | `src/simulacion/lotes.py` | Generador y utilidades del prototipo; lo simulado se migra a datos reales | 2026-11-14 |
| Claude Code (Anthropic) | `src/simulacion/productos.py` | Generador y utilidades del prototipo; lo simulado se migra a datos reales | 2026-11-14 |
| Claude Code (Anthropic) | `src/simulacion/referencias/__init__.py` | Generador y utilidades del prototipo; lo simulado se migra a datos reales | 2026-11-14 |
| Claude Code (Anthropic) | `src/simulacion/referencias/cargar.py` | Generador y utilidades del prototipo; lo simulado se migra a datos reales | 2026-11-14 |
| Claude Code (Anthropic) | `src/simulacion/rotaciones.py` | Generador y utilidades del prototipo; lo simulado se migra a datos reales | 2026-11-14 |
| Claude Code (Anthropic) | `src/simulacion/suelo.py` | Generador y utilidades del prototipo; lo simulado se migra a datos reales | 2026-11-14 |
| Claude Code (Anthropic) | `src/simulacion/tiempo.py` | Generador y utilidades del prototipo; lo simulado se migra a datos reales | 2026-11-14 |
| Claude Code (Anthropic) | `src/simulacion/variables.py` | Generador y utilidades del prototipo; lo simulado se migra a datos reales | 2026-11-14 |
| Claude Code (Anthropic) | `src/simulacion/vegetacion.py` | Generador y utilidades del prototipo; lo simulado se migra a datos reales | 2026-11-14 |
| Claude Code (Anthropic) | `src/web/index.html` | Frontend del prototipo (base de la app) | 2026-11-14 |
| Claude Code (Anthropic) | `src/web/playwright.app.config.ts` | Frontend del prototipo (base de la app) | 2026-11-14 |
| Claude Code (Anthropic) | `src/web/playwright.busqueda.config.ts` | Frontend del prototipo (base de la app) | 2026-11-14 |
| Claude Code (Anthropic) | `src/web/playwright.config.ts` | Frontend del prototipo (base de la app) | 2026-11-14 |
| Claude Code (Anthropic) | `src/web/playwright.e2e.config.ts` | Frontend del prototipo (base de la app) | 2026-11-14 |
| Claude Code (Anthropic) | `src/web/playwright.escenario.config.ts` | Frontend del prototipo (base de la app) | 2026-11-14 |
| Claude Code (Anthropic) | `src/web/playwright.lotes.config.ts` | Frontend del prototipo (base de la app) | 2026-11-14 |
| Claude Code (Anthropic) | `src/web/playwright.panel.config.ts` | Frontend del prototipo (base de la app) | 2026-11-14 |
| Claude Code (Anthropic) | `src/web/pruebas/api.test.ts` | Pruebas del frontend del prototipo | 2026-11-14 |
| Claude Code (Anthropic) | `src/web/pruebas/api2.test.ts` | Pruebas del frontend del prototipo | 2026-11-14 |
| Claude Code (Anthropic) | `src/web/pruebas/atmosfera.test.ts` | Pruebas del frontend del prototipo | 2026-11-14 |
| Claude Code (Anthropic) | `src/web/pruebas/busqueda.test.ts` | Pruebas del frontend del prototipo | 2026-11-14 |
| Claude Code (Anthropic) | `src/web/pruebas/capas.test.ts` | Pruebas del frontend del prototipo | 2026-11-14 |
| Claude Code (Anthropic) | `src/web/pruebas/comparador.test.ts` | Pruebas del frontend del prototipo | 2026-11-14 |
| Claude Code (Anthropic) | `src/web/pruebas/config.test.ts` | Pruebas del frontend del prototipo | 2026-11-14 |
| Claude Code (Anthropic) | `src/web/pruebas/coropleta.test.ts` | Pruebas del frontend del prototipo | 2026-11-14 |
| Claude Code (Anthropic) | `src/web/pruebas/datos.test.ts` | Pruebas del frontend del prototipo | 2026-11-14 |
| Claude Code (Anthropic) | `src/web/pruebas/e2e/busqueda.spec.ts` | Pruebas del frontend del prototipo | 2026-11-14 |
| Claude Code (Anthropic) | `src/web/pruebas/e2e/captura.mjs` | Pruebas del frontend del prototipo | 2026-11-14 |
| Claude Code (Anthropic) | `src/web/pruebas/e2e/coropleta.spec.ts` | Pruebas del frontend del prototipo | 2026-11-14 |
| Claude Code (Anthropic) | `src/web/pruebas/e2e/escenario.spec.ts` | Pruebas del frontend del prototipo | 2026-11-14 |
| Claude Code (Anthropic) | `src/web/pruebas/e2e/filtros.spec.ts` | Pruebas del frontend del prototipo | 2026-11-14 |
| Claude Code (Anthropic) | `src/web/pruebas/e2e/flujo_completo.spec.ts` | Pruebas del frontend del prototipo | 2026-11-14 |
| Claude Code (Anthropic) | `src/web/pruebas/e2e/lotes.spec.ts` | Pruebas del frontend del prototipo | 2026-11-14 |
| Claude Code (Anthropic) | `src/web/pruebas/e2e/panel.spec.ts` | Pruebas del frontend del prototipo | 2026-11-14 |
| Claude Code (Anthropic) | `src/web/pruebas/e2e/riel.spec.ts` | Pruebas del frontend del prototipo | 2026-11-14 |
| Claude Code (Anthropic) | `src/web/pruebas/e2e/rotaciones.spec.ts` | Pruebas del frontend del prototipo | 2026-11-14 |
| Claude Code (Anthropic) | `src/web/pruebas/e2e/tiempo.spec.ts` | Pruebas del frontend del prototipo | 2026-11-14 |
| Claude Code (Anthropic) | `src/web/pruebas/e2e/vista.spec.ts` | Pruebas del frontend del prototipo | 2026-11-14 |
| Claude Code (Anthropic) | `src/web/pruebas/escenario.test.ts` | Pruebas del frontend del prototipo | 2026-11-14 |
| Claude Code (Anthropic) | `src/web/pruebas/filtros.test.ts` | Pruebas del frontend del prototipo | 2026-11-14 |
| Claude Code (Anthropic) | `src/web/pruebas/fixture.ts` | Pruebas del frontend del prototipo | 2026-11-14 |
| Claude Code (Anthropic) | `src/web/pruebas/fondos.test.ts` | Pruebas del frontend del prototipo | 2026-11-14 |
| Claude Code (Anthropic) | `src/web/pruebas/geodesia.test.ts` | Pruebas del frontend del prototipo | 2026-11-14 |
| Claude Code (Anthropic) | `src/web/pruebas/herramientas.test.ts` | Pruebas del frontend del prototipo | 2026-11-14 |
| Claude Code (Anthropic) | `src/web/pruebas/lotes.test.ts` | Pruebas del frontend del prototipo | 2026-11-14 |
| Claude Code (Anthropic) | `src/web/pruebas/poc/adm2.html` | Pruebas del frontend del prototipo | 2026-11-14 |
| Claude Code (Anthropic) | `src/web/pruebas/poc/adm2.ts` | Pruebas del frontend del prototipo | 2026-11-14 |
| Claude Code (Anthropic) | `src/web/pruebas/poc/medir.spec.ts` | Pruebas del frontend del prototipo | 2026-11-14 |
| Claude Code (Anthropic) | `src/web/pruebas/poc/medirapp.spec.ts` | Pruebas del frontend del prototipo | 2026-11-14 |
| Claude Code (Anthropic) | `src/web/pruebas/poc/servidor.mjs` | Pruebas del frontend del prototipo | 2026-11-14 |
| Claude Code (Anthropic) | `src/web/pruebas/preesqueleto.test.ts` | Pruebas del frontend del prototipo | 2026-11-14 |
| Claude Code (Anthropic) | `src/web/pruebas/recoloreo.test.ts` | Pruebas del frontend del prototipo | 2026-11-14 |
| Claude Code (Anthropic) | `src/web/pruebas/riel.test.ts` | Pruebas del frontend del prototipo | 2026-11-14 |
| Claude Code (Anthropic) | `src/web/pruebas/series.test.ts` | Pruebas del frontend del prototipo | 2026-11-14 |
| Claude Code (Anthropic) | `src/web/pruebas/teselas.test.ts` | Pruebas del frontend del prototipo | 2026-11-14 |
| Claude Code (Anthropic) | `src/web/pruebas/textos.test.ts` | Pruebas del frontend del prototipo | 2026-11-14 |
| Claude Code (Anthropic) | `src/web/pruebas/tiempo.test.ts` | Pruebas del frontend del prototipo | 2026-11-14 |
| Claude Code (Anthropic) | `src/web/public/fuentes/OFL.txt` | Frontend del prototipo (base de la app) | 2026-11-14 |
| Claude Code (Anthropic) | `src/web/server/api.ts` | Servidor de la API del prototipo | 2026-11-14 |
| Claude Code (Anthropic) | `src/web/server/node-sqlite.d.ts` | Servidor de la API del prototipo | 2026-11-14 |
| Claude Code (Anthropic) | `src/web/server/rutas_atributos.ts` | Servidor de la API del prototipo | 2026-11-14 |
| Claude Code (Anthropic) | `src/web/server/rutas_lotes.ts` | Servidor de la API del prototipo | 2026-11-14 |
| Claude Code (Anthropic) | `src/web/server/rutas_rotaciones.ts` | Servidor de la API del prototipo | 2026-11-14 |
| Claude Code (Anthropic) | `src/web/server/rutas_serie.ts` | Servidor de la API del prototipo | 2026-11-14 |
| Claude Code (Anthropic) | `src/web/server/sqlite.ts` | Servidor de la API del prototipo | 2026-11-14 |
| Claude Code (Anthropic) | `src/web/server/teselas.ts` | Servidor de la API del prototipo | 2026-11-14 |
| Claude Code (Anthropic) | `src/web/server/validar.ts` | Servidor de la API del prototipo | 2026-11-14 |
| Claude Code (Anthropic) | `src/web/src/app/App.tsx` | Frontend del prototipo (base de la app) | 2026-11-14 |
| Claude Code (Anthropic) | `src/web/src/app/Cabecera.tsx` | Frontend del prototipo (base de la app) | 2026-11-14 |
| Claude Code (Anthropic) | `src/web/src/app/contraste.ts` | Frontend del prototipo (base de la app) | 2026-11-14 |
| Claude Code (Anthropic) | `src/web/src/app/estado.ts` | Frontend del prototipo (base de la app) | 2026-11-14 |
| Claude Code (Anthropic) | `src/web/src/secciones/tierra/Fps.tsx` | Frontend del prototipo (base de la app) | 2026-11-14 |
| Claude Code (Anthropic) | `src/web/src/app/iconos.tsx` | Frontend del prototipo (base de la app) | 2026-11-14 |
| Claude Code (Anthropic) | `src/web/src/secciones/tierra/Riel.tsx` | Frontend del prototipo (base de la app) | 2026-11-14 |
| Claude Code (Anthropic) | `src/web/src/app/tema.css` | Frontend del prototipo (base de la app) | 2026-11-14 |
| Claude Code (Anthropic) | `src/web/src/comparar/comparar.css` | Frontend del prototipo (base de la app) | 2026-11-14 |
| Claude Code (Anthropic) | `src/web/src/comparar/Dividida.tsx` | Frontend del prototipo (base de la app) | 2026-11-14 |
| Claude Code (Anthropic) | `src/web/src/comparar/Escenario.tsx` | Frontend del prototipo (base de la app) | 2026-11-14 |
| Claude Code (Anthropic) | `src/web/src/comparar/sincronia.ts` | Frontend del prototipo (base de la app) | 2026-11-14 |
| Claude Code (Anthropic) | `src/web/src/datos/banderas.ts` | Frontend del prototipo (base de la app) | 2026-11-14 |
| Claude Code (Anthropic) | `src/web/src/datos/binario.ts` | Frontend del prototipo (base de la app) | 2026-11-14 |
| Claude Code (Anthropic) | `src/web/src/datos/busqueda.ts` | Frontend del prototipo (base de la app) | 2026-11-14 |
| Claude Code (Anthropic) | `src/web/src/datos/busqueda.worker.ts` | Frontend del prototipo (base de la app) | 2026-11-14 |
| Claude Code (Anthropic) | `src/web/src/datos/capas.ts` | Frontend del prototipo (base de la app) | 2026-11-14 |
| Claude Code (Anthropic) | `src/web/src/datos/cliente.ts` | Frontend del prototipo (base de la app) | 2026-11-14 |
| Claude Code (Anthropic) | `src/web/src/datos/consultas.ts` | Frontend del prototipo (base de la app) | 2026-11-14 |
| Claude Code (Anthropic) | `src/web/src/datos/desescalar.ts` | Frontend del prototipo (base de la app) | 2026-11-14 |
| Claude Code (Anthropic) | `src/web/src/datos/filtrar.ts` | Frontend del prototipo (base de la app) | 2026-11-14 |
| Claude Code (Anthropic) | `src/web/src/datos/indice.ts` | Frontend del prototipo (base de la app) | 2026-11-14 |
| Claude Code (Anthropic) | `src/web/src/datos/series.ts` | Frontend del prototipo (base de la app) | 2026-11-14 |
| Claude Code (Anthropic) | `src/web/src/datos/tipos.ts` | Frontend del prototipo (base de la app) | 2026-11-14 |
| Claude Code (Anthropic) | `src/web/src/datos/wkt.ts` | Frontend del prototipo (base de la app) | 2026-11-14 |
| Claude Code (Anthropic) | `src/web/src/estilos.css` | Frontend del prototipo (base de la app) | 2026-11-14 |
| Claude Code (Anthropic) | `src/web/src/globo/atmosfera.ts` | Frontend del prototipo (base de la app) | 2026-11-14 |
| Claude Code (Anthropic) | `src/web/src/globo/config.ts` | Frontend del prototipo (base de la app) | 2026-11-14 |
| Claude Code (Anthropic) | `src/web/src/globo/Controles.tsx` | Frontend del prototipo (base de la app) | 2026-11-14 |
| Claude Code (Anthropic) | `src/web/src/globo/coropleta.ts` | Frontend del prototipo (base de la app) | 2026-11-14 |
| Claude Code (Anthropic) | `src/web/src/globo/estrellas.ts` | Frontend del prototipo (base de la app) | 2026-11-14 |
| Claude Code (Anthropic) | `src/web/src/globo/fondos.ts` | Frontend del prototipo (base de la app) | 2026-11-14 |
| Claude Code (Anthropic) | `src/web/src/globo/globo.css` | Frontend del prototipo (base de la app) | 2026-11-14 |
| Claude Code (Anthropic) | `src/web/src/globo/Globo.tsx` | Frontend del prototipo (base de la app) | 2026-11-14 |
| Claude Code (Anthropic) | `src/web/src/globo/leyenda.tsx` | Frontend del prototipo (base de la app) | 2026-11-14 |
| Claude Code (Anthropic) | `src/web/src/globo/patron.ts` | Frontend del prototipo (base de la app) | 2026-11-14 |
| Claude Code (Anthropic) | `src/web/src/globo/recoloreo.ts` | Frontend del prototipo (base de la app) | 2026-11-14 |
| Claude Code (Anthropic) | `src/web/src/graficos/BandaSerie.tsx` | Frontend del prototipo (base de la app) | 2026-11-14 |
| Claude Code (Anthropic) | `src/web/src/graficos/SensorSatelite.tsx` | Frontend del prototipo (base de la app) | 2026-11-14 |
| Claude Code (Anthropic) | `src/web/src/herramientas/AvisoZoom.tsx` | Frontend del prototipo (base de la app) | 2026-11-14 |
| Claude Code (Anthropic) | `src/web/src/herramientas/geodesia.ts` | Frontend del prototipo (base de la app) | 2026-11-14 |
| Claude Code (Anthropic) | `src/web/src/herramientas/herramientas.css` | Frontend del prototipo (base de la app) | 2026-11-14 |
| Claude Code (Anthropic) | `src/web/src/herramientas/Medir.tsx` | Frontend del prototipo (base de la app) | 2026-11-14 |
| Claude Code (Anthropic) | `src/web/src/main.tsx` | Frontend del prototipo (base de la app) | 2026-11-14 |
| Claude Code (Anthropic) | `src/web/src/paneles/Busqueda.tsx` | Frontend del prototipo (base de la app) | 2026-11-14 |
| Claude Code (Anthropic) | `src/web/src/paneles/Chip.tsx` | Frontend del prototipo (base de la app) | 2026-11-14 |
| Claude Code (Anthropic) | `src/web/src/paneles/comparador/datos.ts` | Reexportación hacia secciones/rotaciones/datos.ts; Petición de desarrollo local que usa PanelRegion | 2026-11-14 |
| Claude Code (Anthropic) | `src/web/src/secciones/rotaciones/datos.ts` | Frontend del prototipo (base de la app), movido desde paneles/comparador sin China | 2026-11-14 |
| Claude Code (Anthropic) | `src/web/src/secciones/rotaciones/demo.html` | Frontend del prototipo (base de la app), movido desde paneles/comparador | 2026-11-14 |
| Claude Code (Anthropic) | `src/web/src/secciones/rotaciones/demo.tsx` | Frontend del prototipo (base de la app), movido desde paneles/comparador | 2026-11-14 |
| Claude Code (Anthropic) | `src/web/src/secciones/rotaciones/fixtures.ts` | Frontend del prototipo (base de la app), movido desde paneles/comparador sin China | 2026-11-14 |
| Claude Code (Anthropic) | `src/web/src/secciones/rotaciones/ordenar.ts` | Frontend del prototipo (base de la app), movido desde paneles/comparador | 2026-11-14 |
| Claude Code (Anthropic) | `src/web/src/secciones/rotaciones/Prioridades.tsx` | Frontend del prototipo (base de la app), movido desde paneles/comparador | 2026-11-14 |
| Claude Code (Anthropic) | `src/web/src/paneles/comparador/Rotaciones.tsx` | Reexportación de ResumenPanel como Rotaciones para PanelRegion; Resumen corto de la pestaña Rotaciones con enlace a la sección | 2026-11-14 |
| Claude Code (Anthropic) | `src/web/src/secciones/rotaciones/ResumenPanel.tsx` | Resumen del panel, movido y renombrado desde paneles/comparador/Rotaciones.tsx, sin China | 2026-11-14 |
| Claude Code (Anthropic) | `src/web/src/secciones/rotaciones/TarjetaEstrategia.tsx` | Frontend del prototipo (base de la app), movido desde paneles/comparador sin China | 2026-11-14 |
| Claude Code (Anthropic) | `src/web/pruebas/rotaciones_movido.test.ts` | Pruebas de los reexportes y de la salida de China de Rotaciones | 2026-11-14 |
| Claude Code (Anthropic) | `src/web/src/paneles/filtros/Filtros.tsx` | Frontend del prototipo (base de la app) | 2026-11-14 |
| Claude Code (Anthropic) | `src/web/src/paneles/filtros/filtros_regionales.ts` | Frontend del prototipo (base de la app) | 2026-11-14 |
| Claude Code (Anthropic) | `src/web/src/paneles/Fuentes.tsx` | Frontend del prototipo (base de la app) | 2026-11-14 |
| Claude Code (Anthropic) | `src/web/src/paneles/lotes/Banco.tsx` | Frontend del prototipo (base de la app) | 2026-11-14 |
| Claude Code (Anthropic) | `src/web/src/paneles/lotes/demo.html` | Frontend del prototipo (base de la app) | 2026-11-14 |
| Claude Code (Anthropic) | `src/web/src/paneles/lotes/demo.tsx` | Frontend del prototipo (base de la app) | 2026-11-14 |
| Claude Code (Anthropic) | `src/web/src/paneles/lotes/Lotes.tsx` | Frontend del prototipo (base de la app) | 2026-11-14 |
| Claude Code (Anthropic) | `src/web/src/paneles/lotes/modelo.ts` | Frontend del prototipo (base de la app) | 2026-11-14 |
| Claude Code (Anthropic) | `src/web/src/paneles/Miga.tsx` | Frontend del prototipo (base de la app) | 2026-11-14 |
| Claude Code (Anthropic) | `src/web/src/paneles/panel.css` | Frontend del prototipo (base de la app) | 2026-11-14 |
| Claude Code (Anthropic) | `src/web/src/paneles/PanelCapas.tsx` | Frontend del prototipo (base de la app) | 2026-11-14 |
| Claude Code (Anthropic) | `src/web/src/paneles/PanelRegion.tsx` | Frontend del prototipo (base de la app) | 2026-11-14 |
| Claude Code (Anthropic) | `src/web/src/paneles/Resumen.tsx` | Frontend del prototipo (base de la app) | 2026-11-14 |
| Claude Code (Anthropic) | `src/web/src/paneles/Series.tsx` | Frontend del prototipo (base de la app) | 2026-11-14 |
| Claude Code (Anthropic) | `src/web/src/paneles/Suelo.tsx` | Frontend del prototipo (base de la app) | 2026-11-14 |
| Claude Code (Anthropic) | `src/web/src/textos/avisos.ts` | Frontend del prototipo (base de la app) | 2026-11-14 |
| Claude Code (Anthropic) | `src/web/src/textos/en.ts` | Frontend del prototipo (base de la app) | 2026-11-14 |
| Claude Code (Anthropic) | `src/web/src/textos/es.ts` | Frontend del prototipo (base de la app) | 2026-11-14 |
| Claude Code (Anthropic) | `src/web/src/textos/glosario.ts` | Frontend del prototipo (base de la app) | 2026-11-14 |
| Claude Code (Anthropic) | `src/web/src/textos/i18n.ts` | Frontend del prototipo (base de la app) | 2026-11-14 |
| Claude Code (Anthropic) | `src/web/src/textos/modos.ts` | Frontend del prototipo (base de la app) | 2026-11-14 |
| Claude Code (Anthropic) | `src/web/src/tiempo/CintaEnso.tsx` | Frontend del prototipo (base de la app) | 2026-11-14 |
| Claude Code (Anthropic) | `src/web/src/tiempo/huecos.ts` | Frontend del prototipo (base de la app) | 2026-11-14 |
| Claude Code (Anthropic) | `src/web/src/tiempo/LineaTiempo.tsx` | Frontend del prototipo (base de la app) | 2026-11-14 |
| Claude Code (Anthropic) | `src/web/src/tiempo/Reproductor.ts` | Frontend del prototipo (base de la app) | 2026-11-14 |
| Claude Code (Anthropic) | `src/web/src/tiempo/tiempo.css` | Frontend del prototipo (base de la app) | 2026-11-14 |
| Claude Code (Anthropic) | `src/web/src/tiempo/valor.ts` | Frontend del prototipo (base de la app) | 2026-11-14 |
| Claude Code (Anthropic) | `src/web/vite.config.ts` | Frontend del prototipo (base de la app) | 2026-11-14 |
| Claude Code (Anthropic) | `src/simulacion/geo/descargas_nasa.py` | Descarga con subconjunto por variable vía OPeNDAP de Earthdata (T-D3) | 2026-11-14 |
| Claude Code (Anthropic) | `pruebas/geo/test_descargas_nasa.py` | Pruebas de la descarga con subconjunto (T-D3) | 2026-11-14 |
| Claude Code (Anthropic) | `src/simulacion/geo/imerg_late.py` | Regla de días válidos de IMERG Late por celda (D-011) | 2026-11-14 |
| Claude Code (Anthropic) | `pruebas/geo/test_imerg_late.py` | Pruebas de la regla de IMERG Late | 2026-11-14 |
| Claude Code (Anthropic) | `src/simulacion/geo/sensibilidad_late.py` | Sensibilidad 70/80/90 de IMERG Late en Colombia | 2026-11-14 |
| Claude Code (Anthropic) | `pruebas/geo/test_config_datos.py` | Prueba de la variable AGRO_DATOS (T-D1) | 2026-11-14 |
| Claude Code (Anthropic) | `pruebas/geo/test_cgaz_lectura.py` | Pruebas de lectura de CGAZ y verificación de hash (T-D1) | 2026-11-14 |
| Claude Code (Anthropic) | `pruebas/geo/test_colombia.py` | Pruebas de la comparación de Colombia con DIVIPOLA (T-D1) | 2026-11-14 |
| Claude Code (Anthropic) | `src/simulacion/geo/colombia.py` | Comparación de municipios de CGAZ con DIVIPOLA del DANE (T-D1) | 2026-11-14 |
| Claude Code (Anthropic) | `contratos/unidades.md` | Redacción del contrato de unidades a partir de los datos de CGAZ (T-D1) | 2026-11-14 |
| Claude Code (Anthropic) | `src/simulacion/geo/zonal_mensual.py` | Motor zonal con pesos por firma de grilla (T-D2) | 2026-11-14 |
| Claude Code (Anthropic) | `src/simulacion/geo/lectura_nasa.py` | Lectura orientada de netCDF con puntos de control (T-D2) | 2026-11-14 |
| Claude Code (Anthropic) | `src/simulacion/geo/serie_mensual.py` | Corrida de series mensuales por país (T-D2) | 2026-11-14 |
| Claude Code (Anthropic) | `pruebas/geo/test_zonal_mensual.py` | Pruebas del motor zonal (T-D2) | 2026-11-14 |
| Claude Code (Anthropic) | `pruebas/geo/test_lectura_nasa.py` | Pruebas de la orientación de lecturas (T-D2) | 2026-11-14 |
| Claude Code (Anthropic) | `src/simulacion/geo/pi_d1_colombia.py` | Respuesta preliminar de PI-D1 en Colombia (area frente a cultivo) | 2026-11-14 |
| Claude Code (Anthropic) | `datos/fichas/gfsad1kcm.md` | Ficha de dataset de GFSAD1KCM con DOI y licencia verificados en CMR (T-D2) | 2026-11-14 |
| Claude Code (Anthropic) | `datos/control_desfase_imerg.py`, `datos/meses_precipitacion_col.py` | Control del desfase de IMERG y meses de precipitación de Colombia (T-D2) | 2026-11-14 |
| Claude Code (Anthropic) | `datos/sensibilidad_col.py`, `datos/comparar_sens.py`, `datos/fixture_empalme_imerg.py` | Sensibilidades de clases y reliability, y fixture del empalme IMERG (T-D2) | 2026-11-14 |
| Claude Code (Anthropic) | `pruebas/geo/test_lectura_nasa.py`, `pruebas/geo/test_teselas.py` | Prueba de orientación 120E/120O de IMERG y skipif de test_ruta_wsl (T-D2) | 2026-11-14 |
| Claude Code (Anthropic) | `src/lotes_demo/imerg_diario.py` y `pruebas/lotes/test_imerg_diario.py` | Lectura puntual de IMERG Final V07 diario por OPeNDAP (T-D5 B) | 2026-11-14 |
| Claude Code (Anthropic) | `src/lotes_demo/forzantes.py` y `pruebas/lotes/test_forzantes.py` | Lectura y validación de forzantes POWER e IMERG (T-D5 B) | 2026-11-14 |
| Claude Code (Anthropic); Antigravity (Google DeepMind) | `src/lotes_demo/suelo.py` y `pruebas/lotes/test_lotes_suelo.py` | Parámetros de suelo desde SoilGrids REST (T-D5 B); Claves escalares en la raíz de `parametros_suelo.json` (`arena`, `arcilla`, `mo_pct`, `cos_t_ha`, `profundidad_m`) para `gemelo.suelo.perfil_desde_parametros_datos` conservando `"parametros"` con cuantiles (T-D5 Prioridad 3C, D-027) | 2026-11-14 |
| Claude Code (Anthropic) | `src/lotes_demo/hls_validez.py` y `pruebas/lotes/test_hls_validez.py` | Fracción de observaciones HLS válidas por píxel y mes (T-D5 B) | 2026-11-14 |
| Claude Code (Anthropic) | `src/lotes_demo/construir_lotes.py`, `pruebas/lotes/test_lotes_demo.py`, `datos/lotes/lotes_demo.json` | Construcción de lotes_demo.json (T-D5 B) | 2026-11-14 |
| Claude Code (Anthropic) | `contratos/forzantes_gemelo.md` y fichas `datos/fichas/power_diario.md`, `hls_v2.md`, `imerg_diario.md` | Redacción del contrato y las fichas (T-D5 B) | 2026-11-14 |
| Claude Code (Anthropic) | `src/web/pruebas/sin_procedencia_china.test.ts`, `datos/evidencia/CPC-ASSESS97-AFRICA.yaml` | Prueba de procedencia en server y paneles; ficha de CPC que reemplaza a Cai 2025 (D-024) | 2026-11-14 |
| Claude Code (Anthropic) | `datos/evidencia/kluger_afiliaciones.md`, `datos/evidencia/koppen_beck2023_licencia.md` | Evidencia de afiliaciones de Kluger y de licencia de Köppen-Geiger (D-024) | 2026-11-14 |
| Claude Code (Anthropic) | `src/web/src/secciones/tierra/interfaz.ts` | Interfaz del globo para Web, contrato web_componentes §4 | 2026-11-14 |
| Claude Code (Anthropic) | `src/web/src/secciones/tierra/Tierra.tsx` | Sección Tierra: compone el globo que montaba App.tsx | 2026-11-14 |
| Claude Code (Anthropic) | `src/web/pruebas/interfaz.test.ts` | Pruebas de la interfaz del globo | 2026-11-14 |
| Claude Code (Anthropic) | `src/web/src/comun/unidades.ts` | Conversión única paraMostrar con días reales del mes, contrato web_componentes §5 | 2026-11-14 |
| Claude Code (Anthropic) | `src/web/pruebas/unidades.test.ts` | Pruebas de paraMostrar y sus tres llamadores | 2026-11-14 |
| Claude Code (Anthropic) | `src/web/pruebas/textos_tierra.test.ts` | Pruebas de textos por clave de la sección Tierra | 2026-11-14 |
| Claude Code (Anthropic) | `src/web/src/comun/unidades.ts`, `src/web/pruebas/empalme_imerg.test.ts` | Conversión mm/day de IMERG Late en paraMostrar y prueba del empalme 2025-09 a 2025-10 (D-023) | 2026-11-14 |
| Claude Code (Anthropic) | `datos/extraer_pares_variable_unidad.py` | Extrae los pares (variable, unidad) de serie_mensual para la prueba de paraMostrar | 2026-11-14 |
| Claude Code (Anthropic) | `src/web/pruebas/paneles_unidad.test.ts` | Prueba de que los paneles muestran error ante una unidad sin conversión | 2026-11-14 |
| Claude Code (Anthropic) | `src/web/pruebas/zona_disputa.test.ts` y cambios de disputa en `globo/`, `datos/`, `paneles/` | Zonas en disputa con es_disputa = 1 en las tres capas y clave de texto en vez de país (decisión 3) | 2026-11-14 |
| Claude Code (Anthropic) | `src/web/src/globo/fondos.ts`, `src/web/pruebas/fondos.test.ts`, `src/web/pruebas/e2e/captura.mjs` | Fondo del globo con NASA GIBS (D-020) y pruebas de atribución | 2026-11-14 |
| Claude Code (Anthropic) | `src/mapa_estatico/__init__.py`, `src/mapa_estatico/construir.py`, `pruebas/mapa/test_construir.py` | Conversión de series mensuales a matrices estáticas comprimidas, copia de lotes_demo.json y manifiesto con sha256 (T-D9, D-027) | 2026-11-14 |
| Claude Code (Anthropic) | `src/web/src/comun/rutas.ts`, `src/web/src/datos/estatico.ts`, `src/web/pruebas/estatico.test.ts` | Lectura de archivos estáticos reales en el globo y paneles sin servidor, y pruebas con datos reales de Colombia (T-D9) | 2026-11-14 |
| Claude Code (Anthropic) | `contratos/web_datos.md` | Contrato v0 de archivos estáticos para el Mapa y Web con tamaños y sumas SHA-256 (T-D9, T-D7 Parte C) | 2026-11-14 |
| Claude Code (Anthropic) | `src/web/pruebas/rutas_base.test.ts` | Prueba de que teselas e índice respetan la base de publicación (BASE_URL) | 2026-11-14 |
| Antigravity (Google DeepMind) | `src/lotes_demo/__init__.py` | Exportaciones públicas de `lotes_demo` incluyendo `exposicion_erosiva` y `umbral_p90_semanal` (T-D6) | 2026-11-14 |
| Antigravity (Google DeepMind) | `src/lotes_demo/erosion.py` y `pruebas/lotes/test_erosion.py` | Función `exposicion_erosiva`, umbral semanal P90 sin fuga temporal, pendiente NASADEM 30 m (`S` de McCool et al., 1987) y erodabilidad `K` de Williams (1995) con pruebas TDD (T-D6 Prioridad 4) | 2026-11-14 |
| Antigravity (Google DeepMind) | `src/lotes_demo/forzantes.py`, `src/lotes_demo/resumen_forzantes.py` y `pruebas/lotes/test_forzantes.py` | Corrección de temperatura por altura (`T2M_CORR`, `T2M_MAX_CORR`, `T2M_MIN_CORR`), validación bootstrap anual contra GHCN-Daily `COM00080370` y alineación horaria UTC / correlaciones 1d, 5d y mensual entre POWER e IMERG (T-D5 Prioridades 3A y 3B, D-027) | 2026-11-14 |
| Antigravity (Google DeepMind) | `contratos/forzantes_gemelo.md`, `datos/fichas/ghcn_daily.md`, `datos/fichas/nasadem_hgt.md`, `datos/fichas/power_diario.md`, `datos/fichas/imerg_diario.md`, `LICENCIAS_TERCEROS.md`, `CITAS.md` | Actualización de contrato v1, fichas de dataset, licencias y citas primarias verificadas (T-D5 y T-D6, D-027) | 2026-11-14 |
| Claude Code (Anthropic) | `src/web/pruebas/estatico.test.ts` (escala de color sobre paraMostrar, empalme frente a climatología), `src/web/src/datos/estatico.ts` (leerGz con Content-Encoding), `src/web/src/globo/config.ts` y `src/web/pruebas/config.test.ts` (adm2 hasta z11 con apagado por opacidad, es_disputa), `src/lotes_demo/resumen_forzantes.py` (cobertura de COM00080370 y nota generada) | Correcciones del punto 3 del director, 19:15 | 2026-11-14 |

## Área Gemelo


Registro exigido por las guías de Space Apps 2026 y AGENTS.md §5.3. Cada archivo de código asistido por SI lleva la cabecera `# asistido por SI: <herramienta y uso>` y una fila aquí.

| Herramienta | Archivo | Propósito | Fecha |
|-|-|-|-|
| Cursor (agente) | `requirements-gemelo.txt` | Dependencias directas fijadas del área Gemelo | 2026-11-14 |
| Cursor (agente) | `src/gemelo/__init__.py` | Paquete y exportaciones del núcleo del gemelo digital | 2026-11-14 |
| Cursor (agente) | `src/gemelo/__main__.py` | Punto de entrada CLI de `python -m gemelo` | 2026-11-14 |
| Cursor (agente) | `src/gemelo/agua.py` | Balance hídrico diario (FAO-56 / AquaCrop) | 2026-11-14 |
| Cursor (agente) | `src/gemelo/api.py` | Fachada pública del contrato del gemelo | 2026-11-14 |
| Cursor (agente) | `src/gemelo/biomasa.py` | Crecimiento de biomasa y partición a cosecha | 2026-11-14 |
| Cursor (agente) | `src/gemelo/carbono.py` | Dinámica diaria de carbono orgánico del suelo (ICBM) | 2026-11-14 |
| Cursor (agente) | `src/gemelo/cli.py` | Interfaz de línea de comandos para simular, optimizar y empaquetar | 2026-11-14 |
| Cursor (agente) | `src/gemelo/clima.py` | Lectura y validación de series climáticas diarias (POWER y Datos) | 2026-11-14 |
| Cursor (agente) | `src/gemelo/cobertura.py` | Cobertura viva, rastrojo y exposición erosiva | 2026-11-14 |
| Cursor (agente) | `src/gemelo/dinamica.py` | Evaluación dinámica de cultivos y cobertura entre ciclos | 2026-11-14 |
| Cursor (agente) | `src/gemelo/enso.py` | Clasificación de fases ENSO (ONI) y pesos por escenario | 2026-11-14 |
| Cursor (agente) | `src/gemelo/entrada.py` | Validación y carga de configuraciones YAML/JSON del lote | 2026-11-14 |
| Cursor (agente) | `src/gemelo/escenarios.py` | Construcción de ventanas históricas y escenarios sintéticos | 2026-11-14 |
| Cursor (agente) | `src/gemelo/fenologia.py` | Grados-día acumulados y etapas fenológicas FAO-56 | 2026-11-14 |
| Cursor (agente) | `src/gemelo/incertidumbre.py` | Muestreo Latino Hipercúbico (LHS) del ensamble de parámetros | 2026-11-14 |
| Cursor (agente) | `src/gemelo/indicadores.py` | Resumen de indicadores, percentiles, riesgos y heladas | 2026-11-14 |
| Cursor (agente) | `src/gemelo/manejo.py` | Reglas agronómicas, sucesión, siembra, riego y fertilización | 2026-11-14 |
| Cursor (agente) | `src/gemelo/modelos.py` | Estructuras de datos del lote, cultivos, estrategias y estado | 2026-11-14 |
| Cursor (agente) | `src/gemelo/nitrogeno.py` | Balance simplificado de nitrógeno mineral y orgánico | 2026-11-14 |
| Cursor (agente) | `src/gemelo/optimizacion.py` | Optimización multiobjetivo NSGA-II de rotaciones y manejo (`pymoo`) | 2026-11-14 |
| Cursor (agente) | `src/gemelo/paquete.py` | Generación de paquetes JSON estáticos precalculados para Web | 2026-11-14 |
| Cursor (agente) | `src/gemelo/parametros.py` | Carga de tablas YAML de referencias y parámetros del gemelo | 2026-11-14 |
| Cursor (agente) | `src/gemelo/prioridades.py` | Normalización y ordenamiento por pesos de deslizadores Web | 2026-11-14 |
| Cursor (agente) | `src/gemelo/procedencia.py` | Trazabilidad de parámetros (`Parametro`) y etiquetas de evidencia | 2026-11-14 |
| Cursor (agente) | `src/gemelo/salida.py` | Ensamblado del documento de salida v1/v1.1 conforme al contrato | 2026-11-14 |
| Cursor (agente) | `src/gemelo/simulador.py` | Motor diario de simulación acoplado suelo-agua-C-N-cultivo | 2026-11-14 |
| Cursor (agente) | `src/gemelo/suelo.py` | Perfiles edáficos (SoilGrids, Datos, manual) y Saxton-Rawls | 2026-11-14 |
| Cursor (agente) | `src/gemelo/tarjetas.py` | Generación de tarjetas explicativas de cinco secciones | 2026-11-14 |
| Cursor (agente) | `src/gemelo/textos.py` | Catálogo bilingüe `en`/`es` de claves con parámetros | 2026-11-14 |
| Cursor (agente) | `src/gemelo/referencias/agua_suelo.yaml` | Parámetros físicos de agua y suelo con fuente y rango | 2026-11-14 |
| Cursor (agente) | `src/gemelo/referencias/carbono_nitrogeno.yaml` | Parámetros de balance ICBM C/N con fuente y rango | 2026-11-14 |
| Cursor (agente) | `src/gemelo/referencias/cultivos.yaml` | Catálogo fenológico y parámetros de cultivos | 2026-11-14 |
| Cursor (agente) | `pruebas/gemelo/conftest.py` | Fixtures compartidos de pruebas del gemelo | 2026-11-14 |
| Cursor (agente) | `pruebas/gemelo/test_clima_suelo.py` | Pruebas de lectura climática, SoilGrids y dominio Saxton-Rawls | 2026-11-14 |
| Cursor (agente) | `pruebas/gemelo/test_contrato.py` | Pruebas de conformidad con `contratos/gemelo_api.md` | 2026-11-14 |
| Cursor (agente) | `pruebas/gemelo/test_dinamica.py` | Pruebas de cobertura continua y rotación dinámica | 2026-11-14 |
| Cursor (agente) | `pruebas/gemelo/test_entradas_datos.py` | Pruebas de lectura de forzantes de Datos y lotes DEMO | 2026-11-14 |
| Cursor (agente) | `pruebas/gemelo/test_escenarios_incertidumbre.py` | Pruebas de escenarios climáticos, ENSO e incertidumbre LHS | 2026-11-14 |
| Cursor (agente) | `pruebas/gemelo/test_optimizacion.py` | Pruebas de optimización multiobjetivo con `pymoo` | 2026-11-14 |
| Cursor (agente) | `pruebas/gemelo/test_paquete.py` | Pruebas de exportación de paquetes estáticos para Web | 2026-11-14 |
| Cursor (agente) | `pruebas/gemelo/test_prioridades.py` | Pruebas de normalización y orden por pesos de objetivos | 2026-11-14 |
| Cursor (agente) | `pruebas/gemelo/test_procedencia.py` | Pruebas de etiquetas y trazabilidad de referencias YAML | 2026-11-14 |
| Cursor (agente) | `pruebas/gemelo/test_procedencia_parametros.py` | Pruebas de clase `Parametro` y calibración local | 2026-11-14 |
| Cursor (agente) | `pruebas/gemelo/test_procesos.py` | Pruebas unitarias físicas de agua, biomasa, C, N y fenología | 2026-11-14 |
| Cursor (agente) | `pruebas/gemelo/test_textos.py` | Pruebas de paridad `en`/`es` y ausencia de fuga de idioma | 2026-11-14 |
| Cursor (agente) | `ejemplos/escenario_ames.yaml` | Escenario interno de referencia (Ames) para pruebas | 2026-11-14 |
| Cursor (agente) | `ejemplos/escenario_ipiales.yaml` | Escenario de referencia (Ipiales) | 2026-11-14 |
| Cursor (agente) | `ejemplos/escenario_mead.yaml` | Escenario interno de referencia (Mead) para fijación de pruebas | 2026-11-14 |
| Cursor (agente) | `ejemplos/visualizar_gemelo.py` | Script auxiliar de diagnóstico visual del gemelo | 2026-11-14 |
| Cursor (agente) | `contratos/gemelo_api.md` y `src/gemelo/README.md` | Documentación del contrato v1/v1.1 y guía técnica del gemelo | 2026-11-14 |
| Antigravity (agente) | `requirements-gemelo.lock.txt` | Bloqueo reproducible con hashes SHA-256 generado con `uv pip compile` | 2026-11-14 |
| Antigravity (agente) | `SI_USO.md` y `LICENCIAS_TERCEROS.md` | Inventario de uso de SI y auditoría de licencias y citas verificadas | 2026-11-14 |
| Antigravity (agente) | `src/gemelo/suelo.py`, `src/gemelo/textos.py`, `src/gemelo/tarjetas.py`, `pruebas/gemelo/test_clima_suelo.py`, `src/gemelo/README.md` | Separación de pruebas de dominio y declaración bilingüe de limitación de SoilGrids en Andisoles (`D-029`, `D-030`) | 2026-11-14 |
| Antigravity (agente) | `src/gemelo/suelo.py`, `pruebas/gemelo/test_entradas_datos.py` | Adaptación de `perfil_desde_parametros_datos` al esquema T-D5 anidado en `parametros` | 2026-11-14 |
| Claude Code (Anthropic) | `src/gemelo/alertas.py`, `src/gemelo/clima.py`, `src/gemelo/escenarios.py`, `src/gemelo/entrada.py`, `src/gemelo/salida.py`, `src/gemelo/simulador.py`, `src/gemelo/tarjetas.py`, `src/gemelo/textos.py`, `src/gemelo/paquete.py`, `pruebas/gemelo/test_alertas.py`, `pruebas/gemelo/test_clima_suelo.py`, `ejemplos/escenario_ipiales.yaml`, `ejemplos/escenario_mead.yaml`, `contratos/gemelo_api.md` | Bloque 2: avisos del suelo calibrado en `reunir_parametros`, alerta de helada en etapa sensible (`D-032`), lluvia alterna IMERG como sensibilidad técnica y forzantes T-D5 en los lotes DEMO (modelo Opus 5.5) | 2026-11-14 |
| Claude Code (Anthropic) | `src/gemelo/alertas.py`, `src/gemelo/entrada.py`, `src/gemelo/textos.py`, `src/gemelo/tarjetas.py`, `pruebas/gemelo/test_alertas.py`, `ejemplos/escenario_ipiales.yaml`, `ejemplos/escenario_mead.yaml`, `contratos/gemelo_api.md` | Climatología de heladas de la estación cercana, umbral de helada por cultivo y lote leído de `lotes_demo.json` (modelo Opus 5.5) | 2026-11-14 |
| Claude Code (Anthropic) | `src/gemelo/indicadores.py`, `src/gemelo/simulador.py`, `src/gemelo/clima.py`, `src/gemelo/entrada.py`, `src/gemelo/optimizacion.py`, `src/gemelo/prioridades.py`, `src/gemelo/tarjetas.py`, `src/gemelo/textos.py`, `src/gemelo/api.py`, `src/gemelo/cli.py`, `src/gemelo/paquete.py`, `contratos/gemelo_api.md`, `contratos/prioridades_casos.json`, pruebas | v1.2: exposicion_erosiva de Datos como objetivo del deslizador suelo, alias obsoleto y casos de orden compartidos con Web (modelo Opus 5.5) | 2026-11-14 |

Notas de procedencia sin generación nueva por este equipo de Gemelo:
- `src/gemelo/referencias/enso.yaml` y `src/gemelo/referencias/sucesion.yaml` son copias literales de `origin/datos`.
- La idea científica, alcance, reglas de corte y decisiones (`D-001` a `D-030`) fueron definidas por el equipo humano y aprobadas por el director en `decisiones/registro.md`.

## Datos y Web (continuación)

| Herramienta | Archivo | Propósito | Fecha |
|-|-|-|-|
| Claude Code (Anthropic) | `pruebas/lotes/test_erosion_gemelo.py` | Prueba de que la exposición erosiva de Datos y del Gemelo coincide con la misma lluvia POWER y la misma fracción desnuda (director, 20:50) | 2026-11-14 |
| Claude Code (Anthropic) | `src/web/src/app/ruta.ts` | Rutas por hash de las siete secciones, contrato web_componentes §3 | 2026-11-14 |
| Claude Code (Anthropic) | `src/web/src/app/Navegacion.tsx` | Navegación entre las siete secciones con aria-current | 2026-11-14 |
| Claude Code (Anthropic) | `src/web/src/app/SeccionVacia.tsx` | Cuerpo común de las secciones sin contenido, con aviso.sin_dato | 2026-11-14 |
| Claude Code (Anthropic) | `src/web/src/app/ejemplos.ts` | Carga de ejemplos detrás de la bandera VITE_EJEMPLOS | 2026-11-14 |
| Claude Code (Anthropic) | `src/web/src/ejemplos/index.ts` | Módulo de ejemplos con su marcador, solo entra con VITE_EJEMPLOS=1 | 2026-11-14 |
| Claude Code (Anthropic) | `src/web/src/secciones/portada/Portada.tsx` | Portada: idea en dos frases y botón del recorrido guiado | 2026-11-14 |
| Claude Code (Anthropic) | `src/web/src/secciones/gemelo/Gemelo.tsx` | Sección El gemelo del lote: carga del lote y del ejemplo (T-W6) | 2026-11-14 |
| Claude Code (Anthropic) | `src/web/src/secciones/ciencia/Ciencia.tsx` | Sección Ciencia y validación: métricas, preguntas, limitaciones (T-W6) | 2026-11-14 |
| Claude Code (Anthropic) | `src/web/src/secciones/datos-abiertos/DatosAbiertos.tsx` | Sección Datos abiertos: ficha, descarga y comando (T-W6) | 2026-11-14 |
| Claude Code (Anthropic) | `src/web/src/secciones/rotaciones/Rotaciones.tsx` | Sección Rotaciones: lote por la ruta, datos por props y estructura de la v1.1 | 2026-11-14 |
| Claude Code (Anthropic) | `src/web/src/secciones/rotaciones/gemelo.ts` | Tipos de la salida del gemelo, contrato v1 | 2026-11-14 |
| Claude Code (Anthropic) | `src/web/src/secciones/rotaciones/lector.ts` | Capa que lee la salida del gemelo y carga el ejemplo tras la bandera; Lectura de lotes_demo.json y del paquete estático del gemelo v1.1 | 2026-11-14 |
| Claude Code (Anthropic) | `src/web/src/secciones/rotaciones/ejemplo_gemelo.json` | Ejemplo ficticio SIMULADO que sigue el contrato v1 del gemelo (JSON sin comentario de cabecera); Ejemplo SIMULADO pasado a la forma v1.1 (tarjetas, rótulo, avisos por clave) | 2026-11-14 |
| Claude Code (Anthropic) | `src/web/src/secciones/rotaciones/Banda.tsx` | Componente que muestra un valor con su rango p10 a p90 | 2026-11-14 |
| Claude Code (Anthropic) | `src/web/src/secciones/rotaciones/Avisos.tsx` | Avisos del gemelo con el primero siempre visible | 2026-11-14 |
| Claude Code (Anthropic) | `src/web/src/secciones/rotaciones/ComparadorEstrategias.tsx` | Comparador de línea base y frente con indicadores en banda | 2026-11-14 |
| Claude Code (Anthropic) | `src/web/src/secciones/rotaciones/FrentePareto.tsx` | Frente de Pareto con selector de ejes y alternativa en texto | 2026-11-14 |
| Claude Code (Anthropic) | `src/web/src/secciones/rotaciones/Compromisos.tsx` | Compromisos del frente con los textos del gemelo | 2026-11-14 |
| Claude Code (Anthropic) | `src/web/src/secciones/rotaciones/rotaciones.css` | Estilos de la sección Rotaciones | 2026-11-14 |
| Claude Code (Anthropic) | `src/web/pruebas/rotaciones.test.ts` | Pruebas de bandas, ejemplo, tarjeta, avisos, Pareto y estado sin lote | 2026-11-14 |
| Claude Code (Anthropic) | `src/web/pruebas/rotaciones_bandera.test.ts` | Prueba de que el ejemplo del gemelo solo entra con VITE_EJEMPLOS=1 | 2026-11-14 |
| Claude Code (Anthropic) | `src/web/pruebas/e2e/rotaciones_seccion.spec.ts` | E2E de #/rotaciones con y sin lote y capturas de T-W2 | 2026-11-14 |
| Claude Code (Anthropic) | `src/web/src/secciones/fuentes/Fuentes.tsx` | Sección Fuentes: glosario por modo, créditos y declaración de SI generados | 2026-11-14 |
| Claude Code (Anthropic) | `src/web/pruebas/ruta.test.ts` | Pruebas de rutas por hash y navegación | 2026-11-14 |
| Claude Code (Anthropic) | `src/web/pruebas/frontera.test.ts` | Prueba de frontera entre Web y las carpetas de Daniel | 2026-11-14 |
| Claude Code (Anthropic) | `src/web/pruebas/bandera_ejemplos.test.ts` | Prueba de la bandera VITE_EJEMPLOS con compilación real | 2026-11-14 |
| Claude Code (Anthropic) | `src/web/pruebas/e2e/universo.spec.ts` | E2E de las siete rutas, teclado y globo montado | 2026-11-14 |
| Claude Code (Anthropic) | `src/web/src/secciones/gemelo/GemeloVista.tsx` | Vista del gemelo: cinco variables, ventanas de suelo desnudo y enlace (T-W6) | 2026-11-14 |
| Claude Code (Anthropic) | `src/web/src/secciones/gemelo/Grafico.tsx` | Gráfico SVG con banda y texto alternativo (T-W6) | 2026-11-14 |
| Claude Code (Anthropic) | `src/web/src/secciones/gemelo/tipos.ts` | Tipos locales de la v1 del contrato del gemelo (T-W6) | 2026-11-14 |
| Claude Code (Anthropic) | `src/web/src/secciones/gemelo/ejemplo.ts` | Trayectorias ficticias detrás de VITE_EJEMPLOS (T-W6) | 2026-11-14 |
| Claude Code (Anthropic) | `src/web/src/secciones/gemelo/gemelo.css` | Estilos de la sección El gemelo del lote (T-W6) | 2026-11-14 |
| Claude Code (Anthropic) | `src/web/src/secciones/ciencia/ciencia.css` | Estilos de la sección Ciencia y validación (T-W6) | 2026-11-14 |
| Claude Code (Anthropic) | `src/web/src/secciones/datos-abiertos/datos.css` | Estilos de la sección Datos abiertos (T-W6) | 2026-11-14 |
| Claude Code (Anthropic) | `src/web/pruebas/gemelo_seccion.test.ts` | Pruebas de la sección El gemelo del lote (T-W6) | 2026-11-14 |
| Claude Code (Anthropic) | `src/web/pruebas/ciencia_datos.test.ts` | Pruebas de las secciones Ciencia y Datos abiertos (T-W6) | 2026-11-14 |
| Claude Code (Anthropic) | `src/web/pruebas/e2e/secciones_w6.spec.ts` | E2E de las tres secciones de T-W6 con capturas | 2026-11-14 |
| Claude Code (Anthropic) | `src/web/src/app/Relleno.tsx` | Pinta textos con huecos de datos y el aviso de dato no disponible | 2026-11-14 |
| Claude Code (Anthropic) | `src/web/src/app/recorrido/pasos.ts` | Pasos del guion de tres actos escritos como datos | 2026-11-14 |
| Claude Code (Anthropic) | `src/web/src/app/recorrido/acciones.ts` | Ruta y acciones del globo de cada paso del recorrido | 2026-11-14 |
| Claude Code (Anthropic) | `src/web/src/app/recorrido/estado.ts` | Estado del recorrido guiado | 2026-11-14 |
| Claude Code (Anthropic) | `src/web/src/app/recorrido/Recorrido.tsx` | Panel del recorrido guiado con teclado y aria-live | 2026-11-14 |
| Claude Code (Anthropic) | `src/web/src/app/recorrido/recorrido.css` | Estilos del recorrido con movimiento reducido | 2026-11-14 |
| Claude Code (Anthropic) | `src/web/src/secciones/fuentes/tablas.ts` | Lectura en compilación de licencias, citas y uso de SI | 2026-11-14 |
| Claude Code (Anthropic) | `src/web/src/textos/huecos.ts` | Huecos de datos de los textos y su fuente | 2026-11-14 |
| Claude Code (Anthropic) | `src/web/pruebas/recorrido.test.ts` | Pruebas del recorrido, los huecos y la portada | 2026-11-14 |
| Claude Code (Anthropic) | `src/web/pruebas/fuentes.test.ts` | Pruebas de glosario, modos, créditos y declaración de SI | 2026-11-14 |
| Claude Code (Anthropic) | `src/web/pruebas/accesibilidad.test.ts` | Pruebas de movimiento reducido, foco y contraste | 2026-11-14 |
| Claude Code (Anthropic) | `src/web/pruebas/e2e/recorrido.spec.ts` | E2E de la portada, el recorrido completo con teclado y la sección Fuentes | 2026-11-14 |
| Claude Code (Anthropic) | `src/web/src/secciones/rotaciones/textosGemelo.ts` | Traducción de las claves de texto del gemelo v1.1 con formato %g de Python | 2026-11-14 |
| Claude Code (Anthropic) | `src/web/src/secciones/rotaciones/ejemplo_textos_gemelo.json` | Catálogo de textos del ejemplo SIMULADO del gemelo v1.1, solo bajo VITE_EJEMPLOS | 2026-11-14 |
| Claude Code (Anthropic) | `src/web/pruebas/rotaciones_lector.test.ts` | Pruebas de la lectura del paquete del gemelo con fetch falso | 2026-11-14 |
| Claude Code (Anthropic) | `src/web/pruebas/textos_gemelo.test.ts` | Pruebas del formato de las claves de texto del gemelo | 2026-11-14 |
| Claude Code (Anthropic) | `src/web/pruebas/textos_prohibidos.test.ts` | Prueba de textos prohibidos en los textos de Web y en una compilación | 2026-11-14 |
| Claude Code (Anthropic) | `src/web/pruebas/rutas_base_web.test.ts` | Prueba de que las fuentes tipográficas siguen a la base de la compilación | 2026-11-14 |
| Claude Code (Anthropic) | `src/web/src/secciones/datos-abiertos/manifiesto.ts` | Ficha y descargas de Datos abiertos leídas de datos/manifiesto.json (web_datos v0) | 2026-11-14 |
| Claude Code (Anthropic) | `src/web/pruebas/datos_abiertos_manifiesto.test.ts` | Pruebas de la ficha de Datos abiertos desde el manifiesto | 2026-11-14 |
| Claude Code (Anthropic) | `src/web/src/app/recorrido/cargarHuecos.ts` | Huecos del guion leídos de lotes_demo, meta, HLS y el paquete del gemelo | 2026-11-14 |
| Claude Code (Anthropic) | `src/web/pruebas/cargar_huecos.test.ts` | Pruebas de los huecos del guion con fetch falso | 2026-11-14 |
| Claude Code (Anthropic) | `src/web/pruebas/lotes_nombre.test.ts` | Prueba de que ningún texto de interfaz lleva escrito a mano el lugar de un lote de lotes_demo.json (D-036 f) | 2026-11-15 |
| Claude Code (Anthropic) | `src/web/src/secciones/fuentes/registros.ts` | Filtro de filas en uso de los registros de Fuentes | 2026-11-14 |
| Claude Code (Anthropic) | `src/web/src/secciones/fuentes/registrosPlugin.ts` | Plugin de Vite que filtra los registros al compilar | 2026-11-14 |
| Claude Code (Anthropic) | `src/web/src/secciones/rotaciones/AlertaHelada.tsx` | Alerta de helada del gemelo con sus avisos | 2026-11-14 |
| Claude Code (Anthropic) | `src/web/pruebas/registros.test.ts` | Pruebas del filtro de registros y del plugin | 2026-11-14 |
| Claude Code (Anthropic) | `src/web/pruebas/prohibidos.ts` | Detector de textos prohibidos compartido | 2026-11-14 |
| Claude Code (Anthropic) | `src/web/pruebas/alerta_helada.test.ts` | Pruebas de la alerta de helada | 2026-11-14 |
