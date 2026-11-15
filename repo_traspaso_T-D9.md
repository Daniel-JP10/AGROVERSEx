# Ficha de traspaso entre agentes o personas

- **De:** Agente Constructor (Datos / Mapa, T-D9 y cierre de evidencia RED de PR #6)
- **Para:** Agente Verificador / Orquestador de Datos y Director (Daniel Andres Jimenez Povea)
- **Fecha y hora:** 2026-11-14 18:00 (UTC−5) / 2026-11-14T23:00:00Z
- **Tarea:**
  1. Demostración RED en copia de PR #6 (`C:\NASA\wt\empalme-imerg`, rama `datos-empalme-imerg`): probar que `pruebas/paneles_unidad.test.ts` falla específicamente por mostrar el valor crudo al revertir `paraMostrar` en `Resumen.tsx` y `Series.tsx`, y guardar la evidencia en `datos/evidencia/empalme_imerg_red_paneles.txt`.
  2. Cierre de T-D9 (Hito de las 21:00) y Parte C de T-D7 en `C:\NASA\wt\t-d9-mapa` (rama `datos-t-d9-mapa`): normalización a LF, integración de `origin/web-base-url` (`96e5322`), copia de `lotes_demo.json` a `src/web/public/datos/lotes_demo.json` (D-027), generación de `src/web/public/datos/manifiesto.json` con SHA-256 y meses disponibles, y publicación de `contratos/web_datos.md` v0.
- **Requisito del reto, pregunta de investigación y compuerta:**
  - Requisitos del reto: `N1`, `N2`, `N7`, `N8`, `F4`, `F5`, `F7`, `F12`, `F14` (parte de mapa), `F15`, `F17`; Idea 10.
  - Pregunta de investigación: ninguna directa en T-D9 (producto); prepara la base estática para mostrar `PI-D4` en T-D7.
  - Compuerta: `G6 Producto` (y `G3 Armonización` en la conservación de unidades físicas por mes en el empalme de IMERG Final a Late).
- **Qué se entrega: rutas exactas de archivos y commit**
  - En `C:\NASA\wt\empalme-imerg` (rama `datos-empalme-imerg`, commit `c61243e`):
    - `datos/evidencia/empalme_imerg_red_paneles.txt`
  - En `C:\NASA\wt\t-d9-mapa` (rama `datos-t-d9-mapa`, commits `7452b50` y `723df60` sobre `69509a4`):
    - `contratos/web_datos.md` (v0)
    - `src/mapa_estatico/__init__.py`
    - `src/mapa_estatico/construir.py`
    - `pruebas/mapa/test_construir.py`
    - `src/web/src/comun/rutas.ts`
    - `src/web/src/datos/estatico.ts`
    - `src/web/pruebas/estatico.test.ts`
    - `src/web/pruebas/rutas_base.test.ts` (integrado desde `origin/web-base-url` `96e5322`)
    - `src/web/src/globo/config.ts`, `src/web/src/globo/Globo.tsx`, `src/web/src/globo/coropleta.ts`, `src/web/src/globo/leyenda.tsx`, `src/web/src/globo/recoloreo.ts`
    - `src/web/src/paneles/Resumen.tsx`, `src/web/src/paneles/Series.tsx`, `src/web/src/paneles/Fuentes.tsx`, `src/web/src/paneles/Suelo.tsx`, `src/web/src/paneles/PanelRegion.tsx`, `src/web/src/paneles/Miga.tsx`, `src/web/src/paneles/filtros/Filtros.tsx`
    - `src/web/src/datos/capas.ts`, `src/web/src/datos/series.ts`, `src/web/src/datos/indice.ts` (eliminados `src/web/src/datos/cliente.ts` y `src/web/src/datos/consultas.ts`)
    - `src/web/src/comparar/Dividida.tsx`, `src/web/src/comparar/Escenario.tsx`, `src/web/src/secciones/tierra/interfaz.ts`, `src/web/src/tiempo/CintaEnso.tsx`, `src/web/src/tiempo/LineaTiempo.tsx`, `src/web/src/tiempo/huecos.ts`, `src/web/src/textos/es.ts`, `src/web/src/textos/en.ts`
    - `src/web/public/datos/COL/{precip,t2m,sm_raiz,ndvi}_{0,1,2}.json.gz`, `src/web/public/datos/unidades_geo.json.gz`, `src/web/public/datos/lotes_demo.json`, `src/web/public/datos/meta.json`, `src/web/public/datos/manifiesto.json`
    - `SI_USO.md`
- **Cómo reproducir: comando exacto**
  - Generación de archivos estáticos y manifiesto:
    ```powershell
    $env:PYTHONPATH="C:\NASA\wt\t-d9-mapa\src"
    C:\NASA\AGROVERSEx\.venv\Scripts\python.exe -m mapa_estatico.construir --series C:\NASA\AGROVERSEx\datos\procesados\series\COL --lotes C:\NASA\wt\t-d9-mapa\datos\lotes\lotes_demo.json --salida C:\NASA\wt\t-d9-mapa\src\web\public\datos --pais COL --generado-utc 2026-11-14T22:50:00Z
    ```
  - Pruebas Python (`pytest`):
    ```powershell
    $env:AGRO_DATOS="C:\NASA\AGROVERSEx\datos"
    $env:PYTHONPATH="C:\NASA\wt\t-d9-mapa\src"
    C:\NASA\AGROVERSEx\.venv\Scripts\pytest.exe C:\NASA\wt\t-d9-mapa\pruebas -m "not datos_reales" -q
    ```
  - Verificación de tipos y pruebas frontend (`tsc` y `vitest`):
    ```powershell
    cd C:\NASA\wt\t-d9-mapa\src\web
    npx tsc --noEmit
    npx vitest run
    ```
  - Comprobación de finales de línea LF:
    ```powershell
    git -C C:\NASA\wt\t-d9-mapa diff --stat 69509a4..HEAD
    git -C C:\NASA\wt\t-d9-mapa diff --stat --ignore-cr-at-eol 69509a4..HEAD
    ```
- **Qué se verificó ya y cómo:**
  - En `C:\NASA\wt\empalme-imerg`: al revertir temporalmente `paraMostrar` en `Resumen.tsx` y `Series.tsx`, `npx vitest run pruebas/paneles_unidad.test.ts` falla en 2 de 3 pruebas mostrando literalmente `<strong>123,46 <small></small></strong>` en `Resumen` y `"valor": [123.456]` en `Series`; al restaurar, pasa 3/3 en verde (`datos/evidencia/empalme_imerg_red_paneles.txt`, commit `c61243e`).
  - En `C:\NASA\wt\t-d9-mapa`:
    - `pytest pruebas/mapa/test_construir.py`: 7/7 en verde.
    - Suite completa `pytest -m "not datos_reales"`: 314 passed, 26 skipped, 0 failed.
    - `npx tsc --noEmit`: 0 errores.
    - `npx vitest run`: 31 archivos de prueba, 205/205 pruebas en verde (incluidas `pruebas/estatico.test.ts` con 19 pruebas sobre los datos reales de Colombia y `manifiesto.json`, y `pruebas/rutas_base.test.ts` con compilación real de Vite bajo `--base=/base-de-prueba/`).
    - `git diff --stat 69509a4..HEAD` y `git diff --stat --ignore-cr-at-eol 69509a4..HEAD` son idénticos (55 archivos, 1.282 inserciones, 354 borrados, 0 diferencias por CRLF).
- **Qué falta verificar:**
  - Revisión por un agente verificador con contexto limpio (según D-031) antes de fusionar a `datos` / `integracion`.
  - Incorporar la regla y capa de confianza de T-D7 Parte A (`PI-D4`) cuando cierre la corrida global de series.
- **Afirmaciones con su etiqueta:**
  - `VERIFICADO`: Los 15 archivos estáticos de `src/web/public/datos/` suman 13.028.092 bytes (13,03 MB) y sus hashes SHA-256 coinciden uno a uno con `src/web/public/datos/manifiesto.json` (`pruebas/estatico.test.ts`, `pruebas/mapa/test_construir.py`).
  - `VERIFICADO`: Las 4 variables reales de Colombia (`precip`, `sm_raiz`, `t2m`, `ndvi`) contienen 1 unidad en ADM0, 33 en ADM1 y 1.122 en ADM2, pintan más de 100 valores distintos en el mes inicial (`2024-06`) y no saltan en el empalme de IMERG Final (`mm/hr`) a Late (`mm/day`) en `2025-10` (`pruebas/estatico.test.ts`).
  - `VERIFICADO`: Al revertir la conversión en `Resumen.tsx` y `Series.tsx`, `paneles_unidad.test.ts` falla específicamente porque los paneles renderizan el valor crudo (`123,46` y `123.456`) en lugar del estado de error (`datos/evidencia/empalme_imerg_red_paneles.txt`).
  - `SUPUESTO`: Los rangos visuales de escala de la coropleta (`precip: [0, 500]`, `sm_raiz: [0, 900]`, `t2m: [-10, 35]`, `ndvi: [0, 1]`) en `src/web/src/datos/capas.ts` son supuestos visuales declarados; los valores fuera del rango se saturan en el extremo sin alterar el número mostrado en el panel.
- **Desfases conocidos:**
  - `serie_mensual_ndvi_area.csv.gz` lleva `"1"` en la columna `unidad`, que `pandas.read_csv` sin `dtype={"unidad": str}` leía como entero `1`; se corrigió en `src/mapa_estatico/construir.py` forzando `dtype={"version": str, "unidad": str}` y `str(f["unidad"])`, verificado en `test_construir.py` y `estatico.test.ts`.
  - El CSV de MERRA-2 traía `rean\ufffdlisis` con carácter de reemplazo `U+FFFD` (hallazgo de T-D2); `construir.py` lo corrige a `reanálisis` al exportar y rechaza cualquier otro `U+FFFD` sin corregir.
- **Criterio de aceptación: qué debe ser cierto para darlo por bueno**
  - `datos/evidencia/empalme_imerg_red_paneles.txt` versionado en `datos-empalme-imerg` demostrando el fallo por mostrar el valor crudo.
  - `contratos/web_datos.md` v0, `src/web/public/datos/lotes_demo.json` y `src/web/public/datos/manifiesto.json` publicados y verificados con `pytest` (314 passed) y `vitest` (205 passed), `origin/web-base-url` (`96e5322`) integrado y 100 % de los archivos en LF.
