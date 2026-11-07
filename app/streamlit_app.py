"""Application Streamlit SmartBreak - Tableau de bord général."""

import sys
from pathlib import Path

import pandas as pd
import streamlit as st

# Permet d'importer les modules du projet depuis app/
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.db import get_connection


# --------------------------------------------------
# CONFIGURATION
# --------------------------------------------------

st.set_page_config(
    page_title="SmartBreak | Dashboard",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
        /* Fond principal */
        .stApp,
        [data-testid="stAppViewContainer"] {
            background-color: #F8F7FA;
            color: #29232D;
        }

        /* Texte g?n?ral */
        html, body, [class*="css"], p, label, span,
        div[data-testid="stMarkdownContainer"] {
            color: #29232D;
        }

        /* Titres */
        h1, h2, h3, h4 {
            color: #735973 !important;
        }

        /* Barre lat?rale */
        [data-testid="stSidebar"] {
            background-color: #F0EAF4;
        }

        [data-testid="stSidebar"] * {
            color: #382D3D !important;
        }

        /* Indicateurs KPI */
        [data-testid="stMetric"] {
            background-color: #FFFFFF;
            border: 1px solid #E8DFEA;
            padding: 18px;
            border-radius: 12px;
        }

        [data-testid="stMetricLabel"] {
            color: #5C5260 !important;
        }

        [data-testid="stMetricValue"] {
            color: #A3448A !important;
        }

        /* Tableaux */
        [data-testid="stDataFrame"] {
            background-color: #FFFFFF;
        }

        /* Boutons */
        .stButton button {
            background-color: #A3448A;
            color: #FFFFFF !important;
            border: none;
            border-radius: 8px;
        }

        .stButton button:hover {
            background-color: #85366F;
            border: none;
        }

        /* Messages */
        [data-testid="stAlert"] p {
            color: #29232D !important;
        }
    </style>
    """,
    unsafe_allow_html=True,
)


# --------------------------------------------------
# ACCES AUX DONNEES
# --------------------------------------------------

@st.cache_data(ttl=300)
def load_dashboard_data():
    """Charge les indicateurs et les données depuis PostgreSQL."""

    with get_connection() as conn:
        with conn.cursor() as cur:

            cur.execute("""
                SELECT
                    (SELECT COUNT(*) FROM weather_forecasts),
                    (SELECT COUNT(*) FROM vw_weather_latest_forecasts),
                    (SELECT COUNT(*) FROM vw_weather_daily_summary),
                    (SELECT COUNT(*) FROM green_spaces)
            """)

            counts = cur.fetchone()

            cur.execute("""
                SELECT
                    forecast_time,
                    temperature_2m,
                    apparent_temperature,
                    precipitation,
                    precipitation_probability,
                    wind_speed_10m,
                    relative_humidity_2m,
                    weather_code
                FROM vw_weather_latest_forecasts
                ORDER BY forecast_time
            """)

            weather_columns = [
                column.name for column in cur.description
            ]
            weather = pd.DataFrame(
                cur.fetchall(),
                columns=weather_columns,
            )

            cur.execute("""
                SELECT *
                FROM vw_weather_daily_summary
                ORDER BY forecast_date
            """)

            daily_columns = [
                column.name for column in cur.description
            ]
            daily = pd.DataFrame(
                cur.fetchall(),
                columns=daily_columns,
            )

            cur.execute("""
                SELECT
                    COALESCE(type_ev, 'Non renseigné') AS type_ev,
                    COUNT(*) AS total
                FROM green_spaces
                GROUP BY type_ev
                ORDER BY total DESC
                LIMIT 10
            """)

            category_columns = [
                column.name for column in cur.description
            ]
            categories = pd.DataFrame(
                cur.fetchall(),
                columns=category_columns,
            )

    return counts, weather, daily, categories


# --------------------------------------------------
# SIDEBAR
# --------------------------------------------------

with st.sidebar:
    st.title("🌿 SmartBreak")
    st.caption("Intelligent Outdoor Break Assistant")
    st.divider()

    st.markdown("### Navigation")
    st.markdown("**Vue générale**")
    st.markdown("Météo · À venir")
    st.markdown("Espaces verts · À venir")
    st.markdown("Qualité des données · À venir")

    st.divider()

    if st.button("🔄 Actualiser les données", width="stretch"):
        st.cache_data.clear()
        st.rerun()

    st.caption("Sources : Open-Meteo et Paris Data")


# --------------------------------------------------
# PAGE PRINCIPALE
# --------------------------------------------------

st.title("🌿 SmartBreak")
st.subheader("Tableau de bord général")

st.markdown(
    """
    Bienvenue sur SmartBreak !

    Consultez les données météorologiques de Paris et les espaces
    verts disponibles dans notre base de données.
    """
)

try:
    counts, weather, daily, categories = load_dashboard_data()

except Exception as error:
    st.error("Impossible de charger les données depuis PostgreSQL.")
    st.exception(error)
    st.stop()


# --------------------------------------------------
# KPI
# --------------------------------------------------

st.markdown("### Indicateurs clés")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Snapshots météo", f"{counts[0]:,}".replace(",", " "))

with col2:
    st.metric("Prévisions horaires", f"{counts[1]:,}".replace(",", " "))

with col3:
    st.metric("Jours synthétisés", f"{counts[2]:,}".replace(",", " "))

with col4:
    st.metric("Espaces verts", f"{counts[3]:,}".replace(",", " "))


st.divider()


# --------------------------------------------------
# APERCU METEOROLOGIQUE
# --------------------------------------------------

st.markdown("### 🌤️ Aperçu météorologique")

if not weather.empty:

    weather["forecast_time"] = pd.to_datetime(
        weather["forecast_time"],
        utc=True,
    )

    col1, col2 = st.columns([2, 1])

    with col1:
        st.markdown("**Évolution des températures**")

        temperature_chart = weather.set_index("forecast_time")[
            ["temperature_2m", "apparent_temperature"]
        ]

        st.line_chart(temperature_chart)

    with col2:
        st.markdown("**Prochaine prévision disponible**")

        next_forecast = weather.iloc[0]

        st.metric(
            "Température",
            f"{next_forecast['temperature_2m']:.1f} °C",
        )

        st.metric(
            "Ressenti",
            f"{next_forecast['apparent_temperature']:.1f} °C",
        )

        st.metric(
            "Probabilité de pluie",
            f"{next_forecast['precipitation_probability']} %",
        )

    with st.expander("Voir les prévisions horaires"):
        st.dataframe(
            weather,
            width="stretch",
            hide_index=True,
        )

else:
    st.info("Aucune prévision météorologique disponible.")


st.divider()


# --------------------------------------------------
# APERCU DES ESPACES VERTS
# --------------------------------------------------

st.markdown("### 🌳 Espaces verts de Paris")

if not categories.empty:

    st.markdown("**Répartition par type d'espace vert**")

    category_chart = categories.set_index("type_ev")
    st.bar_chart(category_chart)

    with st.expander("Voir les catégories"):
        st.dataframe(
            categories,
            width="stretch",
            hide_index=True,
        )

else:
    st.info("Aucune catégorie d'espace vert disponible.")


# --------------------------------------------------
# PIED DE PAGE
# --------------------------------------------------

st.divider()

st.caption(
    "SmartBreak — Projet ESEO | "
    "Données issues d'Open-Meteo et de Paris Data. "
    "Les informations affichées sont issues de la base PostgreSQL/PostGIS."
)
