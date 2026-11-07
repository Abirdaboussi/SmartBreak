
"""Connexion et persistance des données dans PostgreSQL / PostGIS."""

import os
from pathlib import Path

import psycopg
from dotenv import load_dotenv
import json
from psycopg.types.json import Jsonb


# Racine du projet, indépendamment du répertoire courant.
PROJECT_ROOT = Path(__file__).resolve().parents[1]

# Chargement explicite du fichier .env.
load_dotenv(dotenv_path=PROJECT_ROOT / ".env")


def get_connection():
    """Ouvre une connexion PostgreSQL à partir des variables du .env."""

    connection_params = {
        "host": os.getenv("POSTGRES_HOST"),
        "port": os.getenv("POSTGRES_PORT"),
        "dbname": os.getenv("POSTGRES_DB"),
        "user": os.getenv("POSTGRES_USER"),
        "password": os.getenv("POSTGRES_PASSWORD"),
    }

    missing = [
        key for key, value in connection_params.items()
        if not value
    ]

    if missing:
        raise ValueError(
            f"Variables PostgreSQL manquantes dans .env : {missing}"
        )

    return psycopg.connect(**connection_params)


def initialize_database(schema_path=None):
    """Exécute le schéma SQL pour initialiser la base de données."""

    if schema_path is None:
        schema_path = PROJECT_ROOT / "sql" / "schema.sql"

    schema_path = Path(schema_path)

    if not schema_path.is_absolute():
        schema_path = PROJECT_ROOT / schema_path

    if not schema_path.exists():
        raise FileNotFoundError(
            f"Fichier de schéma introuvable : {schema_path}"
        )

    schema_sql = schema_path.read_text(encoding="utf-8")

    with get_connection() as conn:
        conn.execute(schema_sql, prepare=False)


def upsert_weather_forecasts(rows):
    """
    Insère ou met à jour les prévisions météo.

    La combinaison location + forecast_time + retrieved_at
    identifie un snapshot de prévision.

    Retourne le nombre de lignes traitées.
    """

    if not isinstance(rows, list):
        raise ValueError("Les données météo doivent être une liste.")

    if not rows:
        return 0

    sql = """
        INSERT INTO weather_forecasts (
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
        )
        VALUES (
            %s, %s, %s, %s, %s, %s, %s, %s,
            %s, %s, %s, %s, %s, %s, %s, %s,
            ST_SetSRID(ST_MakePoint(%s, %s), 4326)
        )
        ON CONFLICT (
            location,
            forecast_time,
            retrieved_at
        )
        DO UPDATE SET
            latitude = EXCLUDED.latitude,
            longitude = EXCLUDED.longitude,
            elevation_m = EXCLUDED.elevation_m,
            source = EXCLUDED.source,
            source_url = EXCLUDED.source_url,
            temperature_2m = EXCLUDED.temperature_2m,
            apparent_temperature = EXCLUDED.apparent_temperature,
            relative_humidity_2m = EXCLUDED.relative_humidity_2m,
            precipitation = EXCLUDED.precipitation,
            precipitation_probability = EXCLUDED.precipitation_probability,
            wind_speed_10m = EXCLUDED.wind_speed_10m,
            cloud_cover = EXCLUDED.cloud_cover,
            weather_code = EXCLUDED.weather_code,
            geom = EXCLUDED.geom;
    """

    values = []

    for row in rows:
        values.append((
            row["location"],
            row["latitude"],
            row["longitude"],
            row["elevation_m"],
            row["source"],
            row["source_url"],
            row["retrieved_at"],
            row["forecast_time"],
            row["temperature_2m"],
            row["apparent_temperature"],
            row["relative_humidity_2m"],
            row["precipitation"],
            row["precipitation_probability"],
            row["wind_speed_10m"],
            row["cloud_cover"],
            row["weather_code"],
            row["longitude"],  # X = longitude
            row["latitude"],   # Y = latitude
        ))

    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.executemany(sql, values)

    return len(rows)


def upsert_green_spaces(rows):
    """
    Insère ou met à jour les espaces verts dans PostGIS.

    Vérifie d'abord la validité topologique des géométries.
    source_id garantit l'idempotence de la publication.
    """
    if not isinstance(rows, list):
        raise ValueError("Les espaces verts doivent être une liste.")

    if not rows:
        return 0

    # Vérification des géométries dans PostGIS avant publication.
    geometries_json = json.dumps(
        [{"geometry": row["geometry"]} for row in rows],
        ensure_ascii=False,
    )

    validation_sql = """
        SELECT
            item.ordinality,
            ST_IsValid(
                ST_SetSRID(
                    ST_GeomFromGeoJSON((item.value->'geometry')::text),
                    4326
                )
            ) AS is_valid
        FROM jsonb_array_elements(%s::jsonb)
        WITH ORDINALITY AS item(value, ordinality);
    """

    insert_sql = """
        INSERT INTO green_spaces (
            source_id,
            name,
            type_ev,
            category,
            address_number,
            address_complement,
            address_street_type,
            address_street_name,
            postal_code,
            polygon_area_m2,
            real_surface_m2,
            horticultural_surface_m2,
            presence_fence,
            perimeter_m,
            opening_year,
            renovation_year,
            entity_count,
            open_24h,
            geom,
            representative_point,
            source,
            source_url,
            retrieved_at,
            raw_properties
        )
        VALUES (
            %s, %s, %s, %s, %s, %s, %s, %s,
            %s, %s, %s, %s, %s, %s, %s, %s,
            %s, %s,
            ST_SetSRID(ST_GeomFromGeoJSON(%s), 4326),
            COALESCE(
                ST_SetSRID(ST_MakePoint(%s, %s), 4326),
                ST_PointOnSurface(
                    ST_SetSRID(ST_GeomFromGeoJSON(%s), 4326)
                )
            ),
            %s, %s, %s, %s
        )
        ON CONFLICT (source_id)
        DO UPDATE SET
            name = EXCLUDED.name,
            type_ev = EXCLUDED.type_ev,
            category = EXCLUDED.category,
            address_number = EXCLUDED.address_number,
            address_complement = EXCLUDED.address_complement,
            address_street_type = EXCLUDED.address_street_type,
            address_street_name = EXCLUDED.address_street_name,
            postal_code = EXCLUDED.postal_code,
            polygon_area_m2 = EXCLUDED.polygon_area_m2,
            real_surface_m2 = EXCLUDED.real_surface_m2,
            horticultural_surface_m2 = EXCLUDED.horticultural_surface_m2,
            presence_fence = EXCLUDED.presence_fence,
            perimeter_m = EXCLUDED.perimeter_m,
            opening_year = EXCLUDED.opening_year,
            renovation_year = EXCLUDED.renovation_year,
            entity_count = EXCLUDED.entity_count,
            open_24h = EXCLUDED.open_24h,
            geom = EXCLUDED.geom,
            representative_point = EXCLUDED.representative_point,
            source = EXCLUDED.source,
            source_url = EXCLUDED.source_url,
            retrieved_at = EXCLUDED.retrieved_at,
            raw_properties = EXCLUDED.raw_properties;
    """

    values = []

    for row in rows:
        geometry_json = json.dumps(
            row["geometry"],
            ensure_ascii=False,
        )

        point = row.get("representative_point") or {}

        values.append((
            row["source_id"],
            row["name"],
            row["type_ev"],
            row["category"],
            row["address_number"],
            row["address_complement"],
            row["address_street_type"],
            row["address_street_name"],
            row["postal_code"],
            row["polygon_area_m2"],
            row["real_surface_m2"],
            row["horticultural_surface_m2"],
            row["presence_fence"],
            row["perimeter_m"],
            row["opening_year"],
            row["renovation_year"],
            row["entity_count"],
            row["open_24h"],
            geometry_json,
            point.get("lon"),
            point.get("lat"),
            geometry_json,
            row["source"],
            row["source_url"],
            row["retrieved_at"],
            Jsonb(row["raw_properties"]),
        ))

    with get_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute(validation_sql, (geometries_json,))
            invalid_geometries = [
                index
                for index, is_valid in cursor.fetchall()
                if not is_valid
            ]

            if invalid_geometries:
                raise ValueError(
                    "Géométries PostGIS invalides aux positions : "
                    f"{invalid_geometries[:20]}"
                )

            cursor.executemany(insert_sql, values)

    return len(rows)