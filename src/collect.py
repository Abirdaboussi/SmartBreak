
"""Collecte des prévisions météo depuis Open-Meteo."""

import json
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import requests


PROJECT_ROOT = Path(__file__).resolve().parents[1]

RAW_DIR = PROJECT_ROOT / "data" / "raw" / "weather"

API_URL = "https://api.open-meteo.com/v1/forecast"

LATITUDE = 48.8566
LONGITUDE = 2.3522
TIMEZONE = "GMT"

WEATHER_VARIABLES = [
    "temperature_2m",
    "apparent_temperature",
    "relative_humidity_2m",
    "precipitation",
    "precipitation_probability",
    "wind_speed_10m",
    "cloud_cover",
    "weather_code",
]


def fetch_weather():
    """Récupère les prévisions horaires depuis Open-Meteo."""

    params = {
        "latitude": LATITUDE,
        "longitude": LONGITUDE,
        "hourly": ",".join(WEATHER_VARIABLES),
        "forecast_days": 7,
        "timezone": TIMEZONE,
        "temperature_unit": "celsius",
        "wind_speed_unit": "kmh",
        "precipitation_unit": "mm",
    }

    response = requests.get(
        API_URL,
        params=params,
        timeout=30,
    )

    response.raise_for_status()

    data = response.json()

    if not isinstance(data, dict):
        raise ValueError("La réponse Open-Meteo doit être un objet JSON.")

    return data


def save_raw_response(data):
    """Enregistre la réponse originale avec ses métadonnées."""

    if not isinstance(data, dict):
        raise ValueError("Les données API doivent être un dictionnaire.")

    retrieved_at = datetime.now(ZoneInfo(TIMEZONE))

    filename = (
        "sample_open_meteo_paris_"
        + retrieved_at.strftime("%Y%m%d_%H%M%S")
        + ".json"
    )

    RAW_DIR.mkdir(parents=True, exist_ok=True)

    output_path = RAW_DIR / filename

    raw_document = {
        "metadata": {
            "source": "Open-Meteo Forecast API",
            "source_url": API_URL,
            "location": "Paris, France",
            "latitude_requested": LATITUDE,
            "longitude_requested": LONGITUDE,
            "retrieved_at": retrieved_at.isoformat(),
            "timezone_requested": TIMEZONE,
        },
        "response": data,
    }

    temporary_path = output_path.with_suffix(".json.tmp")

    with temporary_path.open("w", encoding="utf-8") as file:
        json.dump(
            raw_document,
            file,
            ensure_ascii=False,
            indent=2,
        )

    temporary_path.replace(output_path)

    return output_path, raw_document


def collect_weather():
    """Exécute la collecte et retourne le fichier RAW et son contenu."""

    data = fetch_weather()

    raw_path, raw_document = save_raw_response(data)

    return {
        "raw_path": raw_path,
        "raw_data": raw_document,
        "observation_count": len(data.get("hourly", {}).get("time", [])),
    }
