-- SmartBreak - Schéma PostgreSQL / PostGIS
-- Création idempotente des tables météo et espaces verts.

CREATE EXTENSION IF NOT EXISTS postgis;


-- =====================================================
-- 1. TABLE METEO
-- =====================================================

CREATE TABLE IF NOT EXISTS weather_forecasts (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    location TEXT NOT NULL,
    latitude DOUBLE PRECISION NOT NULL,
    longitude DOUBLE PRECISION NOT NULL,
    elevation_m DOUBLE PRECISION NOT NULL,

    source TEXT NOT NULL,
    source_url TEXT NOT NULL,

    retrieved_at TIMESTAMPTZ NOT NULL,
    forecast_time TIMESTAMPTZ NOT NULL,

    temperature_2m DOUBLE PRECISION NOT NULL,
    apparent_temperature DOUBLE PRECISION NOT NULL,
    relative_humidity_2m INTEGER NOT NULL,
    precipitation DOUBLE PRECISION NOT NULL,
    precipitation_probability INTEGER NOT NULL,
    wind_speed_10m DOUBLE PRECISION NOT NULL,
    cloud_cover INTEGER NOT NULL,
    weather_code INTEGER NOT NULL,

    geom geometry(Point, 4326) NOT NULL,

    CONSTRAINT uq_weather_forecast_snapshot
        UNIQUE (location, forecast_time, retrieved_at),

    CONSTRAINT ck_weather_latitude
        CHECK (latitude BETWEEN -90 AND 90),

    CONSTRAINT ck_weather_longitude
        CHECK (longitude BETWEEN -180 AND 180),

    CONSTRAINT ck_weather_humidity
        CHECK (relative_humidity_2m BETWEEN 0 AND 100),

    CONSTRAINT ck_weather_probability
        CHECK (precipitation_probability BETWEEN 0 AND 100),

    CONSTRAINT ck_weather_precipitation
        CHECK (precipitation >= 0),

    CONSTRAINT ck_weather_wind
        CHECK (wind_speed_10m >= 0),

    CONSTRAINT ck_weather_code
        CHECK (weather_code IN (
            0, 1, 2, 3, 45, 48, 51, 53, 55, 56, 57,
            61, 63, 65, 66, 67, 71, 73, 75, 77,
            80, 81, 82, 85, 86, 95, 96, 99
        ))
);

CREATE INDEX IF NOT EXISTS idx_weather_forecast_time
    ON weather_forecasts (forecast_time);

CREATE INDEX IF NOT EXISTS idx_weather_forecasts_location
    ON weather_forecasts (location);

CREATE INDEX IF NOT EXISTS idx_weather_forecasts_geom
    ON weather_forecasts USING GIST (geom);


-- =====================================================
-- 2. TABLE ESPACES VERTS
-- =====================================================

CREATE TABLE IF NOT EXISTS green_spaces (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    source_id BIGINT NOT NULL UNIQUE,

    name TEXT NOT NULL,
    type_ev TEXT,
    category TEXT,

    address_number INTEGER,
    address_complement TEXT,
    address_street_type TEXT,
    address_street_name TEXT,
    postal_code TEXT,

    polygon_area_m2 DOUBLE PRECISION,
    real_surface_m2 DOUBLE PRECISION,
    horticultural_surface_m2 DOUBLE PRECISION,

    presence_fence TEXT,
    perimeter_m DOUBLE PRECISION,

    opening_year INTEGER,
    renovation_year INTEGER,
    entity_count INTEGER,
    open_24h TEXT,

    geom geometry(Geometry, 4326) NOT NULL,

    representative_point geometry(Point, 4326),

    source TEXT NOT NULL,
    source_url TEXT NOT NULL,
    retrieved_at TIMESTAMPTZ NOT NULL,

    raw_properties JSONB NOT NULL,

    CONSTRAINT ck_green_spaces_geometry_type
        CHECK (
            ST_GeometryType(geom) IN (
                'ST_Polygon',
                'ST_MultiPolygon'
            )
        ),

    CONSTRAINT ck_green_spaces_geometry_valid
        CHECK (ST_IsValid(geom)),

    CONSTRAINT ck_green_spaces_area
        CHECK (
            polygon_area_m2 IS NULL
            OR polygon_area_m2 >= 0
        ),

    CONSTRAINT ck_green_spaces_perimeter
        CHECK (
            perimeter_m IS NULL
            OR perimeter_m >= 0
        )
);

CREATE INDEX IF NOT EXISTS idx_green_spaces_source_id
    ON green_spaces (source_id);

CREATE INDEX IF NOT EXISTS idx_green_spaces_type
    ON green_spaces (type_ev);

CREATE INDEX IF NOT EXISTS idx_green_spaces_category
    ON green_spaces (category);

CREATE INDEX IF NOT EXISTS idx_green_spaces_geom
    ON green_spaces USING GIST (geom);

CREATE INDEX IF NOT EXISTS idx_green_spaces_representative_point
    ON green_spaces USING GIST (representative_point);
