
"""Connexion et persistance des données dans PostgreSQL / PostGIS."""

import os
from pathlib import Path

import psycopg
from dotenv import load_dotenv


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
