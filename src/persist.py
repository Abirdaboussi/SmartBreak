
"""Persistance des résultats CURATED et REJECTED au format JSON."""

import json
from pathlib import Path


def save_json(data, output_path):
    """Écrit un fichier JSON de manière sécurisée."""
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    temporary_path = output_path.with_suffix(
        output_path.suffix + ".tmp"
    )

    with temporary_path.open("w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=2)

    temporary_path.replace(output_path)


def save_weather_outputs(
    curated_rows,
    rejected_observations,
    raw_path,
    raw_data,
    output_root="data",
):
    """
    Sauvegarde les observations transformées et rejetées.

    Les noms des fichiers sont dérivés du fichier RAW source.
    Un rejeu du même RAW met donc à jour les mêmes fichiers.
    """
    raw_path = Path(raw_path)

    if not isinstance(raw_data, dict):
        raise ValueError("Le document RAW doit être un dictionnaire.")

    metadata = raw_data.get("metadata")

    if not isinstance(metadata, dict):
        raise ValueError("Les métadonnées RAW sont absentes.")

    retrieved_at = metadata.get("retrieved_at")

    if not retrieved_at:
        raise ValueError("La date de collecte est absente.")

    if not isinstance(curated_rows, list):
        raise ValueError("Les données curated doivent être une liste.")

    if not isinstance(rejected_observations, list):
        raise ValueError("Les données rejected doivent être une liste.")

    run_id = raw_path.stem

    curated_path = (
        Path(output_root)
        / "curated"
        / "weather"
        / f"{run_id}_curated.json"
    )

    rejected_path = (
        Path(output_root)
        / "rejected"
        / "weather"
        / f"{run_id}_rejected.json"
    )

    curated_document = {
        "dataset": "weather_hourly",
        "source_raw_file": raw_path.name,
        "retrieved_at": retrieved_at,
        "total_observations": len(curated_rows),
        "observations": curated_rows,
    }

    rejected_document = {
        "dataset": "weather_hourly",
        "source_raw_file": raw_path.name,
        "retrieved_at": retrieved_at,
        "total_observations": len(rejected_observations),
        "observations": rejected_observations,
    }

    save_json(curated_document, curated_path)
    save_json(rejected_document, rejected_path)

    return {
        "curated_path": curated_path,
        "rejected_path": rejected_path,
        "curated_count": len(curated_rows),
        "rejected_count": len(rejected_observations),
    }
