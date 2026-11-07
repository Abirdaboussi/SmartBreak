# Gouvernance des datasets — SmartBreak

## 1. Responsabilités et conservation

| Dataset | Responsable (owner) | Fréquence de collecte | Rétention RAW | Rétention CURATED |
|---|---|---|---|---|
| weather_hourly | Équipe projet SmartBreak | À chaque exécution du pipeline | 12 mois (durée cible) | 12 mois (durée cible) |

Les durées indiquées sont des règles de conservation proposées pour le projet. Elles ne correspondent pas à une suppression automatique déjà implémentée.

## 2. Qualité et traçabilité

- Le contrat `config/contracts/weather.yaml` définit les champs obligatoires et les règles de qualité.
- Chaque collecte est conservée au format JSON dans le répertoire RAW.
- Les observations invalides sont isolées dans le répertoire REJECTED avec leurs motifs.
- Les données acceptées sont transformées puis publiées dans PostgreSQL/PostGIS.
- Les logs et le rapport JSON permettent de suivre le résultat de chaque exécution.

## 3. Sécurité

- Les paramètres de connexion PostgreSQL sont stockés dans `.env`.
- Le fichier `.env` est exclu du dépôt Git.
- Le fichier `.env.example` fournit uniquement des valeurs de configuration fictives.
- Les accès à la base doivent être limités aux utilisateurs autorisés.

## 4. Licence et utilisation

Les données météo proviennent d'Open-Meteo. Leur utilisation et leur redistribution doivent respecter les conditions de licence et d'attribution de la source, documentées dans `sources.md`.

## 5. Limites actuelles

La suppression automatique selon les durées de rétention n'est pas encore implémentée. La gouvernance décrit donc la politique cible et les mesures actuellement appliquées, sans prétendre que toutes les opérations sont automatisées.
