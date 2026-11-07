"""Point d'entrée unique du pipeline SmartBreak."""

import json
import logging
import time
from datetime import datetime, timezone
from pathlib import Path

# Modules météo
from src.collect import collect_weather
from src.validate import validate_raw_file
from src.transform import transform_weather_data
from src.persist import save_weather_outputs
from src.publish import (
    publish_weather_data,
    publish_green_spaces_data,
)
from src.db import initialize_database, get_connection

# Modules espaces verts
from src.collect_green_spaces import collect_green_spaces
from src.validate_green_spaces import validate_green_spaces_file
from src.transform_green_spaces import transform_green_spaces_file
from src.persist_green_spaces import save_green_spaces_outputs


PROJECT_ROOT = Path(__file__).resolve().parents[1]

LOG_DIR = PROJECT_ROOT / "logs"
REPORT_DIR = PROJECT_ROOT / "reports"

LOG_FILE = LOG_DIR / "pipeline.log"
REPORT_FILE = REPORT_DIR / "run_report.json"


def setup_logging():
    """Configure les logs du pipeline."""

    LOG_DIR.mkdir(parents=True, exist_ok=True)

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s",
        handlers=[
            logging.FileHandler(LOG_FILE, encoding="utf-8"),
            logging.StreamHandler(),
        ],
        force=True,
    )

    return logging.getLogger("smartbreak.pipeline")


def save_report(report):
    """Enregistre le rapport JSON de manière sécurisée."""

    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    temporary_file = REPORT_FILE.with_suffix(".json.tmp")

    with temporary_file.open("w", encoding="utf-8") as file:
        json.dump(
            report,
            file,
            ensure_ascii=False,
            indent=2,
            default=str,
        )

    temporary_file.replace(REPORT_FILE)


def run_pipeline():
    """Exécute les pipelines météo et espaces verts."""

    logger = setup_logging()

    started_at = datetime.now(timezone.utc)
    start_timer = time.perf_counter()

    report = {
        "project": "smartbreak",
        "datasets": ["weather_hourly", "paris_green_spaces"],
        "started_at": started_at.isoformat(),
        "status": "running",
        "steps": {},
    }

    try:
        # 1. INITIALISATION
        logger.info("Initialisation PostgreSQL/PostGIS")

        initialize_database()

        views_path = PROJECT_ROOT / "sql" / "views.sql"
        views_sql = views_path.read_text(encoding="utf-8")

        with get_connection() as conn:
            conn.execute(views_sql, prepare=False)

        logger.info("Schéma et vues SQL initialisés")

        report["steps"]["database"] = {
            "status": "success",
        }

        # =====================================================
        # 2. PIPELINE METEO
        # =====================================================

        logger.info("========== PIPELINE METEO ==========")

        # 2.1 COLLECT
        logger.info("Collecte météo")

        weather_collection = collect_weather()

        weather_raw_path = weather_collection["raw_path"]
        weather_raw_data = weather_collection["raw_data"]

        report["weather_run_id"] = weather_raw_path.stem
        report["steps"]["weather_collect"] = {
            "status": "success",
            "observations": weather_collection["observation_count"],
            "raw_file": str(
                weather_raw_path.relative_to(PROJECT_ROOT)
            ),
        }

        # 2.2 VALIDATE
        logger.info("Validation météo")

        weather_validation = validate_raw_file(
            weather_raw_path,
            PROJECT_ROOT / "config" / "contracts" / "weather.yaml",
        )

        weather_accepted = weather_validation["accepted"]
        weather_rejected = weather_validation["rejected"]
        weather_quality = weather_validation["report"]

        report["steps"]["weather_validate"] = {
            "status": weather_quality.get("status", "completed"),
            "total": weather_quality["total_observations"],
            "accepted": weather_quality["accepted_observations"],
            "rejected": weather_quality["rejected_observations"],
            "acceptance_rate": weather_quality["acceptance_rate"],
            "rejection_rate": weather_quality["rejection_rate"],
            "rule_violations": weather_quality["rule_violations"],
        }

        # 2.3 TRANSFORM
        logger.info("Transformation météo")

        weather_curated = transform_weather_data(
            weather_accepted,
            weather_raw_data,
        )

        report["steps"]["weather_transform"] = {
            "status": "success",
            "curated_count": len(weather_curated),
        }

        # 2.4 PERSIST
        logger.info("Sauvegarde météo")

        weather_persistence = save_weather_outputs(
            weather_curated,
            weather_rejected,
            weather_raw_path,
            weather_raw_data,
            output_root=PROJECT_ROOT / "data",
        )

        report["steps"]["weather_persist"] = {
            "status": "success",
            "curated_file": str(
                weather_persistence["curated_path"].relative_to(
                    PROJECT_ROOT
                )
            ),
            "rejected_file": str(
                weather_persistence["rejected_path"].relative_to(
                    PROJECT_ROOT
                )
            ),
            "curated_count": weather_persistence["curated_count"],
            "rejected_count": weather_persistence["rejected_count"],
        }

        # 2.5 PUBLISH
        logger.info("Publication météo dans PostgreSQL")

        weather_published = publish_weather_data(weather_curated)

        report["steps"]["weather_publish"] = {
            "status": "success",
            "published_count": weather_published,
        }

        logger.info(
            "Pipeline météo terminé : %s lignes publiées",
            weather_published,
        )

        # =====================================================
        # 3. PIPELINE ESPACES VERTS
        # =====================================================

        logger.info("========== PIPELINE ESPACES VERTS ==========")

        # 3.1 COLLECT
        logger.info("Collecte des espaces verts")

        green_collection = collect_green_spaces()

        green_raw_path = green_collection["raw_path"]

        report["green_spaces_run_id"] = green_raw_path.stem
        report["steps"]["green_spaces_collect"] = {
            "status": "success",
            "observations": green_collection["feature_count"],
            "raw_file": str(
                green_raw_path.relative_to(PROJECT_ROOT)
            ),
        }

        # 3.2 VALIDATE
        logger.info("Validation des espaces verts")

        green_validation = validate_green_spaces_file(
            green_raw_path,
            PROJECT_ROOT / "config" / "contracts" / "green_spaces.yaml",
        )

        green_quality = green_validation["report"]

        report["steps"]["green_spaces_validate"] = {
            "status": green_quality["status"],
            "total": green_quality["total_observations"],
            "accepted": green_quality["accepted_observations"],
            "rejected": green_quality["rejected_observations"],
            "acceptance_rate": green_quality["acceptance_rate"],
            "rejection_rate": green_quality["rejection_rate"],
            "rule_violations": green_quality["rule_violations"],
        }

        # 3.3 TRANSFORM
        logger.info("Transformation des espaces verts")

        green_curated = transform_green_spaces_file(
            green_validation,
            green_raw_path,
        )

        report["steps"]["green_spaces_transform"] = {
            "status": "success",
            "curated_count": len(green_curated),
        }

        # 3.4 PERSIST
        logger.info("Sauvegarde des espaces verts")

        green_persistence = save_green_spaces_outputs(
            green_raw_path,
            green_validation,
            green_curated,
        )

        report["steps"]["green_spaces_persist"] = {
            "status": "success",
            "curated_file": str(
                green_persistence["curated_path"].relative_to(
                    PROJECT_ROOT
                )
            ),
            "rejected_file": str(
                green_persistence["rejected_path"].relative_to(
                    PROJECT_ROOT
                )
            ),
            "report_file": str(
                green_persistence["report_path"].relative_to(
                    PROJECT_ROOT
                )
            ),
            "curated_count": green_persistence["curated_count"],
            "rejected_count": green_persistence["rejected_count"],
        }

        # 3.5 PUBLISH
        logger.info("Publication des espaces verts dans PostGIS")

        green_published = publish_green_spaces_data(green_curated)

        report["steps"]["green_spaces_publish"] = {
            "status": "success",
            "published_count": green_published,
        }

        logger.info(
            "Pipeline espaces verts terminé : %s lignes publiées",
            green_published,
        )

        report["status"] = "success"

        logger.info("Pipeline SmartBreak exécuté avec succès")

    except Exception as error:
        report["status"] = "failed"
        report["error"] = str(error)

        logger.exception("Échec du pipeline SmartBreak")

    finally:
        finished_at = datetime.now(timezone.utc)

        report["finished_at"] = finished_at.isoformat()
        report["duration_seconds"] = round(
            time.perf_counter() - start_timer,
            3,
        )

        save_report(report)

        logger.info("Rapport enregistré : %s", REPORT_FILE)

    return report


def main():
    """Point d'entrée en ligne de commande."""

    report = run_pipeline()

    print("\n========== SMARTBREAK PIPELINE ==========")
    print("Statut :", report["status"])
    print("Durée :", report["duration_seconds"], "secondes")
    print("Rapport :", REPORT_FILE)

    for step_name, step_result in report["steps"].items():
        print(f"{step_name} : {step_result.get('status')}")

    if report["status"] != "success":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
