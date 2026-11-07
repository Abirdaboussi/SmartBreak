
"""Transformation des observations météo validées vers le format curated."""

from datetime import datetime, timezone


WEATHER_FIELDS = [
    "temperature_2m",
    "apparent_temperature",
    "relative_humidity_2m",
    "precipitation",
    "precipitation_probability",
    "wind_speed_10m",
    "cloud_cover",
    "weather_code",
]


def parse_forecast_time(value):
    """Convertit un timestamp GMT en datetime ISO 8601 UTC."""
    try:
        parsed = datetime.strptime(value, "%Y-%m-%dT%H:%M")
    except (TypeError, ValueError) as error:
        raise ValueError(f"Timestamp invalide : {value}") from error

    return parsed.replace(tzinfo=timezone.utc).isoformat()


def normalize_retrieved_at(value):
    """Normalise la date de collecte en UTC."""
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (AttributeError, TypeError, ValueError) as error:
        raise ValueError(f"Date de collecte invalide : {value}") from error

    if parsed.tzinfo is None:
        raise ValueError("La date de collecte doit contenir un fuseau horaire.")

    return parsed.astimezone(timezone.utc).isoformat()


def transform_weather_data(accepted_observations, raw_data):
    """
    Transforme les observations acceptées vers le schéma curated.

    Args:
        accepted_observations: observations retournées par le validateur.
        raw_data: document RAW complet (metadata + response).

    Returns:
        Liste de dictionnaires prêts pour le stockage.
    """
    if not isinstance(raw_data, dict):
        raise ValueError("Le document RAW doit être un dictionnaire.")

    metadata = raw_data.get("metadata")
    response = raw_data.get("response")

    if not isinstance(metadata, dict) or not isinstance(response, dict):
        raise ValueError("Le document RAW doit contenir metadata et response.")

    if response.get("timezone") != "GMT":
        raise ValueError("Le fuseau horaire de la réponse doit être GMT.")

    if response.get("utc_offset_seconds") != 0:
        raise ValueError("Le décalage horaire attendu est de 0 seconde.")

    required_metadata = [
        "source",
        "source_url",
        "location",
        "retrieved_at",
    ]

    for field in required_metadata:
        if field not in metadata or metadata[field] is None:
            raise ValueError(f"Métadonnée obligatoire absente : {field}")

    required_response = ["latitude", "longitude", "elevation"]

    for field in required_response:
        if field not in response or response[field] is None:
            raise ValueError(f"Métadonnée API absente : {field}")

    retrieved_at = normalize_retrieved_at(metadata["retrieved_at"])

    curated_rows = []

    for observation in accepted_observations:
        row = {
            "forecast_time": parse_forecast_time(observation["time"]),
            "location": metadata["location"],
            "latitude": float(response["latitude"]),
            "longitude": float(response["longitude"]),
            "elevation_m": float(response["elevation"]),
            "source": metadata["source"],
            "source_url": metadata["source_url"],
            "retrieved_at": retrieved_at,
        }

        for field in WEATHER_FIELDS:
            if field not in observation or observation[field] is None:
                raise ValueError(
                    f"Champ météo absent de l'observation : {field}"
                )

            if field in ("relative_humidity_2m",
                         "precipitation_probability",
                         "cloud_cover",
                         "weather_code"):
                row[field] = int(observation[field])
            else:
                row[field] = float(observation[field])

        curated_rows.append(row)

    return curated_rows
