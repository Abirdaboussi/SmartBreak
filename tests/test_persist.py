
import json

from src.persist import save_weather_outputs


def test_save_weather_outputs_creates_both_files(tmp_path):
    raw_path = tmp_path / "sample_weather.json"

    raw_data = {
        "metadata": {
            "retrieved_at": "2026-11-07T15:32:58Z"
        }
    }

    curated = [{"temperature_2m": 12.5}]
    rejected = [
        {
            "_source_index": 2,
            "_rejection_reasons": [
                {"rule_id": "Q06", "reason": "Valeur invalide"}
            ],
        }
    ]

    result = save_weather_outputs(
        curated,
        rejected,
        raw_path,
        raw_data,
        output_root=tmp_path / "data",
    )

    assert result["curated_count"] == 1
    assert result["rejected_count"] == 1
    assert result["curated_path"].exists()
    assert result["rejected_path"].exists()


def test_saved_json_preserves_rejection_reasons(tmp_path):
    raw_path = tmp_path / "sample_weather.json"

    raw_data = {
        "metadata": {
            "retrieved_at": "2026-11-07T15:32:58Z"
        }
    }

    rejected = [
        {
            "_source_index": 3,
            "_rejection_reasons": [
                {"rule_id": "Q07", "reason": "Code météo invalide"}
            ],
        }
    ]

    result = save_weather_outputs(
        [],
        rejected,
        raw_path,
        raw_data,
        output_root=tmp_path / "data",
    )

    with result["rejected_path"].open(encoding="utf-8") as file:
        document = json.load(file)

    assert document["total_observations"] == 1
    assert document["observations"][0]["_source_index"] == 3
    assert (
        document["observations"][0]["_rejection_reasons"][0]["rule_id"]
        == "Q07"
    )


def test_replaying_same_raw_reuses_same_paths(tmp_path):
    raw_path = tmp_path / "sample_weather.json"

    raw_data = {
        "metadata": {
            "retrieved_at": "2026-11-07T15:32:58Z"
        }
    }

    first = save_weather_outputs(
        [{"temperature_2m": 12.5}],
        [],
        raw_path,
        raw_data,
        output_root=tmp_path / "data",
    )

    second = save_weather_outputs(
        [{"temperature_2m": 13.0}],
        [],
        raw_path,
        raw_data,
        output_root=tmp_path / "data",
    )

    assert first["curated_path"] == second["curated_path"]

    with second["curated_path"].open(encoding="utf-8") as file:
        document = json.load(file)

    assert document["observations"][0]["temperature_2m"] == 13.0
