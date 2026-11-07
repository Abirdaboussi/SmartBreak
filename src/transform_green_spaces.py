"""Transformation des espaces verts acceptés en données CURATED."""

from datetime import datetime, timezone
from pathlib import Path
import json


def optional_number(value):
    """Convertit une valeur numérique facultative."""
    if value is None or value == "":
        return None

    try:
        number = float(value)
        return number if number >= 0 else None
    except (TypeError, ValueError):
        return None


def optional_integer(value):
    """Convertit une année ou un entier facultatif."""
    if value is None or value == "":
        return None

    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def transform_green_spaces_data(accepted_features, metadata):
    """
    Transforme les features GeoJSON acceptées en lignes CURATED.
    Les propriétés originales sont conservées dans raw_properties.
    """
    retrieved_at = metadata.get("retrieved_at")

    if not retrieved_at:
        raise ValueError("Métadonnée retrieved_at absente.")

    rows = []

    for feature in accepted_features:
        properties = feature["properties"]
        geometry = feature["geometry"]

        representative_point = properties.get("geom_x_y")

        if not isinstance(representative_point, dict):
            representative_point = None
        elif not (
            isinstance(representative_point.get("lon"), (int, float))
            and isinstance(representative_point.get("lat"), (int, float))
        ):
            representative_point = None
        else:
            longitude = representative_point["lon"]
            latitude = representative_point["lat"]

            if not (
                -180 <= longitude <= 180
                and -90 <= latitude <= 90
            ):
                representative_point = None

        row = {
            "source_id": properties["nsq_espace_vert"],
            "name": properties["nom_ev"].strip(),
            "type_ev": properties.get("type_ev"),
            "category": properties.get("categorie"),
            "address_number": optional_integer(
                properties.get("adresse_numero")
            ),
            "address_complement": properties.get("adresse_complement"),
            "address_street_type": properties.get("adresse_typevoie"),
            "address_street_name": properties.get("adresse_libellevoie"),
            "postal_code": properties.get("adresse_codepostal"),
            "polygon_area_m2": optional_number(
                properties.get("poly_area")
            ),
            "real_surface_m2": optional_number(
                properties.get("surface_totale_reelle")
            ),
            "horticultural_surface_m2": optional_number(
                properties.get("surface_horticole")
            ),
            "presence_fence": (
                str(properties["presence_cloture"])
                if properties.get("presence_cloture") is not None
                else None
            ),
            "perimeter_m": optional_number(
                properties.get("perimeter")
            ),
            "opening_year": optional_integer(
                properties.get("annee_ouverture")
            ),
            "renovation_year": optional_integer(
                properties.get("annee_renovation")
            ),
            "entity_count": optional_integer(
                properties.get("nb_entites")
            ),
            "open_24h": (
                str(properties["ouvert_ferme"])
                if properties.get("ouvert_ferme") is not None
                else None
            ),
            "geometry": geometry,
            "representative_point": representative_point,
            "source": metadata["source"],
            "source_url": metadata["source_url"],
            "retrieved_at": retrieved_at,
            "raw_properties": properties,
        }

        rows.append(row)

    return rows


def transform_green_spaces_file(validation_result, raw_path):
    """Transforme les données validées à partir du fichier RAW."""
    raw_path = Path(raw_path)

    metadata_path = raw_path.with_name(
        raw_path.stem + ".metadata.json"
    )

    if not metadata_path.exists():
        raise FileNotFoundError(
            f"Métadonnées introuvables : {metadata_path}"
        )

    with open(metadata_path, "r", encoding="utf-8") as file:
        metadata = json.load(file)

    return transform_green_spaces_data(
        validation_result["accepted"],
        metadata,
    )
