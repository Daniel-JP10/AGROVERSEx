# Contrato web_componentes · v1

Frontera entre la sección La Tierra desde el espacio, de Daniel, y el resto del universo AGROVERSEx, de Web. Lo firman Daniel y el compañero B.

- Estado: v1 FIRMADA. Firma registrada el 2026-11-14 a las 13:57 (UTC−5), con 57 minutos de retraso sobre el hito de Sáb 13:00 porque el PR de la app de Daniel llegó después de esa hora.
- Historia: v0 borrador del 2026-11-14 en la rama `web`; Daniel aprobó §1, §2, §3, §5, §8 y §9 y pidió los cambios que recoge esta v1.
- Manda sobre las rutas orientativas de `Docu/01_IDEA_AGROVERSEx.md` §5.5. Todo cambio se escribe a la vez aquí, en `decisiones/registro.md` y en la idea (`contratos/LEEME.md`). Desde la v1, solo cambios aditivos.

## 1. Dónde vive la app

La app es una sola y vive en `src/web/`, no en `web/` como dice la §5.5. No hay un segundo proyecto de frontend: el universo se arma reorganizando esta app.

## 2. Quién es dueño de qué

Las carpetas de Daniel se quedan donde están; la sección Tierra es solo su punto de entrada.

| Ruta en `src/web/` | Dueño | Nota |
|-|-|-|
| `server/` | Daniel | Solo para desarrollo local. La versión pública no usa API: lee archivos estáticos según `contratos/web_datos.md`, que sale de T-D7. Reemplazar `server/` es tarea de Daniel |
| `src/globo/`, `src/datos/`, `src/tiempo/`, `src/comparar/`, `src/herramientas/`, `src/graficos/` | Daniel | Sin cambios de ubicación |
| `src/paneles/` salvo `comparador/` | Daniel | Panel de unidad y sus pestañas |
| `src/secciones/tierra/` | Daniel | `Tierra.tsx` contiene lo que hoy compone `src/app/App.tsx`: globo, búsqueda, riel, capas, comparador, medir, panel y línea de tiempo |
| `src/secciones/tierra/interfaz.ts` | Daniel | Única puerta del globo hacia el resto, §4 |
| `src/comun/unidades.ts` | Daniel | Función única de conversión, §5 |
| `src/app/` (`App.tsx`, `Cabecera.tsx`, `tema.css`) | Web | Esqueleto: rutas, navegación, cabecera, tokens |
| `src/app/Riel.tsx`, `src/app/Fps.tsx` | Daniel | Son herramientas del globo; se mueven a `secciones/tierra/` |
| `src/textos/` | Web | Archivo único de traducción por clave, §6 |
| `src/secciones/portada/`, `gemelo/`, `rotaciones/`, `ciencia/`, `datos-abiertos/`, `fuentes/` | Web | Las otras seis secciones |
| `src/paneles/comparador/` | Web | Pasa completo a `src/secciones/rotaciones/`. Sus `fixtures` se ven SIMULADO. La pestaña Rotaciones del panel queda como resumen con enlace, §7 |
| `pruebas/` | Cada dueño las de sus rutas | |

Ninguno toca los archivos del otro sin pull request.

## 3. Rutas del universo

Rutas por hash, sin dependencia nueva. Funcionan en cualquier alojamiento estático sin reescrituras del servidor.

| Sección (§4.1 de la idea) | Ruta | Parámetros |
|-|-|-|
| Portada | `#/` | |
| La Tierra desde el espacio | `#/tierra` | `unidad`, `variable`, `mes` opcionales |
| El gemelo del lote | `#/gemelo` | `lote` |
| Rotaciones | `#/rotaciones` | `unidad`, `lote` |
| Ciencia y validación | `#/ciencia` | |
| Datos abiertos | `#/datos` | |
| Fuentes, glosario y créditos | `#/fuentes` | |

El recorrido guiado (T-W1) navega entre estas rutas y usa la interfaz del §4 para mover el globo.

## 4. Interfaz del globo

Web usa solo lo que exporta `src/secciones/tierra/interfaz.ts`. No importa nada de `globo/`, `paneles/` ni del almacén `app/estado.ts`. Toda la interfaz la implementa Daniel.

| Función | Qué hace | Nota |
|-|-|-|
| `irAUnidad(unidad_id)` | Selecciona la unidad y vuela a ella | `unidad_id` con el formato de `contratos/unidades.md` v0, por ejemplo `{iso3}-ADM2-{shapeID}`. La traducción a la clave interna es de Daniel |
| `cambiarVariable(id)` | Cambia la capa pintada | Ids de `datos/capas.ts` |
| `cambiarMes(mes)` | Cambia el mes mostrado | Recibe `AAAA-MM` en UTC |
| `activarComparador(activo)` | Abre o cierra el comparador A/B | Daniel lo expone en el almacén |
| `alSeleccionar(fn)` | Avisa cuando cambia la unidad seleccionada; devuelve la función para desuscribirse | |
| `abrirPestana(nombre)` | Abre una pestaña del panel de unidad | Daniel lo expone en el almacén |

## 5. Conversión de unidades

- Una sola función por magnitud, en `src/comun/unidades.ts`, de Daniel. Todo el universo la usa (docu §6.6).
- Los datos guardan la unidad del producto; la conversión es solo para mostrar (idea §5.2).
- Firma: `paraMostrar(variable, valor, unidadProducto, mes) => { valor, unidad }`, con `mes` obligatorio.
- Se quita el respaldo de 730,5 h por mes medio. `mmHoraAMmMes` de `datos/desescalar.ts`, `mmPorMes` de `datos/series.ts` y `valoresCapa` de `datos/capas.ts` pasan a usar `paraMostrar`.

## 6. Textos y traducción

- Un archivo de traducción por clave que mantiene Web en `src/textos/`. El globo lee sus textos por clave con `t(clave)` de `textos/i18n.ts`.
- Las claves salen del inglés (`en.ts`), porque la entrega va en inglés. Al español solo le pueden faltar claves si están marcadas.
- El agente de Daniel pasa a claves los textos de los archivos de Daniel y agrega esas claves a `en.ts` y `es.ts` en el mismo PR, que revisa Web.

## 7. Enlace del panel a Rotaciones

- Identificador de lote: `DEMO-{iso3}-{nn}`, por ejemplo `DEMO-USA-01`, `DEMO-COL-01` y `DEMO-COL-02`.
- La lista de lotes sale de un archivo estático `lotes_demo.json` con `lote_id`, `unidad_id` y `nombre`. `/api/rotaciones` desaparece.
- La pestaña Rotaciones del panel de unidad muestra un resumen corto. Si la unidad tiene lote DEMO, enlaza a `#/rotaciones?unidad=<unidad_id>&lote=<lote_id>`; si no, lo explica.
- La sección Rotaciones completa es de Web (T-W2) y lee al Gemelo según `contratos/gemelo_api.md`, que todavía no existe. Este contrato no fija la forma de esos datos.

## 8. Tokens de diseño

- Tema único oscuro de espacio negro, pedido del director (docu §6.5). La fuente de verdad son las variables de `src/app/tema.css`; aquí no se copian valores para que no se desincronicen.
- `tema.css` pasa a ser de Web. Si Daniel necesita un token nuevo, lo pide o abre PR.
- Tipografía: IBM Plex Sans, servida local desde `public/fuentes/`, licencia OFL (`public/fuentes/OFL.txt`).
- El contraste de texto se comprueba por cálculo en las pruebas (hoy `pruebas/riel.test.ts`).

## 9. Ejemplos y SIMULADO

- Todo valor que venga de un ejemplo o de datos simulados se ve SIMULADO en pantalla.
- Ningún ejemplo llega a la versión pública. Una bandera de compilación lo impide y una prueba que puede fallar lo comprueba (T-W0 paso 4). El nombre de la bandera se fija en T-W0.

## 10. Abierto

1. `contratos/gemelo_api.md` y su ejemplo, del compañero A.
2. `contratos/web_datos.md`, de T-D7, del que dependen §2, §7 y §11.

## 11. Secciones Ciencia y Datos abiertos

Las secciones Ciencia y validación y Datos abiertos leen los archivos que entrega Daniel según `contratos/web_datos.md`, todavía pendiente. Este contrato no fija su forma.

## Firmas

- Daniel Andres Jimenez Povea: firmado, 2026-11-14 13:57 (UTC−5)
- Compañero B, Web: firmado, 2026-11-14 13:57 (UTC−5)
