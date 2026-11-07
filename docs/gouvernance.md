# Gouvernance des datasets — SmartBreak

## 1. Responsabilités et conservation

Les deux datasets sont gérés dans le cadre du projet SmartBreak par l'équipe projet.

| Dataset | Producteur | Responsable (owner) | Mise à jour de la source | Collecte par le pipeline | Rétention RAW | Rétention CURATED |
|---|---|---|---|---|---|---|
| `weather_hourly` | Open-Meteo | Équipe projet SmartBreak | Prévisions actualisées régulièrement par le fournisseur | À chaque exécution du pipeline | 12 mois (durée cible) | 12 mois (durée cible) |
| `paris_green_spaces` | Ville de Paris / DEVE — Paris Data | Équipe projet SmartBreak | Quotidienne selon les métadonnées du dataset | À chaque exécution du pipeline | 12 mois (durée cible) | 12 mois (durée cible) |

Les durées indiquées sont des règles de conservation proposées pour le projet. Elles ne correspondent pas à une suppression automatique déjà implémentée.

Les données rejetées et les rapports de qualité sont également conservés dans des répertoires distincts afin de faciliter l'audit et le suivi des collectes.

## 2. Qualité et traçabilité

Chaque source dispose de son propre contrat de qualité :

- `config/contracts/weather.yaml` : règles Q01 à Q08 pour les prévisions météorologiques.
- `config/contracts/green_spaces.yaml` : règles GQ01 à GQ07 pour les espaces verts.

Le processus de qualité suit les principes suivants :

1. Conservation de la réponse originale dans le répertoire RAW avant transformation.
2. Vérification de la structure et des champs obligatoires.
3. Contrôle des types, valeurs, coordonnées et contraintes propres à chaque source.
4. Séparation des enregistrements acceptés et rejetés, avec les motifs de rejet.
5. Transformation des données acceptées vers un format CURATED normalisé.
6. Publication dans PostgreSQL/PostGIS avec des contraintes d'intégrité et des index adaptés.

Les mécanismes de traçabilité comprennent :

- les métadonnées de collecte (`source`, `source_url`, `retrieved_at`) ;
- l'identifiant source des espaces verts (`source_id`) ;
- les dates de prévision et de collecte pour la météo (`forecast_time`, `retrieved_at`) ;
- les propriétés originales des espaces verts conservées dans `raw_properties` ;
- les journaux d'exécution dans `logs/pipeline.log` ;
- le rapport global dans `reports/run_report.json` ;
- les rapports de qualité propres à chaque dataset.

L'utilisation de clés uniques et d'UPSERT permet de limiter les doublons lors des republications. Pour la météo, les différents snapshots sont conservés grâce à la clé d'unicité `(location, forecast_time, retrieved_at)`. Pour les espaces verts, la clé métier est `source_id`.

## 3. Sécurité

- Les paramètres de connexion PostgreSQL sont stockés dans le fichier `.env`.
- Le fichier `.env` est exclu du dépôt Git.
- Le fichier `.env.example` fournit uniquement des valeurs de configuration fictives.
- Les identifiants et mots de passe ne doivent jamais être intégrés au code source ou aux fichiers RAW.
- Les accès à la base doivent être limités aux utilisateurs autorisés.
- Les échanges avec les API publiques utilisent des connexions HTTPS.

Les deux datasets exploités ne nécessitent pas de données personnelles pour le fonctionnement actuel de SmartBreak.

## 4. Licences et conditions d'utilisation

### 4.1 Données météorologiques

Les prévisions météorologiques proviennent d'Open-Meteo.

Leur utilisation, leur attribution et leur redistribution doivent respecter les conditions applicables à la source. Les informations correspondantes sont documentées dans `docs/sources.md`.

### 4.2 Espaces verts

Les données géographiques proviennent du jeu de données officiel « Espaces verts et assimilés » publié sur Paris Data par la Ville de Paris / DEVE.

Le jeu de données est diffusé sous licence ODbL (Open Database License). Toute réutilisation et redistribution doit respecter les obligations de cette licence, notamment les obligations d'attribution et, lorsque cela s'applique, de partage à l'identique des bases dérivées.

La source et son URL sont conservées dans les métadonnées de collecte.

## 5. Limites et précautions d'utilisation

- Les durées de rétention sont des objectifs documentés, mais leur application automatique n'est pas encore implémentée.
- La fréquence de collecte dépend de l'exécution effective du pipeline.
- Les mises à jour annoncées par les producteurs ne garantissent pas qu'une nouvelle version soit disponible à chaque collecte.
- La présence d'un espace dans le dataset Paris Data ne garantit pas son accessibilité au public : certains enregistrements correspondent à des espaces verts assimilés ou à d'autres catégories.
- Les prévisions météorologiques sont associées à un point central de Paris et ne représentent pas les microclimats propres à chaque espace vert.
- Les informations descriptives facultatives peuvent être absentes ou incomplètes dans les sources.

La gouvernance décrit ainsi les responsabilités, les règles de qualité et les mesures effectivement appliquées, tout en distinguant clairement les fonctionnalités opérationnelles des objectifs d'amélioration.