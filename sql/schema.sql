
-- SmartBreak - Vues métier météo
-- Les dates de prévision sont stockées en UTC.

-- 1. Dernière version collectée de chaque prévision
CREATE OR REPLACE VIEW vw_weather_latest_forecasts AS
SELECT DISTINCT ON (location, forecast_time)
    id,
    location,
    latitude,
    longitude,
    elevation_m,
    source,
    source_url,
    retrieved_at,
    forecast_time,
    temperature_2m,
    apparent_temperature,
    relative_humidity_2m,
    precipitation,
    precipitation_probability,
    wind_speed_10m,
    cloud_cover,
    weather_code,
    geom
FROM weather_forecasts
ORDER BY
    location,
    forecast_time,
    retrieved_at DESC;


-- 2. Synthèse météo par journée locale à Paris
CREATE OR REPLACE VIEW vw_weather_daily_summary AS
SELECT
    location,
    (forecast_time AT TIME ZONE 'Europe/Paris')::date AS forecast_date,

    ROUND(AVG(temperature_2m)::numeric, 1)
        AS avg_temperature_c,

    ROUND(MIN(temperature_2m)::numeric, 1)
        AS min_temperature_c,

    ROUND(MAX(temperature_2m)::numeric, 1)
        AS max_temperature_c,

    ROUND(SUM(precipitation)::numeric, 2)
        AS total_precipitation_mm,

    ROUND(AVG(precipitation_probability)::numeric, 1)
        AS avg_precipitation_probability,

    ROUND(MAX(wind_speed_10m)::numeric, 1)
        AS max_wind_speed_kmh,

    ROUND(AVG(cloud_cover)::numeric, 1)
        AS avg_cloud_cover,

    COUNT(*) AS forecast_hours

FROM vw_weather_latest_forecasts
GROUP BY
    location,
    (forecast_time AT TIME ZONE 'Europe/Paris')::date;
