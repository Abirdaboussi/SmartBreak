"""Vérifie la connexion à PostgreSQL et la présence de PostGIS (étape 0.3).

Lit les paramètres dans le fichier .env : aucun mot de passe dans le code.
"""
import os

from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL

load_dotenv()  # charge les variables du .env dans l'environnement

# URL.create gère correctement les caractères spéciaux du mot de passe
url = URL.create(
    drivername="postgresql+psycopg",
    username=os.environ["POSTGRES_USER"],
    password=os.environ["POSTGRES_PASSWORD"],
    host=os.environ["POSTGRES_HOST"],
    port=int(os.environ["POSTGRES_PORT"]),
    database=os.environ["POSTGRES_DB"],
)

engine = create_engine(url)
with engine.connect() as conn:
    print("PostgreSQL :", conn.execute(text("SELECT version()")).scalar())
    print("PostGIS    :", conn.execute(text("SELECT postgis_version()")).scalar())
    print("Utilisateur:", conn.execute(text("SELECT current_user")).scalar())