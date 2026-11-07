# SmartBreak — Recommandation de pauses extérieures à Paris

**Projet final — Architecture des bases de données et collecte de données — ESEO 2026–2027**

## 1. Présentation du projet

SmartBreak est un projet de traitement et de valorisation de données destiné à aider le grand public à identifier des moments favorables à une pause ou à une balade en extérieur à Paris.

La qualité d'une pause extérieure dépend notamment des conditions météorologiques : température, pluie, vent, humidité et couverture nuageuse.

La première version technique du projet met en place un pipeline automatisé qui collecte les prévisions météorologiques horaires de Paris, contrôle leur qualité, les transforme, conserve les données brutes et publie les données validées dans PostgreSQL/PostGIS.

**Question centrale :** comment collecter, contrôler, historiser et exploiter des données météorologiques fiables afin de préparer un service d'aide au choix des moments favorables aux pauses extérieures ?

### Public cible

- Grand public résidant à Paris ou visitant la ville.
- Personnes souhaitant organiser une pause ou une balade en fonction de la météo.

### Périmètre actuel

La version livrée couvre :
- La collecte de prévisions météorologiques horaires pour Paris.
- La conservation des réponses brutes au format JSON.
- La validation selon un contrat de données.
- La séparation des données acceptées et rejetées.
- La transformation et la normalisation des données.
- La publication dans PostgreSQL avec l'extension PostGIS.
- La création de vues SQL pour consulter les dernières prévisions et les synthèses journalières.
- La traçabilité des exécutions par des logs et un rapport JSON.

Les espaces verts, la recommandation personnalisée de lieux, l'interface utilisateur et le moteur complet de décision constituent des évolutions futures et ne sont pas présentés comme des fonctionnalités déjà livrées.

## 2. Architecture et flux de données

Le pipeline suit les étapes suivantes :

1. **Collecte :** récupération des prévisions horaires via l'API Open-Meteo.
2. **RAW :** archivage de la réponse JSON avec les métadonnées de collecte.
3. **Validation :** contrôle des observations selon le contrat `config/contracts/weather.yaml`.
4. **Rejets :** conservation des observations invalides et de leurs motifs de rejet.
5. **Transformation :** normalisation des timestamps et préparation des champs CURATED.
6. **Publication :** insertion ou mise à jour des données dans PostgreSQL/PostGIS par UPSERT.
7. **Consultation :** exposition des données au moyen de vues SQL.
8. **Traçabilité :** écriture des logs et du rapport `reports/run_report.json`.

### Technologies

| Élément | Technologie |
|---|---|
| Langage | Python |
| Source météo | Open-Meteo Forecast API |
| Format RAW | JSON |
| Contrat de données | YAML |
| Base de données | PostgreSQL |
| Données géographiques | PostGIS |
| Accès base de données | psycopg 3 |
| Tests | pytest |
| Configuration | python-dotenv |

## 3. Source de données et licence

La source actuellement intégrée est l'API de prévisions météorologiques Open-Meteo :

https://api.open-meteo.com/v1/forecast

Les variables collectées sont :
- `temperature_2m` : température à 2 mètres, en °C.
- `apparent_temperature` : température ressentie, en °C.
- `relative_humidity_2m` : humidité relative, en %.
- `precipitation` : précipitations prévues, en mm.
- `precipitation_probability` : probabilité de précipitations, en %.
- `wind_speed_10m` : vitesse du vent à 10 mètres, en km/h.
- `cloud_cover` : couverture nuageuse, en %.
- `weather_code` : code météorologique WMO.

Les données sont des **prévisions**, et non des observations météorologiques réellement mesurées.

Les conditions de licence et d'attribution applicables à la source sont documentées dans `docs/sources.md`. La source doit être attribuée à Open-Meteo conformément à ses conditions d'utilisation.

## 4. Installation et configuration

### Prérequis

- Python 3.10 ou version compatible avec les dépendances du projet.
- PostgreSQL installé et démarré.
- Extension PostGIS disponible sur l'instance PostgreSQL.
- Git.

### Récupération du projet

```powershell
git clone https://github.com/Abirdaboussi/SmartBreak.git
cd SmartBreak
```

### Création de l'environnement Python

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### Configuration de la base de données

Créer une base PostgreSQL nommée `smartbreak` et un utilisateur disposant des droits nécessaires.

Copier le fichier d'exemple :

```powershell
Copy-Item .env.example .env
```

Modifier ensuite `.env` avec les paramètres de connexion de l'environnement local :

```dotenv
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=smartbreak
POSTGRES_USER=smartbreak
POSTGRES_PASSWORD=VOTRE_MOT_DE_PASSE
```

Le fichier `.env` contient des informations de connexion et ne doit jamais être ajouté au dépôt Git.

L'extension PostGIS est activée par le script `sql/schema.sql`. L'utilisateur PostgreSQL doit disposer des permissions nécessaires pour créer cette extension, ou celle-ci doit être activée préalablement par un administrateur.

## 5. Exécution du pipeline

Depuis la racine du projet, avec l'environnement virtuel activé :

```powershell
python -m src.pipeline
```

Le pipeline exécute automatiquement :
- l'initialisation du schéma PostgreSQL/PostGIS et des vues ;
- la collecte des prévisions ;
- la validation des observations ;
- la transformation des observations acceptées ;
- la sauvegarde des fichiers CURATED et REJECTED ;
- la publication dans PostgreSQL ;
- la génération du rapport d'exécution.

Les sorties sont enregistrées dans :
- `data/raw/weather/` : réponses brutes ;
- `data/curated/weather/` : données transformées et acceptées ;
- `data/rejected/weather/` : données rejetées ;
- `logs/` : journaux d'exécution ;
- `reports/run_report.json` : rapport de la dernière exécution.

## 6. Qualité des données et tests

Le contrat `config/contracts/weather.yaml` définit le schéma attendu et les contrôles de qualité.

Huit règles sont appliquées :

| Règle | Contrôle |
|---|---|
| Q01 | Présence des champs obligatoires |
| Q02 | Unicité des timestamps |
| Q03 | Format des timestamps |
| Q04 | Ordre chronologique |
| Q05 | Fréquence horaire |
| Q06 | Types et plages numériques |
| Q07 | Validité des codes météorologiques WMO |
| Q08 | Cohérence des unités |

Les observations non conformes sont isolées dans le répertoire REJECTED avec leurs motifs de rejet. Les observations valides sont transformées et publiées.

Pour lancer les tests :

```powershell
python -m pytest -q
```

La suite de tests actuelle contient **19 tests réussis** dans l'environnement de développement utilisé pour valider cette version.

## 7. Base de données et consultation

La table `weather_forecasts` stocke les prévisions validées, leurs métadonnées et leur géométrie géographique au format PostGIS `geometry(Point, 4326)`.

Une contrainte d'unicité sur `(location, forecast_time, retrieved_at)` permet de rejouer une même collecte sans créer de doublons.

Deux vues facilitent la consultation :

- `vw_weather_latest_forecasts` : dernière version disponible de chaque prévision horaire.
- `vw_weather_daily_summary` : synthèse journalière des températures, précipitations, probabilités de pluie, vent et couverture nuageuse.

Les agrégations journalières utilisent le fuseau `Europe/Paris`.

## 8. Traçabilité et reprise

Chaque collecte possède un identifiant dérivé du nom du fichier RAW. Les fichiers CURATED et REJECTED sont associés à cette collecte.

Le pipeline produit un rapport JSON comprenant notamment :
- les dates de début et de fin ;
- le statut global ;
- le nombre d'observations collectées ;
- les nombres d'observations acceptées et rejetées ;
- le taux d'acceptation ;
- le nombre de violations par règle ;
- le nombre de lignes publiées ;
- la durée d'exécution.

### Stratégie de reprise

En cas d'échec :
1. consulter `logs/pipeline.log` et `reports/run_report.json` ;
2. identifier l'étape en erreur ;
3. vérifier la disponibilité de l'API et de PostgreSQL ;
4. corriger la configuration ou le problème identifié ;
5. relancer le pipeline.

L'UPSERT permet de rejouer une publication pour un même instant de collecte sans créer de doublons.

Un scénario d'incident doit être exécuté et documenté séparément avant de déclarer la reprise effectivement testée.

## 9. Gouvernance et organisation du dépôt

Le dictionnaire de données est disponible dans `docs/data_dictionary.md`.

Les choix d'architecture sont documentés dans `docs/ADR_001.md`. Les règles de gouvernance et les informations relatives aux sources sont décrites dans `docs/gouvernance.md` et `docs/sources.md`.

Les données brutes de démonstration peuvent être conservées dans le dépôt. Les nouvelles données générées, les logs, les rapports d'exécution, les environnements virtuels et les secrets sont exclus du versionnement.

## 10. Limites et perspectives

La version actuelle est une première brique technique démontrable. Elle ne constitue pas encore un système complet de recommandation de pauses.

Évolutions envisagées :
- intégrer les données officielles des espaces verts de Paris ;
- enrichir le modèle géographique avec les lieux accessibles ;
- définir un score de confort extérieur explicable ;
- développer une interface de consultation ;
- intégrer des préférences utilisateur et des critères d'accessibilité ;
- automatiser les collectes et le suivi de la qualité.

## 11. Utilisation d'outils d'intelligence artificielle

Des outils d'intelligence artificielle ont été utilisés comme assistance au développement, à la structuration de la documentation et à l'analyse des erreurs.

Les scripts, les résultats de tests, les requêtes SQL et le fonctionnement du pipeline ont été vérifiés dans l'environnement local du projet. Les résultats présentés correspondent aux exécutions effectivement réalisées.

## 12. Dépôt

GitHub : https://github.com/Abirdaboussi/SmartBreak
