# Uso de SI

Registro exigido por las guías de Space Apps 2026 y AGENTS.md §5.3. Cada archivo de código asistido por SI lleva la cabecera `# asistido por SI: <herramienta y uso>` y una fila aquí.

| Herramienta | Archivo | Propósito | Fecha |
|-|-|-|-|
| Cursor (agente) | `pytest.ini` | Configuración del entorno y marcadores de pruebas | 2026-11-14 |
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

Notas de procedencia sin generación nueva por este equipo de Gemelo:
- `src/gemelo/referencias/enso.yaml` y `src/gemelo/referencias/sucesion.yaml` son copias literales de `origin/datos`.
- La idea científica, alcance, reglas de corte y decisiones (`D-001` a `D-030`) fueron definidas por el equipo humano y aprobadas por el director en `decisiones/registro.md`.
