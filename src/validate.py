
"""Validation des données météo à partir du contrat YAML."""

import json
import math
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path

import yaml


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONTRACT = PROJECT_ROOT / "config" / "contracts" / "weather.yaml"


def load_contract(contract_path=DEFAULT_CONTRACT):
    """Charge le contrat de données YAML."""
    with open(contract_path, "r", encoding="utf-8") as file:
        return yaml.safe_load(file)


def parse_timestamp(value):
    """Convertit un timestamp au format attendu en datetime."""
    if not isinstance(value, str):
        return None

    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}", value):
        return None

    try:
        return datetime.strptime(value, "%Y-%m-%dT%H:%M")
    except ValueError:
        return None


def is_null(value):
    """Détecte les valeurs absentes ou NaN."""
    if value is None:
        return True

    if isinstance(value, float) and math.isnan(value):
        return True

    return False


def validate_raw_structure(raw_data, contract):
    """Vérifie les clés obligatoires définies dans le contrat RAW."""
    if not isinstance(raw_data, dict):
        raise ValueError("Le fichier RAW doit contenir un objet JSON.")

    structure = contract["contract"]["raw_structure"]

    for key in structure["root_keys"]:
        if key not in raw_data:
            raise ValueError(f"Structure RAW invalide : clé '{key}' absente.")

    metadata = raw_data["metadata"]
    response = raw_data["response"]

    if not isinstance(metadata, dict):
        raise ValueError("RAW invalide : metadata doit être un objet.")

    if not isinstance(response, dict):
        raise ValueError("RAW invalide : response doit être un objet.")

    for key in structure["metadata_fields"]:
        if key not in metadata:
            raise ValueError(f"RAW invalide : metadata.{key} absent.")

    for key in structure["response_fields"]:
        if key not in response:
            raise ValueError(f"RAW invalide : response.{key} absent.")

    if not isinstance(response["hourly"], dict):
        raise ValueError("RAW invalide : response.hourly doit être un objet.")

    if not isinstance(response["hourly_units"], dict):
        raise ValueError("RAW invalide : response.hourly_units doit être un objet.")


def extract_observations(hourly_data, fields):
    """Transforme les tableaux horaires de l'API en lignes."""
    lengths = [
        len(values)
        for values in hourly_data.values()
        if isinstance(values, list)
    ]

    if not lengths:
        return []

    number_of_rows = max(lengths)
    observations = []

    for index in range(number_of_rows):
        observation = {}

        for field in fields:
            field_name = field["name"]
            values = hourly_data.get(field_name)

            if isinstance(values, list) and index < len(values):
                observation[field_name] = values[index]
            else:
                observation[field_name] = None

        observations.append(observation)

    return observations


def validate_raw_data(raw_data, contract, detected_at=None):
    """
    Valide les données RAW.

    Retourne :
    - accepted : observations valides
    - rejected : observations invalides et leurs raisons
    - report : résumé de qualité
    """
    if detected_at is None:
        detected_at = datetime.now(timezone.utc).isoformat()

    validate_raw_structure(raw_data, contract)

    response = raw_data["response"]
    hourly_data = response["hourly"]

    contract_fields = contract["contract"]["fields"]
    quality_rules = contract["contract"]["quality_rules"]

    fields_by_name = {
        field["name"]: field for field in contract_fields
    }

    observations = extract_observations(hourly_data, contract_fields)

    # Un dataset vide n'est pas considéré comme valide.
    if not observations:
        raise ValueError("Dataset vide : aucune observation météo à valider.")

    accepted = []
    rejected = []

    rule_counts = {
        rule["id"]: 0 for rule in quality_rules
    }

    row_errors = [[] for _ in observations]

    def add_error(index, rule_id, reason):
        row_errors[index].append({
            "rule_id": rule_id,
            "reason": reason,
            "detected_at": detected_at,
        })

    # Q08 : vérification des unités au niveau du dataset.
    expected_units = {
        name: field["unit"]
        for name, field in fields_by_name.items()
    }

    actual_units = response["hourly_units"]

    unit_errors = []

    for field_name, expected_unit in expected_units.items():
        actual_unit = actual_units.get(field_name)

        if actual_unit != expected_unit:
            unit_errors.append(
                f"{field_name}: unité attendue '{expected_unit}', "
                f"unité reçue '{actual_unit}'"
            )

    if unit_errors:
        reason = "Unités API incompatibles : " + "; ".join(unit_errors)

        for index in range(len(observations)):
            add_error(index, "Q08", reason)

    # Q01, Q03, Q06 et Q07.
    parsed_timestamps = []

    for index, observation in enumerate(observations):

        # Q01 : champs obligatoires.
        for field in contract_fields:
            field_name = field["name"]

            if field.get("required", False):
                if is_null(observation.get(field_name)):
                    add_error(
                        index,
                        "Q01",
                        f"Champ obligatoire absent ou nul : {field_name}",
                    )

        # Q03 : format du timestamp.
        timestamp = observation.get("time")
        parsed_timestamp = parse_timestamp(timestamp)
        parsed_timestamps.append(parsed_timestamp)

        if parsed_timestamp is None:
            add_error(
                index,
                "Q03",
                f"Timestamp invalide : {timestamp!r}",
            )

        # Q06 : types et limites numériques.
        for field in contract_fields:
            field_name = field["name"]

            if field.get("type") not in ("integer", "float"):
                continue

            value = observation.get(field_name)

            if is_null(value):
                continue

            if isinstance(value, bool) or not isinstance(value, (int, float)):
                add_error(
                    index,
                    "Q06",
                    f"{field_name} doit être numérique : {value!r}",
                )
                continue

            if not math.isfinite(value):
                add_error(
                    index,
                    "Q06",
                    f"{field_name} doit être une valeur finie.",
                )
                continue

            if field["type"] == "integer" and not isinstance(value, int):
                add_error(
                    index,
                    "Q06",
                    f"{field_name} doit être un entier : {value!r}",
                )
                continue

            if "min" in field and value < field["min"]:
                add_error(
                    index,
                    "Q06",
                    f"{field_name} = {value} est inférieur au minimum "
                    f"{field['min']}.",
                )

            if "max" in field and value > field["max"]:
                add_error(
                    index,
                    "Q06",
                    f"{field_name} = {value} est supérieur au maximum "
                    f"{field['max']}.",
                )

        # Q07 : codes météo autorisés.
        weather_code = observation.get("weather_code")
        allowed_codes = fields_by_name["weather_code"].get(
            "allowed_values", []
        )

        if not is_null(weather_code):
            if (
                isinstance(weather_code, bool)
                or not isinstance(weather_code, int)
                or weather_code not in allowed_codes
            ):
                add_error(
                    index,
                    "Q07",
                    f"Code météo WMO invalide : {weather_code!r}",
                )

    # Q02 : unicité des timestamps.
    seen_timestamps = set()

    for index, timestamp in enumerate(parsed_timestamps):
        if timestamp is None:
            continue

        if timestamp in seen_timestamps:
            add_error(
                index,
                "Q02",
                f"Timestamp dupliqué : {timestamp.isoformat()}",
            )
        else:
            seen_timestamps.add(timestamp)

    # Q04 et Q05 : ordre chronologique et fréquence.
    previous_timestamp = None

    for index, timestamp in enumerate(parsed_timestamps):
        if timestamp is None:
            continue

        # Un doublon est déjà identifié par Q02.
        if timestamp in {
            parsed_timestamps[previous_index]
            for previous_index in range(index)
            if parsed_timestamps[previous_index] is not None
        }:
            continue

        if previous_timestamp is not None:
            if timestamp < previous_timestamp:
                add_error(
                    index,
                    "Q04",
                    "Observation non chronologique : timestamp antérieur "
                    "à l'observation précédente.",
                )

            elif timestamp - previous_timestamp != timedelta(hours=1):
                add_error(
                    index,
                    "Q05",
                    f"Intervalle incorrect : {timestamp - previous_timestamp} "
                    "au lieu de 1 heure.",
                )

        previous_timestamp = timestamp

    # Séparation des observations acceptées et rejetées.
    for index, observation in enumerate(observations):
        errors = row_errors[index]

        if errors:
            rejected_observation = dict(observation)
            rejected_observation["_source_index"] = index
            rejected_observation["_rejection_reasons"] = errors
            rejected.append(rejected_observation)

            # Chaque règle compte une seule fois par observation.
            affected_rules = {
                error["rule_id"] for error in errors
            }

            for rule_id in affected_rules:
                rule_counts[rule_id] += 1
        else:
            accepted.append(observation)

    total = len(observations)
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
            "passed" if rejected_count == 0
            else "completed_with_rejections"
        ),
    }

    return {
        "accepted": accepted,
        "rejected": rejected,
        "report": report,
    }


def validate_raw_file(raw_path, contract_path=DEFAULT_CONTRACT):
    """Charge un fichier RAW JSON et lance sa validation."""
    with open(raw_path, "r", encoding="utf-8") as file:
        raw_data = json.load(file)

    contract = load_contract(contract_path)

    return validate_raw_data(raw_data, contract)
