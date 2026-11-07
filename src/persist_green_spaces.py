"""Persistance des données CURATED et REJECTED des espaces verts."""

import json
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def save_json(data, output_path):
    """Sauvegarde JSON de manière atomique."""
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    temporary_path = output_path.with_name(
        output_path.name + ".tmp"
    )

    with temporary_path.open("w", encoding="utf-8") as file:
        json.dump(
            data,
            file,
            ensure_ascii=False,
            indent=2,
            allow_nan=False,
        )

    temporary_path.replace(output_path)
    return output_path


def save_green_spaces_outputs(
    raw_path,
    validation_result,
    curated_rows,
):
    """Sauvegarde les trois sorties du traitement."""
    raw_path = Path(raw_path)
    run_id = raw_path.stem

    curated_path = (
        PROJECT_ROOT
        / "data"
        / "curated"
        / "green_spaces"
        / f"{run_id}_curated.json"
    )

    rejected_path = (
        PROJECT_ROOT
        / "data"
        / "rejected"
        / "green_spaces"
        / f"{run_id}_rejected.json"
    )

    report_path = (
        PROJECT_ROOT
        / "reports"
        / "green_spaces"
        / f"{run_id}_quality_report.json"
    )

    curated_data = {
        "dataset": "paris_green_spaces",
        "raw_file": raw_path.name,
        "total": len(curated_rows),
        "data": curated_rows,
    }

    rejected_data = {
        "dataset": "paris_green_spaces",
        "raw_file": raw_path.name,
        "total": len(validation_result["rejected"]),
        "data": validation_result["rejected"],
    }

    save_json(curated_data, curated_path)
    save_json(rejected_data, rejected_path)
    save_json(validation_result["report"], report_path)

    return {
        "curated_path": curated_path,
        "rejected_path": rejected_path,
        "report_path": report_path,
        "curated_count": len(curated_rows),
        "rejected_count": len(validation_result["rejected"]),
    }
