# Dictionnaire de données — SmartBreak

## 1. Présentation

Le projet SmartBreak exploite deux sources de données complémentaires pour étudier les conditions favorables aux pauses en extérieur à Paris :

- **Open-Meteo** : prévisions météorologiques horaires pour Paris.
- **Paris Data — Espaces verts et assimilés** : informations descriptives et géographiques sur les espaces verts parisiens.

Les données sont collectées, validées, transformées et publiées dans une base PostgreSQL avec l'extension PostGIS.

Ce dictionnaire décrit les champs des deux tables CURATED : `weather_forecasts` et `green_spaces`.

---

## 2. Table `weather_forecasts`

### 2.1 Description

Cette table contient les prévisions météorologiques horaires collectées depuis l'API Open-Meteo.

Chaque ligne représente une observation prévisionnelle caractérisée par :
- un lieu ;
- une échéance de prévision ;
- un instant de collecte.

La contrainte d'unicité porte sur `(location, forecast_time, retrieved_at)`. Elle permet de conserver plusieurs snapshots d'une même échéance lorsqu'ils sont collectés à des moments différents.

### 2.2 Dictionnaire des champs

| Champ | Type PostgreSQL | Obligatoire | Unité / format | Description |
|---|---|---|---|---|
| `id` | BIGINT | Oui | Identifiant | Clé primaire générée automatiquement par PostgreSQL. |
| `location` | TEXT | Oui | Texte | Nom du lieu associé aux prévisions. |
| `latitude` | DOUBLE PRECISION | Oui | Degrés décimaux | Latitude du point de prévision. |
| `longitude` | DOUBLE PRECISION | Oui | Degrés décimaux | Longitude du point de prévision. |
| `elevation_m` | DOUBLE PRECISION | Oui | Mètre | Altitude du point de prévision. |
| `source` | TEXT | Oui | Texte | Nom de la source de données. |
| `source_url` | TEXT | Oui | URL | Adresse de l'API utilisée pour la collecte. |
| `retrieved_at` | TIMESTAMPTZ | Oui | Date UTC | Date et heure de récupération des données. |
| `forecast_time` | TIMESTAMPTZ | Oui | Date UTC | Date et heure auxquelles la prévision s'applique. |
| `temperature_2m` | DOUBLE PRECISION | Oui | °C | Température de l'air à 2 mètres. |
| `apparent_temperature` | DOUBLE PRECISION | Oui | °C | Température ressentie. |
| `relative_humidity_2m` | INTEGER | Oui | % | Humidité relative à 2 mètres. |
| `precipitation` | DOUBLE PRECISION | Oui | mm | Quantité de précipitations prévue. |
| `precipitation_probability` | INTEGER | Oui | % | Probabilité de précipitations. |
| `wind_speed_10m` | DOUBLE PRECISION | Oui | km/h | Vitesse du vent à 10 mètres. |
| `cloud_cover` | INTEGER | Oui | % | Couverture nuageuse. |
| `weather_code` | INTEGER | Oui | Code WMO | Code numérique décrivant les conditions météorologiques. |
| `geom` | geometry(Point, 4326) | Oui | Coordonnées géographiques | Géométrie spatiale du point de prévision, en longitude/latitude. |

### 2.3 Contraintes et règles

- Latitude comprise entre -90 et 90.
- Longitude comprise entre -180 et 180.
- Humidité relative comprise entre 0 et 100 %.
- Probabilité de précipitations comprise entre 0 et 100 %.
- Précipitations et vitesse du vent positives ou nulles.
- Code météo appartenant à la liste des codes WMO autorisés dans le schéma SQL.
- Unicité du triplet `(location, forecast_time, retrieved_at)`.

### 2.4 Index

- `idx_weather_forecast_time` : accélère les recherches par échéance.
- `idx_weather_forecasts_location` : accélère les recherches par lieu.
- `idx_weather_forecasts_geom` : index spatial GiST sur la géométrie.

---

## 3. Table `green_spaces`

### 3.1 Description

Cette table contient les espaces verts et assimilés issus du jeu de données officiel de Paris Data.

Chaque espace est identifié par son identifiant source `source_id`. Les données descriptives, les informations de surface, les adresses et les géométries sont stockées dans cette table.

Les propriétés originales de la source sont également conservées dans `raw_properties` afin de préserver la traçabilité.

### 3.2 Dictionnaire des champs

| Champ | Type PostgreSQL | Obligatoire | Unité / format | Description |
|---|---|---|---|---|
| `id` | BIGINT | Oui | Identifiant | Clé primaire technique générée automatiquement. |
| `source_id` | BIGINT | Oui | Identifiant source | Identifiant unique de l'espace vert dans Paris Data. |
| `name` | TEXT | Oui | Texte | Nom de l'espace vert. |
| `type_ev` | TEXT | Non | Texte | Type d'espace vert fourni par la source. |
| `category` | TEXT | Non | Texte | Catégorie de l'espace vert. |
| `address_number` | INTEGER | Non | Numéro | Numéro de l'adresse. |
| `address_complement` | TEXT | Non | Texte | Complément d'adresse. |
| `address_street_type` | TEXT | Non | Texte | Type de voie. |
| `address_street_name` | TEXT | Non | Texte | Nom de la voie. |
| `postal_code` | TEXT | Non | Texte | Code postal. |
| `polygon_area_m2` | DOUBLE PRECISION | Non | m² | Surface calculée du polygone dans la source. |
| `real_surface_m2` | DOUBLE PRECISION | Non | m² | Surface totale réelle renseignée par la source. |
| `horticultural_surface_m2` | DOUBLE PRECISION | Non | m² | Surface horticole renseignée par la source. |
| `presence_fence` | TEXT | Non | Texte | Information sur la présence d'une clôture. |
| `perimeter_m` | DOUBLE PRECISION | Non | m | Périmètre renseigné par la source. |
| `opening_year` | INTEGER | Non | Année | Année d'ouverture. |
| `renovation_year` | INTEGER | Non | Année | Année de rénovation. |
| `entity_count` | INTEGER | Non | Nombre | Nombre d'entités associé à l'espace vert dans la source. |
| `open_24h` | TEXT | Non | Texte | Information source relative à l'ouverture ou à la fermeture. |
| `geom` | geometry(Geometry, 4326) | Oui | Polygon / MultiPolygon | Géométrie spatiale de l'espace vert, en longitude/latitude. |
| `representative_point` | geometry(Point, 4326) | Non | Coordonnées géographiques | Point représentatif fourni par la source lorsqu'il est disponible et valide. |
| `source` | TEXT | Oui | Texte | Nom de la source de données. |
| `source_url` | TEXT | Oui | URL | Adresse de la source utilisée pour la collecte. |
| `retrieved_at` | TIMESTAMPTZ | Oui | Date UTC | Date et heure de récupération du dataset. |
| `raw_properties` | JSONB | Oui | JSON | Ensemble des propriétés originales de la feature GeoJSON. |

### 3.3 Correspondance avec les champs Paris Data

Les principales correspondances appliquées pendant la transformation sont :

| Champ CURATED | Champ source |
|---|---|
| `source_id` | `nsq_espace_vert` |
| `name` | `nom_ev` |
| `type_ev` | `type_ev` |
| `category` | `categorie` |
| `address_number` | `adresse_numero` |
| `address_complement` | `adresse_complement` |
| `address_street_type` | `adresse_typevoie` |
| `address_street_name` | `adresse_libellevoie` |
| `postal_code` | `adresse_codepostal` |
| `polygon_area_m2` | `poly_area` |
| `real_surface_m2` | `surface_totale_reelle` |
| `horticultural_surface_m2` | `surface_horticole` |
| `presence_fence` | `presence_cloture` |
| `perimeter_m` | `perimeter` |
| `opening_year` | `annee_ouverture` |
| `renovation_year` | `annee_renovation` |
| `entity_count` | `nb_entites` |
| `open_24h` | `ouvert_ferme` |
| `representative_point` | `geom_x_y` |

Les propriétés originales sont conservées dans `raw_properties`.

### 3.4 Transformations appliquées

- Les surfaces et le périmètre sont convertis en valeurs numériques facultatives.
- Les valeurs numériques négatives ou non convertibles sont remplacées par `NULL`.
- Les années et les nombres d'entités sont convertis en entiers lorsque cela est possible.
- Les informations de clôture et d'ouverture sont converties en texte.
- Le point représentatif est conservé uniquement si ses coordonnées sont numériques et dans les limites géographiques valides.
- La géométrie GeoJSON est conservée et convertie en géométrie PostGIS lors de la publication.

### 3.5 Contraintes et règles

- `source_id` est obligatoire et unique.
- `name` est obligatoire.
- La géométrie est obligatoire.
- La géométrie doit être de type Polygon ou MultiPolygon.
- La géométrie doit être valide selon `ST_IsValid`.
- La surface polygonale et le périmètre, lorsqu'ils sont renseignés, doivent être positifs ou nuls.

### 3.6 Index

- `idx_green_spaces_source_id` : recherche par identifiant source.
- `idx_green_spaces_type` : recherche par type d'espace vert.
- `idx_green_spaces_category` : recherche par catégorie.
- `idx_green_spaces_geom` : index spatial GiST sur les polygones.
- `idx_green_spaces_representative_point` : index spatial GiST sur les points représentatifs.

---

## 4. Données spatiales et système de coordonnées

Les deux tables utilisent le système de référence spatial **EPSG:4326** (WGS 84).

- Pour la météo, `geom` représente le point géographique auquel les prévisions sont associées.
- Pour les espaces verts, `geom` représente l'emprise géographique de l'espace.
- `representative_point` facilite les opérations de localisation et de visualisation.

Les index GiST permettent d'accélérer les recherches spatiales.

Les surfaces et périmètres proviennent des attributs du dataset source. Ils ne sont pas recalculés par le pipeline.

---

## 5. Gestion temporelle et traçabilité

Les deux sources n'ont pas la même logique temporelle.

| Champ | Table | Signification |
|---|---|---|
| `retrieved_at` | `weather_forecasts` | Date de collecte du snapshot météo. |
| `forecast_time` | `weather_forecasts` | Échéance à laquelle la prévision s'applique. |
| `retrieved_at` | `green_spaces` | Date de récupération du dataset géographique. |

Pour la météo, la distinction entre date de collecte et date de prévision permet de conserver l'historique des snapshots.

Pour les espaces verts, `source_id` permet d'identifier un même enregistrement lors des collectes successives et de réaliser un UPSERT sans créer de doublons.

Les champs `source`, `source_url` et `retrieved_at` assurent la traçabilité des données publiées.

---

## 6. Qualité et limites des données

Les données sont contrôlées avant leur publication en base.

- Les prévisions météo sont soumises aux règles Q01 à Q08.
- Les espaces verts sont soumis aux règles GQ01 à GQ07.
- Les enregistrements invalides sont isolés dans les sorties REJECTED avec les raisons de rejet.
- Les données acceptées sont transformées puis publiées dans PostgreSQL/PostGIS.

La présence d'un espace dans le dataset ne garantit pas qu'il soit accessible au public. Certains enregistrements correspondent à des espaces assimilés, des équipements ou d'autres catégories.

Par ailleurs, les prévisions météo proviennent d'un point central de Paris. Elles ne représentent donc pas nécessairement les microclimats propres à chaque espace vert.

Enfin, les champs descriptifs facultatifs peuvent être absents dans la source et sont alors conservés à `NULL` dans la table CURATED.