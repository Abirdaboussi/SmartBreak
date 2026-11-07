
"""Point d'entrée unique du pipeline SmartBreak."""

import json
import logging
import time
from datetime import datetime, timezone
from pathlib import Path

from src.collect import collect_weather
from src.validate import validate_raw_file
from src.transform import transform_weather_data
from src.persist import save_weather_outputs
from src.publish import publish_weather_data
from src.db import initialize_database, get_connection

PROJECT_ROOT = Path(__file__).resolve().parents[1]

LOG_DIR = PROJECT_ROOT / "logs"
REPORT_DIR = PROJECT_ROOT / "reports"

LOG_FILE = LOG_DIR / "pipeline.log"
REPORT_FILE = REPORT_DIR / "run_report.json"


def setup_logging():
    """Configure les logs dans logs/pipeline.log."""

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
    """Exécute toutes les étapes du pipeline météo."""

    logger = setup_logging()

    started_at = datetime.now(timezone.utc)
    start_timer = time.perf_counter()

    report = {
        "project": "smartbreak",
        "dataset": "weather_hourly",
        "started_at": started_at.isoformat(),
        "status": "running",
        "steps": {},
    }

    try:
        # Initialisation de la base et des vues SQL
        logger.info("Initialisation PostgreSQL/PostGIS")

        initialize_database()

        views_path = PROJECT_ROOT / "sql" / "views.sql"
        views_sql = views_path.read_text(encoding="utf-8")

        with get_connection() as conn:
            conn.execute(views_sql, prepare=False)

        logger.info("Schéma et vues SQL initialisés")

        # 1. COLLECT
        logger.info("Étape 1/5 - Collecte météo")

        collection = collect_weather()

        raw_path = collection["raw_path"]
        raw_data = collection["raw_data"]

        report["run_id"] = raw_path.stem
        report["raw_file"] = str(raw_path.relative_to(PROJECT_ROOT))
        report["steps"]["collect"] = {
            "status": "success",
            "observations": collection["observation_count"],
        }

        logger.info(
            "Collecte terminée : %s observations",
            collection["observation_count"],
        )

        # 2. VALIDATE
        logger.info("Étape 2/5 - Validation des données")

        validation = validate_raw_file(
            raw_path,
            PROJECT_ROOT / "config" / "contracts" / "weather.yaml",
        )

        accepted = validation["accepted"]
        rejected = validation["rejected"]
        quality_report = validation["report"]

        report["steps"]["validate"] = {
            "status": quality_report.get("status", "completed"),
            "total": quality_report["total_observations"],
            "accepted": quality_report["accepted_observations"],
            "rejected": quality_report["rejected_observations"],
            "acceptance_rate": quality_report["acceptance_rate"],
            "rejection_rate": quality_report["rejection_rate"],
            "rule_violations": quality_report["rule_violations"],
        }

        logger.info(
            "Validation terminée : %s acceptées, %s rejetées",
            len(accepted),
            len(rejected),
        )

        # 3. TRANSFORM
        logger.info("Étape 3/5 - Transformation")

        curated_rows = transform_weather_data(
            accepted,
            raw_data,
        )

        report["steps"]["transform"] = {
            "status": "success",
            "curated_count": len(curated_rows),
        }

        logger.info(
            "Transformation terminée : %s lignes CURATED",
            len(curated_rows),
        )

        # 4. PERSIST
        logger.info("Étape 4/5 - Persistance JSON")

        persistence = save_weather_outputs(
            curated_rows,
            rejected,
            raw_path,
            raw_data,
            output_root=PROJECT_ROOT / "data",
        )

        report["steps"]["persist"] = {
            "status": "success",
            "curated_file": str(
                persistence["curated_path"].relative_to(PROJECT_ROOT)
            ),
            "rejected_file": str(
                persistence["rejected_path"].relative_to(PROJECT_ROOT)
            ),
            "curated_count": persistence["curated_count"],
            "rejected_count": persistence["rejected_count"],
        }

        logger.info("Persistance JSON terminée")

        # 5. PUBLISH
        logger.info("Étape 5/5 - Publication PostgreSQL/PostGIS")

        published_count = publish_weather_data(curated_rows)

        report["steps"]["publish"] = {
            "status": "success",
            "published_count": published_count,
        }

        logger.info(
            "Publication terminée : %s lignes traitées",
            published_count,
        )

        report["status"] = "success"

        logger.info("Pipeline exécuté avec succès")

    except Exception as error:
        report["status"] = "failed"
        report["error"] = str(error)

        logger.exception("Échec du pipeline")

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

    if report["status"] != "success":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
