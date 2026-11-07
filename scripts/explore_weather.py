
"""
SmartBreak - Open-Meteo API exploration

Purpose:
- Request hourly weather forecasts for Paris.
- Save the original JSON response in RAW.
- Inspect available variables, units, missing values and timestamps.
"""

from dbm import error
import json
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import pandas as pd
import requests
import sys


# ---------------------------------------------------------
# 1. Project configuration
# ---------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[1]

RAW_DIR = PROJECT_ROOT / "data" / "raw" / "weather"
RAW_DIR.mkdir(parents=True, exist_ok=True)

API_URL = "https://api.open-meteo.com/v1/forecast"

# Representative coordinates for central Paris
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


# ---------------------------------------------------------
# 2. API request
# ---------------------------------------------------------

def fetch_weather():
    """Retrieve hourly weather forecasts from Open-Meteo."""

    params = {
        "latitude": LATITUDE,
        "longitude": LONGITUDE,
        "hourly": ",".join(WEATHER_VARIABLES),
        "forecast_days": 2,
        "timezone": TIMEZONE,
        "temperature_unit": "celsius",
        "wind_speed_unit": "kmh",
        "precipitation_unit": "mm",
    }

    print("\nConnecting to Open-Meteo...")

    response = requests.get(
        API_URL,
        params=params,
        timeout=30
    )

    print("HTTP status:", response.status_code)

    response.raise_for_status()

    return response.json()


# ---------------------------------------------------------
# 3. Save original RAW response
# ---------------------------------------------------------

def save_raw_response(data):
    """Save the original API response without transformation."""

    retrieved_at = datetime.now(ZoneInfo(TIMEZONE))

    filename = (
    "sample_open_meteo_paris_"
    + retrieved_at.strftime("%Y%m%d_%H%M%S")
    + ".json"
    )

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

    with output_path.open("w", encoding="utf-8") as file:
        json.dump(
            raw_document,
            file,
            ensure_ascii=False,
            indent=2
        )

    print("\nRAW response saved:")
    print(output_path)

    return output_path


# ---------------------------------------------------------
# 4. Inspect API metadata
# ---------------------------------------------------------

def inspect_metadata(data):
    print("\n========== API METADATA ==========")

    print("Latitude returned:", data.get("latitude"))
    print("Longitude returned:", data.get("longitude"))
    print("Timezone:", data.get("timezone"))
    print("Timezone abbreviation:", data.get("timezone_abbreviation"))
    print("UTC offset (seconds):", data.get("utc_offset_seconds"))
    print("Elevation (m):", data.get("elevation"))

    print("\nHourly units:")

    for variable, unit in data.get("hourly_units", {}).items():
        print(f"- {variable}: {unit}")


# ---------------------------------------------------------
# 5. Convert hourly arrays into a DataFrame
# ---------------------------------------------------------

def inspect_hourly_data(data):
    print("\n========== HOURLY DATA ==========")

    hourly = data.get("hourly")

    if not hourly or "time" not in hourly:
        raise ValueError("The API response does not contain hourly data.")

    df = pd.DataFrame(hourly)

    if df.empty:
        raise ValueError("The hourly dataset is empty.")

    print("Dataset shape:", df.shape)
    print("Number of observations:", len(df))
    print("Number of columns:", len(df.columns))

    print("\nColumns:")
    print(df.columns.tolist())

    print("\nFirst 5 observations:")
    print(df.head().to_string(index=False))

    print("\nLast 5 observations:")
    print(df.tail().to_string(index=False))

    print("\nMissing values by column:")
    print(df.isna().sum().to_string())

    print("\nData types:")
    print(df.dtypes.to_string())

    print("\nTime range:")
    print("Start:", df["time"].min())
    print("End:", df["time"].max())

    # Check that the returned timestamps are hourly
    timestamps = pd.to_datetime(df["time"])
    differences = timestamps.diff().dropna()

    print("\nTimestamp interval check:")
    print(differences.value_counts().to_string())

    return df


# ---------------------------------------------------------
# 6. Main execution
# ---------------------------------------------------------

def main():
    try:
        data = fetch_weather()

        save_raw_response(data)

        inspect_metadata(data)

        df = inspect_hourly_data(data)

        print("\n========== EXPLORATION SUMMARY ==========")
        print("API exploration completed successfully.")
        print("Observations:", len(df))
        print("Variables:", len(df.columns) - 1)
        print("Total missing values:", int(df.isna().sum().sum()))

    except requests.RequestException as error:
        print("\nAPI request failed:")
        print(error)
        sys.exit(1)
    except (ValueError, KeyError, TypeError) as error:            
        print("\nData inspection failed:")
        print(error)
        sys.exit(1)


if __name__ == "__main__":
    main()
