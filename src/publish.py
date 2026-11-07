
"""Publication des données CURATED dans PostgreSQL / PostGIS."""

from src.db import upsert_weather_forecasts, upsert_green_spaces


def publish_weather_data(curated_rows):
    """
    Publie les prévisions météo dans PostgreSQL.

    Args:
        curated_rows: liste des observations transformées.

    Returns:
        Nombre de lignes traitées.
    """

    if not isinstance(curated_rows, list):
        raise ValueError("Les données à publier doivent être une liste.")

    if not curated_rows:
        return 0

    published_count = upsert_weather_forecasts(curated_rows)

    return published_count


def publish_green_spaces_data(curated_rows):
    """Publie les espaces verts CURATED dans PostgreSQL/PostGIS."""

    if not isinstance(curated_rows, list):
        raise ValueError(
            "Les espaces verts à publier doivent être une liste."
        )

    if not curated_rows:
        return 0

    return upsert_green_spaces(curated_rows)