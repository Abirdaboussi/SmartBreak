
import pytest

from src.transform import transform_weather_data


@pytest.fixture
def raw_data():
    return {
        "metadata": {
            "source": "Open-Meteo Forecast API",
            "source_url": "https://api.open-meteo.com/v1/forecast",
            "location": "Paris, France",
            "retrieved_at": "2026-11-07T15:32:58.790164+00:00",
        },
        "response": {
            "latitude": 48.853382,
            "longitude": 2.355208,
            "timezone": "GMT",
            "utc_offset_seconds": 0,
            "elevation": 36.0,
        },
    }


@pytest.fixture
def accepted_observations():
    return [
        {
            "time": "2026-11-07T00:00",
            "temperature_2m": 5.5,
            "apparent_temperature": 4.2,
            "relative_humidity_2m": 100,
            "precipitation": 0.0,
            "precipitation_probability": 0,
            "wind_speed_10m": 0.8,
            "cloud_cover": 100,
            "weather_code": 45,
        }
    ]


def test_transform_creates_curated_row(raw_data, accepted_observations):
    rows = transform_weather_data(accepted_observations, raw_data)

    assert len(rows) == 1
    assert rows[0]["location"] == "Paris, France"
    assert rows[0]["temperature_2m"] == 5.5
    assert rows[0]["weather_code"] == 45


def test_forecast_timestamp_is_explicitly_utc(
    raw_data, accepted_observations
):
    rows = transform_weather_data(accepted_observations, raw_data)

    assert rows[0]["forecast_time"] == "2026-11-07T00:00:00+00:00"


def test_retrieved_at_is_normalized_to_utc(
    raw_data, accepted_observations
):
    raw_data["metadata"]["retrieved_at"] = "2026-11-07T16:32:58+01:00"

    rows = transform_weather_data(accepted_observations, raw_data)

    assert rows[0]["retrieved_at"] == "2026-11-07T15:32:58+00:00"


def test_empty_accepted_observations_returns_empty_list(raw_data):
    rows = transform_weather_data([], raw_data)

    assert rows == []


def test_invalid_timezone_is_rejected(raw_data, accepted_observations):
    raw_data["response"]["timezone"] = "Europe/Paris"

    with pytest.raises(ValueError, match="GMT"):
        transform_weather_data(accepted_observations, raw_data)


def test_missing_weather_field_is_rejected(raw_data, accepted_observations):
    del accepted_observations[0]["temperature_2m"]

    with pytest.raises(ValueError, match="temperature_2m"):
        transform_weather_data(accepted_observations, raw_data)
