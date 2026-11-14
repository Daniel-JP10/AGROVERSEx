-- asistido por SI: Claude Code (Anthropic), escritura y revisión de código; base del prototipo migrada en el hackatón
-- Esquema de INICIAR 8.3. unidad lleva nombre_en; estatico lleva media (SoilGrids solo publica la media).
CREATE TABLE IF NOT EXISTS fuente(id TEXT PRIMARY KEY, cita TEXT, url TEXT, licencia TEXT, ficha_ev TEXT);
CREATE TABLE IF NOT EXISTS variable(
    id TEXT PRIMARY KEY, nombre TEXT, unidad_medida TEXT, escala REAL, desplazamiento REAL, relleno REAL,
    valido_min REAL, valido_max REAL, producto TEXT, version TEXT, doi TEXT, resolucion_nativa TEXT,
    crs_nativo TEXT, inicio TEXT, fin TEXT,
    nivel_dato TEXT, -- observado|modelo|reanalisis|indice|real_contexto
    etiqueta TEXT, fuente_id TEXT);
CREATE TABLE IF NOT EXISTS unidad(
    id TEXT PRIMARY KEY, -- código GID de GADM, o gb:<shapeID> de gbOpen donde se use como relleno
    nivel INTEGER, -- 0 pais, 1 primer nivel, 2 segundo nivel, 9 zona en disputa
    iso3 TEXT, padre_id TEXT, nombre TEXT, nombre_ascii TEXT, nombre_es TEXT, nombre_en TEXT,
    area_km2 REAL, punto_lat REAL, punto_lon REAL, fuente_limite TEXT, licencia_limite TEXT,
    cruce_ambiguo INTEGER,
    bbox_oeste REAL, bbox_sur REAL, bbox_este REAL, bbox_norte REAL); -- EPSG:4326; si cruza el antimeridiano da -180..180
CREATE TABLE IF NOT EXISTS estatico(
    unidad_id TEXT, variable_id TEXT, q05 REAL, q50 REAL, q95 REAL, media REAL, fraccion_valida REAL,
    PRIMARY KEY(unidad_id, variable_id));
CREATE TABLE IF NOT EXISTS clase_fraccion(
    unidad_id TEXT, esquema TEXT, -- koppen, igbp, wrb, ecoregion
    clase TEXT, fraccion REAL);
CREATE TABLE IF NOT EXISTS metadatos(clave TEXT PRIMARY KEY, valor TEXT); -- semilla, versiones, sha256, fecha de generación
