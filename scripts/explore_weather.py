"""Profilage initial des données météo RAW de SmartBreak."""

import json
from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = PROJECT_ROOT / "data" / "raw" / "weather"
REPORT_DIR = PROJECT_ROOT / "reports"


def load_latest_raw():
    """Charge le dernier fichier RAW sans le modifier."""

    files = sorted(
        RAW_DIR.glob("*.json"),
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )

    if not files:
        raise FileNotFoundError("Aucun fichier RAW disponible.")

    raw_path = files[0]

    with raw_path.open("r", encoding="utf-8") as file:
        document = json.load(file)

    if not isinstance(document, dict):
        raise ValueError("Le document RAW doit être un objet JSON.")

    response = document.get("response", {})
    hourly = response.get("hourly")

    if not isinstance(hourly, dict) or "time" not in hourly:
        raise ValueError("Les données horaires sont absentes du RAW.")

    print("Fichier RAW utilisé :", raw_path.name)

    return document, raw_path


def profile_weather(document):
    """Calcule les statistiques descriptives du jeu de données."""

    df = pd.DataFrame(document["response"]["hourly"])

    if df.empty:
        raise ValueError("Le jeu de données est vide.")

    print("\n========== DIMENSIONS ==========")
    print("Nombre de lignes :", len(df))
    print("Nombre de colonnes :", len(df.columns))

    print("\n========== CHAMPS ET TYPES ==========")
    print(df.dtypes.to_string())

    print("\n========== VALEURS MANQUANTES ==========")

    missing = pd.DataFrame({
        "missing_count": df.isna().sum(),
        "missing_percentage": df.isna().mean() * 100,
    })

    print(missing.to_string())

    print("\n========== DOUBLONS ==========")

    duplicate_rows = int(df.duplicated().sum())
    duplicate_times = int(df["time"].duplicated().sum())

    print("Lignes entièrement dupliquées :", duplicate_rows)
    print("Horodatages dupliqués :", duplicate_times)

    print("\n========== STATISTIQUES NUMÉRIQUES ==========")

    numeric_columns = [
        column
        for column in df.select_dtypes(include="number").columns
        if column != "weather_code"
    ]

    numeric_stats = df[numeric_columns].describe().T

    print(numeric_stats.to_string())

    print("\n========== VARIABLES CATÉGORIELLES ==========")

    categorical_columns = [
        column
        for column in df.columns
        if column == "weather_code"
        or df[column].dtype == "object"
        and column != "time"
    ]

    categorical_stats = {}

    for column in categorical_columns:
        frequencies = (
            df[column]
            .value_counts(dropna=False)
            .head(10)
        )

        categorical_stats[column] = {
            str(value): int(count)
            for value, count in frequencies.items()
        }

        print(f"\n{column} - Top 10 :")
        print(frequencies.to_string())

    print("\n========== PLAGE TEMPORELLE ==========")

    timestamps = pd.to_datetime(df["time"], errors="coerce")

    print("Début :", timestamps.min())
    print("Fin :", timestamps.max())

    intervals = timestamps.diff().dropna().value_counts()

    print("\nFréquences des intervalles :")
    print(intervals.to_string())

    # Construction du rapport exportable.
    report = {
        "dataset": "weather_hourly",
        "source": document.get("metadata", {}).get("source"),
        "raw_retrieved_at": document.get("metadata", {}).get("retrieved_at"),
        "row_count": int(len(df)),
        "column_count": int(len(df.columns)),
        "columns": [
            {
                "name": column,
                "type": str(df[column].dtype),
            }
            for column in df.columns
        ],
        "missing_values": {
            column: {
                "count": int(df[column].isna().sum()),
                "percentage": float(df[column].isna().mean() * 100),
            }
            for column in df.columns
        },
        "duplicate_rows": duplicate_rows,
        "duplicate_timestamps": duplicate_times,
        "numeric_statistics": {
            column: {
                "min": float(df[column].min()),
                "max": float(df[column].max()),
                "mean": float(df[column].mean()),
                "median": float(df[column].median()),
            }
            for column in numeric_columns
        },
        "categorical_frequencies": categorical_stats,
        "time_range": {
            "start": str(timestamps.min()),
            "end": str(timestamps.max()),
        },
        "interval_frequencies": {
            str(interval): int(count)
            for interval, count in intervals.items()
        },
    }

    return report


def main():
    document, raw_path = load_latest_raw()
    report = profile_weather(document)

    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    report_path = REPORT_DIR / "weather_profile.json"

    with report_path.open("w", encoding="utf-8") as file:
        json.dump(
            report,
            file,
            ensure_ascii=False,
            indent=2,
        )

    print("\n========== PROFILING SUMMARY ==========")
    print("Observations :", report["row_count"])
    print("Variables :", report["column_count"])
    print("Valeurs manquantes :", sum(
        item["count"]
        for item in report["missing_values"].values()
    ))
    print("Lignes dupliquées :", report["duplicate_rows"])
    print("Horodatages dupliqués :", report["duplicate_timestamps"])
    print("\nRapport enregistré :", report_path)


if __name__ == "__main__":
    main()
