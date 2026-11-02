"""
init_project.py - Crée une fois pour toutes la structure du projet SmartBreak.

Usage (depuis le dossier PARENT du projet, ex. C:/Users/Abir/Projets) :
    python init_project.py

Comportement IDEMPOTENT : un fichier ou dossier déjà existant n'est jamais
écrasé. On peut relancer le script sans risque, par exemple après avoir
ajouté une nouvelle source dans la liste SOURCES.
"""
from pathlib import Path
import shutil

# Dossier racine du projet, créé dans le dossier courant
PROJECT = Path.cwd() / "smartbreak"

# Sources gérées par le pipeline. Pour ajouter une source plus tard :
# ajouter son nom ici (ex. "air_quality") puis relancer le script.
SOURCES = ["weather"]

# Zones de données de l'architecture RAW / REJECTED / CURATED
DATA_ZONES = ["raw", "curated", "rejected"]

# Dossiers qui peuvent rester vides : on y place un .gitkeep
# (Git ne versionne pas les dossiers vides)
KEEP_DIRS = (
    [f"data/{zone}/{src}" for zone in DATA_ZONES for src in SOURCES]
    + ["reports", "logs", "docs/architecture", "scripts"]
)

# ---------------------------------------------------------------------------
# Contenu des fichiers : chemin relatif -> texte
# ---------------------------------------------------------------------------
FILES = {
    # ---------------- Racine ----------------
    ".gitignore": """\
# --- Environnement Python ---
.venv/
__pycache__/
*.pyc
.pytest_cache/

# --- Secrets : JAMAIS dans le dépôt (exigence du guide) ---
.env

# --- Logs d'exécution ---
logs/*.log

# --- Données : régénérées par le pipeline, donc non versionnées ---
# Structure : data/<zone>/<source>/<fichier>
data/*/*/*
# ... sauf la structure (.gitkeep) et les échantillons exigés par le guide
!data/*/*/.gitkeep
!data/*/*/sample_*
""",

    ".env.example": """\
# Copier ce fichier en .env puis compléter. Le .env n'est JAMAIS versionné.
# Variables de connexion à la base (utilisées à partir de l'étape 0.3)
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=smartbreak
POSTGRES_USER=smartbreak
POSTGRES_PASSWORD=change_me
""",

    "README.md": """\
# SmartBreak - Recommandation dynamique de pause et de balade à Paris

> Projet final - Architecture BD et collecte de données - ESEO 2026-2027

## 1. Problème, utilisateur et question centrale
_À compléter (étape 1.1)_

## 2. Changement de sujet par rapport aux TP
_Ce projet est indépendant du projet personnel des TP. Les jalons des
séances 1 à 3 ont été refaits (voir `docs/`). À détailler._

## 3. Sources, licences et dates d'accès
_À compléter (étape 1.2, puis à chaque nouvelle source)_

## 4. Architecture et circulation des données
_À compléter (diagrammes dans `docs/architecture/`)_

## 5. Installation
_À compléter_

## 6. Exécution
_À compléter_

## 7. Contrat, règles de qualité et traitement des rejets
_À compléter (étapes 1.3 et 1.6)_

## 8. Résultat final et mode de consultation
_À compléter_

## 9. Test d'incident et stratégie de reprise
_À compléter (étape 1.12)_

## 10. Gouvernance : responsable et rétention
_Voir `docs/gouvernance.md`_

## 11. Limites, choix écartés et perspectives
_À compléter_

## 12. Usage d'outils d'IA
- Outil utilisé : ...
- Tâches assistées : ...
- Vérifications réalisées : ...
- Parties retravaillées personnellement : ...
""",

    # ---------------- Configuration ----------------
    "config/settings.yaml": """\
# Paramètres du pipeline SmartBreak.
# AUCUN secret ici : les secrets passent par le fichier .env.
# Les sections de chaque source sont ajoutées à l'étape 1.2 / 1.4.
project: smartbreak
sources: {}
""",

    "config/contracts/weather.yaml": """\
# Contrat de données - source météo (Open-Meteo Forecast)
# Version 1 rédigée à l'étape 1.3 :
# dataset, version, grain, owner, champs obligatoires, types, règles qualité.
""",

    # ---------------- SQL ----------------
    "sql/schema.sql": """\
-- Schéma de la base SmartBreak (PostgreSQL + PostGIS)
-- Tables, clés primaires et étrangères, contraintes, index.
-- Rédigé à l'étape 1.8, puis enrichi à chaque nouvelle source.
""",

    "sql/views.sql": """\
-- Vues métier (couche "mart") : indice de sortie, recommandations.
-- Rédigées aux étapes 1.13 et 5.x.
""",

    # ---------------- Code du pipeline ----------------
    "src/__init__.py": """\
# Rend le dossier src importable comme un package (utile pour les tests).
""",

    "src/config.py": """\
\"\"\"Lecture de la configuration : config/settings.yaml et variables du .env.

Implémenté à l'étape 1.4.
\"\"\"
""",

    "src/collect.py": """\
\"\"\"Étape 1 du pipeline - COLLECTE.

Appelle la source configurée, gère les erreurs d'accès et enregistre la
réponse BRUTE (non modifiée) dans data/raw/<source>/, avec un fichier de
métadonnées (source, URL, date de collecte, run_id, taille).

Implémenté à l'étape 1.4.
\"\"\"
""",

    "src/validate.py": """\
\"\"\"Étape 3 du pipeline - QUALITÉ.

Applique les règles du contrat de données (config/contracts/<source>.yaml).
Sépare les lignes acceptées des lignes rejetées ; chaque rejet conserve la
valeur concernée, la règle violée, la raison et la date de détection.

Implémenté à l'étape 1.6.
\"\"\"
""",

    "src/transform.py": """\
\"\"\"Étape 4 du pipeline - TRANSFORMATION.

Typage, normalisation (UTC, unités), renommage, déduplication et champs
calculés. Produit data/curated/<source>/.

Implémenté à l'étape 1.7.
\"\"\"
""",

    "src/db.py": """\
\"\"\"Connexion à PostgreSQL (paramètres lus dans le .env).

Implémenté à l'étape 1.8.
\"\"\"
""",

    "src/publish.py": """\
\"\"\"Étape 6 du pipeline - PUBLICATION.

Charge les données curated en base avec un UPSERT (pas de doublon au rejeu).

Implémenté à l'étape 1.8.
\"\"\"
""",

    "src/pipeline.py": """\
\"\"\"Point d'entrée unique du pipeline.

Enchaîne collecte -> validation -> transformation -> publication,
écrit les logs (logs/pipeline.log) et le rapport d'exécution
(reports/run_report.json).

Implémenté à l'étape 1.9.
\"\"\"
""",

    # ---------------- Application ----------------
    "app/streamlit_app.py": """\
\"\"\"Restitution Streamlit : décision dehors/dedans, créneaux, lieux.

Implémenté à l'étape 1.13, puis enrichi en phase 5.
\"\"\"
""",

    # ---------------- Tests ----------------
    "tests/test_quality.py": """\
\"\"\"Tests automatisés (pytest) des règles de qualité.

Implémentés à l'étape 1.10.
\"\"\"
""",

    # ---------------- Documentation ----------------
    "docs/fiche_projet.md": """\
# Fiche projet - SmartBreak

| Question | Réponse |
|---|---|
| Nom | SmartBreak |
| Utilisateur | _à compléter_ |
| Problème | _à compléter_ |
| Décision | _à compléter_ |
| Question centrale | _à compléter_ |
| Périmètre (inclus / exclu) | _à compléter_ |
| Fréquence utile | _à compléter_ |

## Cas d'usage et KPI

| Cas d'usage | KPI | Données nécessaires | Fréquence |
|---|---|---|---|
| 1. | | | |
| 2. | | | |
| 3. | | | |
""",

    "docs/sources.md": """\
# Fiches sources

## Source météo - comparaison des candidates

| Critère | Source A | Source B |
|---|---|---|
| Producteur et URL | | |
| Mode d'accès | | |
| Format | | |
| Fréquence de mise à jour | | |
| Clé ou identifiant | | |
| Licence ou conditions | | |
| Risque technique | | |
| Données personnelles | | |

**Source retenue et justification :** _à compléter (étape 1.2)_
""",

    "docs/data_dictionary.md": """\
# Dictionnaire de données

## weather_hourly
_Grain : "Une ligne représente ..." - à compléter (étape 1.3)_

| Champ | Type | Obligatoire | Unité | Description | Exemple |
|---|---|---|---|---|---|
""",

    "docs/ADR_001.md": """\
# ADR 001 - Architecture cible

- **Contexte :** ...
- **Exigences :** ...
- **Options comparées :** ...
- **Décision :** ...
- **Arguments :** ...
- **Conséquences positives :** ...
- **Conséquences négatives :** ...
- **Condition de réexamen :** ...
""",

    "docs/gouvernance.md": """\
# Gouvernance des datasets

| Dataset | Responsable (owner) | Fréquence de collecte | Rétention raw | Rétention curated |
|---|---|---|---|---|
| weather | _à compléter_ | | | |
""",
}


def write_if_absent(path: Path, content: str) -> str:
    """Écrit le fichier seulement s'il n'existe pas encore (idempotence).

    - encoding="utf-8" : les accents sont conservés correctement ;
    - newline="\\n"     : fins de ligne Unix, identiques sur tous les OS.
    Retourne un statut lisible pour le récapitulatif.
    """
    if path.exists():
        return "conservé"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8", newline="\n")
    return "créé"


def main() -> None:
    print(f"Projet : {PROJECT}\n")

    # 1) Dossiers pouvant rester vides + fichier .gitkeep
    for rel in KEEP_DIRS:
        status = write_if_absent(PROJECT / rel / ".gitkeep", "")
        print(f"[{status:8}] {rel}/.gitkeep")

    # 2) Fichiers de base
    for rel, content in FILES.items():
        status = write_if_absent(PROJECT / rel, content)
        print(f"[{status:8}] {rel}")

    # 3) Copie de ce script dans le projet (traçabilité de la création)
    target = PROJECT / "scripts" / "init_project.py"
    if not target.exists():
        shutil.copy(Path(__file__), target)
        print("[créé    ] scripts/init_project.py")

    print("\nStructure prête.")


if __name__ == "__main__":
    main()