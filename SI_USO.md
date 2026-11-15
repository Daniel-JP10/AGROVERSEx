# Uso de SI

Registro exigido por las guías de Space Apps 2026 y AGENTS.md §5.3. Cada archivo de código asistido por SI lleva la cabecera `asistido por SI: <herramienta y uso>` y una fila aquí.

| Herramienta | Archivo | Propósito | Fecha |
|-|-|-|-|
| Claude Code (Anthropic) | `pruebas/geo/test_descargas.py` | Pruebas del backend del prototipo | 2026-11-14 |
| Claude Code (Anthropic) | `pruebas/geo/test_estaticos.py` | Pruebas del backend del prototipo | 2026-11-14 |
| Claude Code (Anthropic) | `pruebas/geo/test_estaticos_reales.py` | Pruebas del backend del prototipo | 2026-11-14 |
| Claude Code (Anthropic) | `pruebas/geo/test_indice_busqueda.py` | Pruebas del índice de búsqueda sobre unidades CGAZ (T-D1) | 2026-11-14 |
| Claude Code (Anthropic) | `pruebas/geo/test_normalizar.py` | Pruebas del backend del prototipo | 2026-11-14 |
| Claude Code (Anthropic) | `pruebas/geo/test_teselas.py` | Pruebas de teselas con unidad_id de CGAZ (T-D1) | 2026-11-14 |
| Claude Code (Anthropic) | `pruebas/geo/test_unidades.py` | Pruebas de unidades CGAZ: ids, padres, áreas, GPKG (T-D1) | 2026-11-14 |
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
| Claude Code (Anthropic) | `pytest.ini` | Configuración del entorno o de pruebas | 2026-11-14 |
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
| Claude Code (Anthropic) | `src/simulacion/geo/teselas.py` | Teselas y simplificación sobre unidad_id de CGAZ (T-D1) | 2026-11-14 |
| Claude Code (Anthropic) | `src/simulacion/geo/unidades.py` | Migración de límites GADM a CGAZ: lectura, ids, jerarquía, áreas y GPKG (T-D1) | 2026-11-14 |
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
| Claude Code (Anthropic) | `src/web/src/app/Fps.tsx` | Frontend del prototipo (base de la app) | 2026-11-14 |
| Claude Code (Anthropic) | `src/web/src/app/iconos.tsx` | Frontend del prototipo (base de la app) | 2026-11-14 |
| Claude Code (Anthropic) | `src/web/src/app/Riel.tsx` | Frontend del prototipo (base de la app) | 2026-11-14 |
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
| Claude Code (Anthropic) | `src/web/src/paneles/comparador/datos.ts` | Frontend del prototipo (base de la app) | 2026-11-14 |
| Claude Code (Anthropic) | `src/web/src/paneles/comparador/demo.html` | Frontend del prototipo (base de la app) | 2026-11-14 |
| Claude Code (Anthropic) | `src/web/src/paneles/comparador/demo.tsx` | Frontend del prototipo (base de la app) | 2026-11-14 |
| Claude Code (Anthropic) | `src/web/src/paneles/comparador/fixtures.ts` | Frontend del prototipo (base de la app) | 2026-11-14 |
| Claude Code (Anthropic) | `src/web/src/paneles/comparador/ordenar.ts` | Frontend del prototipo (base de la app) | 2026-11-14 |
| Claude Code (Anthropic) | `src/web/src/paneles/comparador/Prioridades.tsx` | Frontend del prototipo (base de la app) | 2026-11-14 |
| Claude Code (Anthropic) | `src/web/src/paneles/comparador/Rotaciones.tsx` | Frontend del prototipo (base de la app) | 2026-11-14 |
| Claude Code (Anthropic) | `src/web/src/paneles/comparador/TarjetaEstrategia.tsx` | Frontend del prototipo (base de la app) | 2026-11-14 |
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
| Claude Code (Anthropic) | `pruebas/geo/test_config_datos.py` | Prueba de la variable AGRO_DATOS (T-D1) | 2026-11-14 |
| Claude Code (Anthropic) | `pruebas/geo/test_cgaz_lectura.py` | Pruebas de lectura de CGAZ y verificación de hash (T-D1) | 2026-11-14 |
| Claude Code (Anthropic) | `pruebas/geo/test_colombia.py` | Pruebas de la comparación de Colombia con DIVIPOLA (T-D1) | 2026-11-14 |
| Claude Code (Anthropic) | `src/simulacion/geo/colombia.py` | Comparación de municipios de CGAZ con DIVIPOLA del DANE (T-D1) | 2026-11-14 |
| Claude Code (Anthropic) | `contratos/unidades.md` | Redacción del contrato de unidades a partir de los datos de CGAZ (T-D1) | 2026-11-14 |
| Claude Code (Anthropic) | `src/simulacion/geo/descargas_nasa.py` | Descarga con subconjunto por variable vía OPeNDAP de Earthdata (T-D3) | 2026-11-14 |
| Claude Code (Anthropic) | `pruebas/geo/test_descargas_nasa.py` | Pruebas de la descarga con subconjunto (T-D3) | 2026-11-14 |
| Claude Code (Anthropic) | `src/simulacion/geo/imerg_late.py` | Regla de días válidos de IMERG Late por celda (D-011) | 2026-11-14 |
| Claude Code (Anthropic) | `pruebas/geo/test_imerg_late.py` | Pruebas de la regla de IMERG Late | 2026-11-14 |
| Claude Code (Anthropic) | `src/simulacion/geo/sensibilidad_late.py` | Sensibilidad 70/80/90 de IMERG Late en Colombia | 2026-11-14 |
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
| Claude Code (Anthropic) | `src/lotes_demo/suelo.py` y `pruebas/lotes/test_lotes_suelo.py` | Parámetros de suelo desde SoilGrids REST (T-D5 B) | 2026-11-14 |
| Claude Code (Anthropic) | `src/lotes_demo/hls_validez.py` y `pruebas/lotes/test_hls_validez.py` | Fracción de observaciones HLS válidas por píxel y mes (T-D5 B) | 2026-11-14 |
| Claude Code (Anthropic) | `src/lotes_demo/construir_lotes.py`, `pruebas/lotes/test_lotes_demo.py`, `datos/lotes/lotes_demo.json` | Construcción de lotes_demo.json (T-D5 B) | 2026-11-14 |
| Claude Code (Anthropic) | `contratos/forzantes_gemelo.md` y fichas `datos/fichas/power_diario.md`, `hls_v2.md`, `imerg_diario.md` | Redacción del contrato y las fichas (T-D5 B) | 2026-11-14 |
| Claude Code (Anthropic) | `src/web/pruebas/sin_procedencia_china.test.ts`, `datos/evidencia/CPC-ASSESS97-AFRICA.yaml` | Prueba de procedencia en server y paneles; ficha de CPC que reemplaza a Cai 2025 (D-024) | 2026-11-14 |
| Claude Code (Anthropic) | `datos/evidencia/kluger_afiliaciones.md`, `datos/evidencia/koppen_beck2023_licencia.md` | Evidencia de afiliaciones de Kluger y de licencia de Köppen-Geiger (D-024) | 2026-11-14 |
