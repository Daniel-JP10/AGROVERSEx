-- asistido por SI: Claude Code (Anthropic), escritura y revisión de código; base del prototipo migrada en el hackatón
-- Esquema de INICIAR 8.3. Las tablas compartidas (fuente, variable, unidad, estatico, clase_fraccion,
-- metadatos) salen de geo/esquema_geo.sql, que crear_esquema() ejecuta antes que este archivo.
-- Mensual y lote_diario guardan enteros escalados (escala, desplazamiento y relleno en `variable`); NULL = hueco.
-- Los índices no van aquí: se crean al final (tarea 12).
CREATE TABLE mensual(
    unidad_id TEXT, mes_id INTEGER, -- mes_id = (anio-2000)*12 + mes-1, de 0 a 322
    precip INTEGER, precip_err INTEGER, precip_frac INTEGER, t2m INTEGER, t2m_p10 INTEGER, t2m_p90 INTEGER,
    t2m_max INTEGER, t2m_min INTEGER, rh2m INTEGER, rad_sw INTEGER, dias_helada INTEGER,
    et INTEGER, et_p10 INTEGER, et_p90 INTEGER, et_frac INTEGER,
    ndvi INTEGER, ndvi_p10 INTEGER, ndvi_p90 INTEGER, ndvi_frac INTEGER,
    lst_dia INTEGER, lst_err INTEGER, lst_frac INTEGER,
    sm_sup INTEGER, sm_raiz INTEGER, sm_err INTEGER, sm_frac INTEGER,
    sm_fuente INTEGER, -- 1 GLDAS, 2 SMAP L4, 3 SMAP L3
    sm_qual INTEGER, tws INTEGER, tws_err INTEGER, tws_frac INTEGER,
    dias_calor INTEGER, dias_extremo INTEGER, dias_suelo_expuesto INTEGER,
    suelo_metodo INTEGER, -- 1 solo NDVI, 2 NDVI+NBR2
    bandera_motivo INTEGER, -- bitmask: hueco de producto, nube, nieve, provisional, fuera de cobertura, calidad baja (B_CALIDAD_BAJA)
    PRIMARY KEY(unidad_id, mes_id)) WITHOUT ROWID;
CREATE TABLE anual(
    unidad_id TEXT, anio INTEGER, prod_tendencia, prod_estado, prod_desempeno, cobertura_igbp, cambio_cobertura,
    erosion_p05, erosion_p50, erosion_p95, soc_tier1, soc_metodo, clase_condicion, periodo,
    PRIMARY KEY(unidad_id, anio)) WITHOUT ROWID;
CREATE TABLE enso(mes_id INTEGER PRIMARY KEY, oni REAL, roni REAL); -- dato real NOAA CPC
CREATE TABLE evento(id TEXT PRIMARY KEY, tipo, inicio, fin, region_texto, magnitud_texto, url, etiqueta);
CREATE TABLE evento_unidad(evento_id TEXT, unidad_id TEXT, intensidad REAL);
CREATE TABLE sistema_rotacion(id TEXT PRIMARY KEY, region, habitual, alternativa_1, alternativa_2, fuente_id, etiqueta);
CREATE TABLE efecto_antecesor(pais, antecesor, cultivo, efecto2, eff_div, beta_lluvia, beta_t, significativo, fuente_id);
CREATE TABLE cultivo(
    id TEXT PRIMARY KEY, nombre, familia, kc_ini, kc_mid, kc_end, etapas, zr_min, zr_max, p, agua_min, agua_max,
    fija_n, ndfa_media, ndfa_de, analogo_de, fuente_id, etiqueta);
CREATE TABLE regla_sucesion(cultivo_o_familia, enfermedad, intervalo_min, intervalo_max, clima, fuente_id);
CREATE TABLE zona_demo(unidad_id TEXT, zona TEXT); -- unidades (ADM1 y sus ADM2) de cada zona DEMO
CREATE TABLE lote(id TEXT PRIMARY KEY, unidad_id TEXT, geom_wkt TEXT, cultivo_actual TEXT, zona_demo TEXT); -- sintético, sin persona asociada
CREATE TABLE lote_diario(
    lote_id TEXT, dia_id INTEGER, ndvi INTEGER, nbr2 INTEGER, sm_verdad INTEGER, sm_sensor INTEGER, nube INTEGER,
    PRIMARY KEY(lote_id, dia_id)) WITHOUT ROWID;
CREATE TABLE lote_ventana(lote_id TEXT, temporada, inicio, fin, error_semanas, detectada, confianza);
