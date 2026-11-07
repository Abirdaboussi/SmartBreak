"""Validation des espaces verts provenant de Paris Data."""

import json
import math
from datetime import datetime, timezone
from pathlib import Path

import yaml


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONTRACT = (
    PROJECT_ROOT / "config" / "contracts" / "green_spaces.yaml"
)


def load_green_spaces_contract(contract_path=DEFAULT_CONTRACT):
    """Charge le contrat YAML des espaces verts."""
    with open(contract_path, "r", encoding="utf-8") as file:
        return yaml.safe_load(file)


def is_missing(value):
    """Détecte une valeur absente."""
    return value is None or (
        isinstance(value, str) and not value.strip()
    )


def is_valid_number(value):
    """Vérifie qu'une valeur est un nombre fini."""
    return (
        not isinstance(value, bool)
        and isinstance(value, (int, float))
        and math.isfinite(value)
    )


def validate_position(position):
    """Vérifie une position GeoJSON [longitude, latitude]."""
    if not isinstance(position, list) or len(position) < 2:
        return False

    longitude, latitude = position[:2]

    if not is_valid_number(longitude):
        return False

    if not is_valid_number(latitude):
        return False

    return (
        -180 <= longitude <= 180
        and -90 <= latitude <= 90
    )


def validate_ring(ring):
    """Vérifie la structure et la fermeture d'un anneau."""
    if not isinstance(ring, list) or len(ring) < 4:
        return False

    if not all(validate_position(position) for position in ring):
        return False

    return ring[0][:2] == ring[-1][:2]


def validate_polygon_coordinates(coordinates):
    """Vérifie les anneaux d'un polygone."""
    if not isinstance(coordinates, list) or not coordinates:
        return False

    return all(validate_ring(ring) for ring in coordinates)


def validate_geometry(geometry):
    """Vérifie la structure d'une géométrie Polygon/MultiPolygon."""
    if not isinstance(geometry, dict):
        return False, "Géométrie absente ou invalide."

    geometry_type = geometry.get("type")
    coordinates = geometry.get("coordinates")

    if geometry_type == "Polygon":
        if not validate_polygon_coordinates(coordinates):
            return False, "Structure Polygon invalide."
        return True, None

    if geometry_type == "MultiPolygon":
        if not isinstance(coordinates, list) or not coordinates:
            return False, "Structure MultiPolygon invalide."

        for polygon in coordinates:
            if not validate_polygon_coordinates(polygon):
                return False, "Anneau MultiPolygon invalide."

        return True, None

    return False, f"Type de géométrie non autorisé : {geometry_type!r}"


def validate_green_spaces_data(raw_data, contract, detected_at=None):
    """
    Valide les features GeoJSON.

    Retourne les features acceptées, rejetées et un rapport qualité.
    """
    if detected_at is None:
        detected_at = datetime.now(timezone.utc).isoformat()

    structure = contract["contract"]["raw_structure"]

    if not isinstance(raw_data, dict):
        raise ValueError("Le RAW GeoJSON doit être un objet.")

    for key in structure["required_keys"]:
        if key not in raw_data:
            raise ValueError(f"Clé RAW obligatoire absente : {key}")

    if raw_data.get("type") != structure["root_type"]:
        raise ValueError("Le document doit être une FeatureCollection.")

    features = raw_data.get("features")

    if not isinstance(features, list) or not features:
        raise ValueError("Aucune feature GeoJSON à valider.")

    fields = contract["contract"]["fields"]
    identifier_field = fields["identifier"]
    name_field = fields["name"]
    allowed_geometry_types = set(fields["geometry_types"])

    rules = contract["contract"]["quality_rules"]
    rule_counts = {rule["id"]: 0 for rule in rules}

    row_errors = [[] for _ in features]
    identifiers = {}

    def add_error(index, rule_id, reason):
        row_errors[index].append({
            "rule_id": rule_id,
            "reason": reason,
            "detected_at": detected_at,
        })

    # Première passe : identifiants et doublons.
    for index, feature in enumerate(features):
        if not isinstance(feature, dict):
            add_error(index, "GQ01", "Feature GeoJSON invalide.")
            continue

        properties = feature.get("properties")

        if not isinstance(properties, dict):
            add_error(index, "GQ01", "Propriétés absentes ou invalides.")
            continue

        identifier = properties.get(identifier_field)

        if (
            isinstance(identifier, bool)
            or not isinstance(identifier, int)
        ):
            add_error(
                index,
                "GQ01",
                f"Identifiant absent ou non entier : {identifier!r}",
            )
        else:
            identifiers.setdefault(identifier, []).append(index)

    for identifier, indexes in identifiers.items():
        if len(indexes) > 1:
            for index in indexes:
                add_error(
                    index,
                    "GQ02",
                    f"Identifiant dupliqué : {identifier}",
                )

    # Deuxième passe : contrôles métier et géométriques.
    for index, feature in enumerate(features):
        if not isinstance(feature, dict):
            continue

        properties = feature.get("properties")

        if not isinstance(properties, dict):
            continue

        # GQ03 : nom obligatoire.
        name = properties.get(name_field)

        if is_missing(name):
            add_error(index, "GQ03", "Nom de l'espace vert absent.")

        # GQ04 : type de géométrie.
        geometry = feature.get("geometry")

        if not isinstance(geometry, dict):
            add_error(index, "GQ04", "Géométrie absente.")
            continue

        geometry_type = geometry.get("type")

        if geometry_type not in allowed_geometry_types:
            add_error(
                index,
                "GQ04",
                f"Type de géométrie non autorisé : {geometry_type!r}",
            )
            continue

        # GQ05 et GQ06 : coordonnées et structure.
        valid, reason = validate_geometry(geometry)

        if not valid:
            rule_id = (
                "GQ06"
                if reason and (
                    "Structure" in reason or "Anneau" in reason
                )
                else "GQ05"
            )
            add_error(index, rule_id, reason)

        # GQ07 : valeurs numériques positives ou nulles.
        for field_name in (
            "poly_area",
            "surface_totale_reelle",
            "surface_horticole",
            "perimeter",
        ):
            value = properties.get(field_name)

            if is_missing(value):
                continue

            if not is_valid_number(value) or value < 0:
                add_error(
                    index,
                    "GQ07",
                    f"{field_name} doit être un nombre positif ou nul : "
                    f"{value!r}",
                )

    accepted = []
    rejected = []

    for index, feature in enumerate(features):
        errors = row_errors[index]

        if errors:
            rejected_feature = dict(feature)
            rejected_feature["_source_index"] = index
            rejected_feature["_rejection_reasons"] = errors
            rejected.append(rejected_feature)

            for rule_id in {error["rule_id"] for error in errors}:
                rule_counts[rule_id] += 1
        else:
            accepted.append(feature)

    total = len(features)
    accepted_count = len(accepted)
    rejected_count = len(rejected)

    report = {
        "dataset": contract["contract"]["name"],
        "contract_version": contract["contract"]["version"],
        "detected_at": detected_at,
        "total_observations": total,
        "accepted_observations": accepted_count,
        "rejected_observations": rejected_count,
        "acceptance_rate": round(accepted_count / total * 100, 2),
        "rejection_rate": round(rejected_count / total * 100, 2),
        "rule_violations": rule_counts,
        "status": (
            "passed"
            if rejected_count == 0
            else "completed_with_rejections"
        ),
    }

    return {
        "accepted": accepted,
        "rejected": rejected,
        "report": report,
    }


def validate_green_spaces_file(
    raw_path,
    contract_path=DEFAULT_CONTRACT,
):
    """Charge le GeoJSON RAW et lance sa validation."""
    with open(raw_path, "r", encoding="utf-8") as file:
        raw_data = json.load(file)

    contract = load_green_spaces_contract(contract_path)

    return validate_green_spaces_data(raw_data, contract)
