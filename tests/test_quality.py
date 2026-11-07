"""Tests automatisés du validateur de qualité météo."""

from copy import deepcopy

import pytest

from src.validate import load_contract, validate_raw_data


@pytest.fixture
def contract():
    return load_contract()



@pytest.fixture
def valid_raw_data():
    """Construit un fichier RAW conforme au contrat."""
    return {
        "metadata": {
            "source": "Open-Meteo Forecast API",
            "source_url": "https://api.open-meteo.com/v1/forecast",
            "location": "Paris, France",
            "latitude_requested": 48.8566,
            "longitude_requested": 2.3522,
            "retrieved_at": "2026-11-07T15:00:00+00:00",
            "timezone_requested": "GMT",
        },
        "response": {
            "latitude": 48.853382,
            "longitude": 2.355208,
            "timezone": "GMT",
            "timezone_abbreviation": "GMT",
            "utc_offset_seconds": 0,
            "elevation": 36.0,
            "hourly_units": {
                "time": "iso8601",
                "temperature_2m": "°C",
                "apparent_temperature": "°C",
                "relative_humidity_2m": "%",
                "precipitation": "mm",
                "precipitation_probability": "%",
                "wind_speed_10m": "km/h",
                "cloud_cover": "%",
                "weather_code": "wmo code",
            },
            "hourly": {
                "time": ["2026-11-07T00:00"],
                "temperature_2m": [12.5],
                "apparent_temperature": [11.8],
                "relative_humidity_2m": [75],
                "precipitation": [0.0],
                "precipitation_probability": [10],
                "wind_speed_10m": [8.0],
                "cloud_cover": [30],
                "weather_code": [2],
            },
        },
    }



def test_valid_observation_is_accepted(contract, valid_raw_data):
    result = validate_raw_data(valid_raw_data, contract)

    assert len(result["accepted"]) == 1
    assert len(result["rejected"]) == 0
    assert result["report"]["status"] == "passed"


def test_missing_required_field_is_rejected(contract, valid_raw_data):
    del valid_raw_data["response"]["hourly"]["temperature_2m"][0]

    result = validate_raw_data(valid_raw_data, contract)

    assert len(result["rejected"]) == 1
    assert any(
        error["rule_id"] == "Q01"
        for error in result["rejected"][0]["_rejection_reasons"]
    )


def test_invalid_timestamp_is_rejected(contract, valid_raw_data):
    valid_raw_data["response"]["hourly"]["time"][0] = "2026/11/07"

    result = validate_raw_data(valid_raw_data, contract)

    assert len(result["rejected"]) == 1
    assert "Q03" in [
        error["rule_id"]
        for error in result["rejected"][0]["_rejection_reasons"]
    ]


def test_duplicate_timestamp_is_rejected(contract, valid_raw_data):
    hourly = valid_raw_data["response"]["hourly"]

    for field_name, values in hourly.items():
        values.append(values[0])

    result = validate_raw_data(valid_raw_data, contract)

    assert len(result["rejected"]) == 1
    assert "Q02" in [
        error["rule_id"]
        for error in result["rejected"][0]["_rejection_reasons"]
    ]


def test_wrong_hourly_frequency_is_rejected(contract, valid_raw_data):
    hourly = valid_raw_data["response"]["hourly"]

    for field_name, values in hourly.items():
        values.append(values[0])

    hourly["time"][1] = "2026-11-07T02:00"

    result = validate_raw_data(valid_raw_data, contract)

    assert len(result["rejected"]) == 1
    assert "Q05" in [
        error["rule_id"]
        for error in result["rejected"][0]["_rejection_reasons"]
    ]


def test_out_of_range_temperature_is_rejected(contract, valid_raw_data):
    valid_raw_data["response"]["hourly"]["temperature_2m"][0] = 100

    result = validate_raw_data(valid_raw_data, contract)

    assert len(result["rejected"]) == 1
    assert "Q06" in [
        error["rule_id"]
        for error in result["rejected"][0]["_rejection_reasons"]
    ]


def test_invalid_weather_code_is_rejected(contract, valid_raw_data):
    valid_raw_data["response"]["hourly"]["weather_code"][0] = 999

    result = validate_raw_data(valid_raw_data, contract)

    assert len(result["rejected"]) == 1
    assert "Q07" in [
        error["rule_id"]
        for error in result["rejected"][0]["_rejection_reasons"]
    ]


def test_invalid_units_reject_observations(contract, valid_raw_data):
    valid_raw_data["response"]["hourly_units"]["temperature_2m"] = "F"

    result = validate_raw_data(valid_raw_data, contract)

    assert len(result["rejected"]) == 1
    assert "Q08" in [
        error["rule_id"]
        for error in result["rejected"][0]["_rejection_reasons"]
    ]


def test_multiple_errors_count_one_rejected_row(contract, valid_raw_data):
    hourly = valid_raw_data["response"]["hourly"]

    hourly["temperature_2m"][0] = 100
    hourly["weather_code"][0] = 999

    result = validate_raw_data(valid_raw_data, contract)

    assert len(result["rejected"]) == 1

    rule_ids = {
        error["rule_id"]
        for error in result["rejected"][0]["_rejection_reasons"]
    }

    assert "Q06" in rule_ids
    assert "Q07" in rule_ids
    assert result["report"]["rejected_observations"] == 1
    assert result["report"]["rule_violations"]["Q06"] == 1
    assert result["report"]["rule_violations"]["Q07"] == 1


def test_invalid_raw_structure_raises_error(contract):
    with pytest.raises(ValueError):
        validate_raw_data({}, contract)