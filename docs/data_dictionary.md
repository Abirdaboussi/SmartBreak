# Dictionnaire de données — SmartBreak

## 1. Dataset : weather_hourly

**Source :** Open-Meteo Forecast API

**Zone géographique :** Paris, France

**Grain :** Une ligne représente les conditions météorologiques
prévues pour une heure précise et une localisation donnée.

**Fréquence :** Horaire.

**Fuseau horaire de stockage :** GMT (UTC).

**Format RAW :** JSON.

**Destination CURATED :** PostgreSQL.

## 2. Description des champs

| Champ | Type | Obligatoire | Unité | Description | Exemple |
|---|---|---|---|---|---|
| time | STRING | Oui | GMT | Date et heure de la prévision | 2026-11-07T10:00 |
| temperature_2m | FLOAT | Oui | °C | Température à 2 mètres | 12.5 |
| apparent_temperature | FLOAT | Oui | °C | Température ressentie | 11.2 |
| relative_humidity_2m | INTEGER | Oui | % | Humidité relative | 75 |
| precipitation | FLOAT | Oui | mm | Quantité de précipitations prévue | 0.0 |
| precipitation_probability | INTEGER | Oui | % | Probabilité de précipitations | 20 |
| wind_speed_10m | FLOAT | Oui | km/h | Vitesse du vent à 10 mètres | 8.5 |
| cloud_cover | INTEGER | Oui | % | Couverture nuageuse | 40 |
| weather_code | INTEGER | Oui | WMO code | Code météorologique WMO | 3 |

## 3. Structure et métadonnées RAW

Le fichier RAW est un objet JSON composé de deux clés principales :

- `metadata` : informations relatives à la collecte.
- `response` : réponse originale de l'API Open-Meteo.

### Métadonnées de collecte

| Métadonnée | Description |
|---|---|
| source | Nom de la source de données |
| source_url | URL de l'API |
| location | Localisation demandée |
| latitude_requested | Latitude demandée |
| longitude_requested | Longitude demandée |
| retrieved_at | Date et heure de collecte en UTC |
| timezone_requested | Fuseau horaire demandé |

### Métadonnées de la réponse API

| Métadonnée | Description |
|---|---|
| latitude | Latitude réellement retournée |
| longitude | Longitude réellement retournée |
| timezone | Fuseau horaire de la réponse |
| timezone_abbreviation | Abréviation du fuseau |
| utc_offset_seconds | Décalage par rapport à UTC |
| elevation | Altitude du point de prévision |
| hourly_units | Unités des variables horaires |

La réponse originale est conservée dans `response`.
Les observations horaires sont disponibles dans `response.hourly`.

## 4. Règles de qualité

| ID | Règle | Objectif |
|---|---|---|
| Q01 | Champs obligatoires | Éviter les valeurs absentes |
| Q02 | Unicité du timestamp | Éviter les doublons |
| Q03 | Format du timestamp | Garantir des dates exploitables |
| Q04 | Ordre chronologique | Préserver la cohérence temporelle |
| Q05 | Fréquence horaire | Détecter les heures manquantes |
| Q06 | Plages numériques | Détecter les valeurs anormales |
| Q07 | Code météo valide | Respecter le domaine des codes WMO |
| Q08 | Unités cohérentes | Éviter les erreurs d'interprétation |

## 5. Utilisation dans SmartBreak

Les données météo seront utilisées pour évaluer les conditions
favorables à une pause extérieure.

Les variables principales sont :
- temperature_2m et apparent_temperature ;
- precipitation et precipitation_probability ;
- wind_speed_10m ;
- cloud_cover ;
- weather_code.

Les données sont des prévisions météorologiques et non
des observations réelles.