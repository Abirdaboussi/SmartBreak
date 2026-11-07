"""Collecte des espaces verts depuis Paris Data."""

import json
from datetime import datetime, timezone
from pathlib import Path

import requests


PROJECT_ROOT = Path(__file__).resolve().parents[1]

RAW_DIR = PROJECT_ROOT / "data" / "raw" / "green_spaces"

API_URL = (
    "https://opendata.paris.fr/api/explore/v2.1/"
    "catalog/datasets/espaces_verts/exports/geojson"
)


def save_raw_response(content, retrieved_at):
    """Sauvegarde le GeoJSON original et ses métadonnées."""

    RAW_DIR.mkdir(parents=True, exist_ok=True)

    timestamp = retrieved_at.strftime("%Y%m%d_%H%M%S")
    filename = f"sample_paris_green_spaces_{timestamp}"

    raw_path = RAW_DIR / f"{filename}.geojson"
    metadata_path = RAW_DIR / f"{filename}.metadata.json"

    # Sauvegarde des octets originaux sans modification.
    temporary_raw_path = raw_path.with_suffix(".geojson.tmp")
    temporary_raw_path.write_bytes(content)
    temporary_raw_path.replace(raw_path)

    metadata = {
        "source": "Paris Data - Espaces verts et assimilés",
        "source_url": API_URL,
        "dataset_id": "espaces_verts",
        "publisher": "Ville de Paris",
        "license": "ODbL",
        "retrieved_at": retrieved_at.isoformat(),
        "raw_file": raw_path.name,
        "format": "GeoJSON",
    }

    temporary_metadata_path = metadata_path.with_suffix(
        ".metadata.json.tmp"
    )

    with temporary_metadata_path.open("w", encoding="utf-8") as file:
        json.dump(metadata, file, ensure_ascii=False, indent=2)

    temporary_metadata_path.replace(metadata_path)

    return raw_path, metadata_path, metadata


def fetch_green_spaces():
    """Télécharge l'export GeoJSON des espaces verts parisiens."""

    retrieved_at = datetime.now(timezone.utc)

    response = requests.get(
        API_URL,
        timeout=60,
    )

    response.raise_for_status()

    # On sauvegarde la réponse originale avant son interprétation.
    raw_path, metadata_path, metadata = save_raw_response(
        response.content,
        retrieved_at,
    )

    try:
        data = json.loads(response.content)
    except (json.JSONDecodeError, UnicodeDecodeError) as error:
        raise ValueError(
            "La réponse Paris Data n'est pas un JSON valide. "
            f"Le fichier RAW a été conservé : {raw_path}"
        ) from error

    if not isinstance(data, dict):
        raise ValueError("La réponse GeoJSON doit être un objet JSON.")

    if data.get("type") != "FeatureCollection":
        raise ValueError(
            "La réponse GeoJSON doit être une FeatureCollection."
        )

    features = data.get("features")

    if not isinstance(features, list):
        raise ValueError(
            "Le champ features doit être une liste."
        )

    return {
        "raw_path": raw_path,
        "metadata_path": metadata_path,
        "metadata": metadata,
        "feature_count": len(features),
    }


def collect_green_spaces():
    """Exécute la collecte des espaces verts."""

    return fetch_green_spaces()


if __name__ == "__main__":
    result = collect_green_spaces()

    print("========== COLLECTE ESPACES VERTS ==========")
    print("Fichier RAW :", result["raw_path"])
    print("Métadonnées :", result["metadata_path"])
    print("Nombre d'espaces verts :", result["feature_count"])
