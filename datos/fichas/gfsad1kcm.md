# Ficha de dataset

- Nombre corto: gfsad1kcm
- Producto oficial y versión: GFSAD1KCM versión 001, Global Food Security Support Analysis Data (GFSAD) Crop Mask 2010 Global 1 km V001 (NASA MEaSUREs). Colección CMR C2763261632-LPCLOUD. VERIFICADO (CMR, consulta del 2026-11-14)
- Agencia y centro de datos: NASA, LP DAAC (provider LPCLOUD)
- Página oficial: DOI https://doi.org/10.5067/MEaSUREs/GFSAD/GFSAD1KCM.001 (página no leída: PENDIENTE). Guía de usuario leída: https://lpdaac.usgs.gov/documents/172/GFSAD1K_User_Guide_V1.pdf
- Cita: Thenkabail, P. (2017). Global Food Security Support Analysis Data (GFSAD) Crop Mask 2010 Global 1 km V001 [Dataset]. NASA Land Processes Distributed Active Archive Center. Autor, fecha (2017-02-09) y editor de CMR `CollectionCitations`; lista completa de autores PENDIENTE. Licencia: política de uso de datos de Earthdata (LicenseURL de CMR), sin restricción marcada en CMR
- Variable y unidades: una banda uint8 de clases; sin `nodata` declarado. Leyenda de la guía de usuario (sección 2.2.4, VERIFICADO): 1 riego mayor, 2 riego menor, 3 secano, 4 secano con fragmentos menores, 5 secano con fragmentos muy menores, 9 sin cultivo. El valor 0 aparece en el archivo (547 millones de celdas, el océano) y no figura en la leyenda: se trata como no cultivo (INFERENCIA)
- Resolución espacial nominal: 1 km; celda real 0,008928197 grados (unos 993 m en el ecuador), 40457 columnas por 20188 filas
- CRS nativo: EPSG:4326, esquina superior izquierda (-180,2545, 90,2545). VERIFICADO (rasterio)
- Resolución temporal: un solo mapa, año nominal 2010 (datos de 2007 a 2012). Granulo único GFSAD1KCM.2010.001.2016348142550
- Archivo: 34.998.124 bytes, sha256 2203a3e37691cdcbe8afa8a8aa61db240cb5196a7b655dd87b1a3f10a323bd9c. Descarga: earthaccess.search_data(short_name='GFSAD1KCM', version='001') y enlace https://data.lpdaac.earthdatacloud.nasa.gov/lp-prod-protected/GFSAD1KCM.001/GFSAD1KCM.2010.001.2016348142550/GFSAD1KCM.2010.001.2016348142550.tif con la sesión de Earthdata (fecha 2026-11-14); copia en WSL `~/tmp/agroversex/t-d2/crudos/gfsad1kcm/`, fuera de git
- Conteo de clases (VERIFICADO): 0: 547.412.833; 1: 3.091.988; 2: 4.810.869; 3: 11.733.044; 4: 3.858.035; 5: 13.700.176; 9: 232.138.971
- Uso en T-D2: fracción de cultivo por celda gruesa = promedio por área (intersección exacta, exactextract) de un indicador 1/0 de las clases 1, 2 y 3. Sin remuestreo bilineal ni cúbico: la clase se cuenta, no se interpola. SUPUESTO: se excluyen las clases 4 y 5, que la guía describe con fracciones solo menores o muy menores de cultivo. La sensibilidad con las clases 1 a 5 no se corrió: PENDIENTE
- Candidato descartado: MCD12C1 061 (cobertura MODIS 0,05 grados, C2484078896-LPCLOUD). Existe pero llega solo en HDF4 de 1,2 GB, que este rasterio no abre, y no tiene DMR++ para OPeNDAP (404). Quedó sin usar; año 2024 descargado y borrado
- Limitaciones: mapa de 2010; mezcla cuatro estudios con definiciones distintas; no distingue cultivos y los fragmentos menores no se cuentan. Ninguna fracción de cultivo describe un lote
- Requisito del reto y pregunta que atiende: F8, N2; PI-D1. Compuerta G2
- Responsable: constructor de datos (subagente), orquestador de datos Daniel
- Verificador y fecha: PENDIENTE
