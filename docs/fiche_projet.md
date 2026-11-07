# Fiche projet — SmartBreak

| Question | Réponse |
|---|---|
| Nom | SmartBreak |
| Utilisateur | Grand public : habitants et visiteurs de Paris souhaitant organiser une pause ou une balade extérieure. |
| Problème | Il est difficile de choisir un moment favorable pour une activité extérieure sans disposer d'une information météo horaire centralisée et exploitable. |
| Décision | Collecter, contrôler, transformer et stocker des prévisions météo horaires afin de préparer un service d'aide à la décision. |
| Question centrale | Comment exploiter des données météorologiques fiables et actualisées pour identifier les périodes potentiellement favorables aux pauses extérieures à Paris ? |
| Périmètre (inclus / exclu) | Inclus : collecte Open-Meteo, archivage RAW, validation, transformation, stockage PostgreSQL/PostGIS et vues SQL. Exclu de la version actuelle : espaces verts, recommandation personnalisée, interface utilisateur et géolocalisation des préférences. |
| Fréquence utile | Données météorologiques horaires, collectées à chaque exécution du pipeline. |

## Cas d'usage et KPI

| Cas d'usage | KPI | Données nécessaires | Fréquence |
|---|---|---|---|
| 1. Consulter les prévisions horaires à Paris | Nombre d'heures disponibles et fraîcheur de la dernière collecte | Température, pluie, vent, humidité, couverture nuageuse, code météo | Horaire |
| 2. Comparer les conditions météo sur une journée | Température moyenne/minimale/maximale, précipitations cumulées, vent maximal | Prévisions horaires et timestamps | Journalière |
| 3. Vérifier la fiabilité des données collectées | Taux d'acceptation, nombre de rejets, violations par règle | Rapport de validation Q01–Q08 | À chaque exécution |

## Objectifs mesurables de la première version

- Collecter les prévisions horaires disponibles pour Paris.
- Appliquer huit règles automatisées de qualité.
- Conserver séparément les données acceptées et rejetées.
- Publier les données validées dans PostgreSQL/PostGIS.
- Garantir l'idempotence de la publication pour un même instant de collecte.
- Produire un rapport JSON et des logs pour chaque exécution.

**Limite :** ces KPI évaluent le fonctionnement et la qualité du pipeline. Ils ne mesurent pas encore la pertinence d'un moteur de recommandation, qui n'est pas implémenté dans cette version.
