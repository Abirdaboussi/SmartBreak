# Fiches sources — SmartBreak

## 1. Source météo retenue

| Critère | Open-Meteo Forecast API |
|---|---|
| Producteur et URL | Open-Meteo — https://api.open-meteo.com/v1/forecast |
| Mode d'accès | API HTTP GET |
| Format | JSON |
| Fréquence de mise à jour | Prévisions actualisées régulièrement par le fournisseur |
| Clé ou identifiant | Combinaison localisation, heure de prévision et instant de collecte |
| Licence ou conditions | Conditions et attribution Open-Meteo ; consulter les pages officielles relatives aux données utilisées |
| Risque technique | Indisponibilité de l'API, évolution du schéma, limites d'utilisation |
| Données personnelles | Aucune donnée personnelle n'est demandée par le pipeline |

## 2. Utilisation dans SmartBreak

La collecte porte sur Paris (latitude et longitude définies dans `src/collect.py`) et récupère huit variables horaires :

- Température et température ressentie.
- Humidité relative.
- Précipitations et probabilité de précipitations.
- Vitesse du vent.
- Couverture nuageuse.
- Code météorologique WMO.

La réponse originale est conservée dans le répertoire RAW avec les métadonnées de collecte.

## 3. Justification du choix

Open-Meteo a été retenue pour les raisons suivantes :

- Accès simple via une API HTTP.
- Réponse structurée au format JSON.
- Variables météorologiques horaires adaptées au besoin.
- Couverture géographique de Paris.
- Intégration simple dans un pipeline Python.

## 4. Attribution et précautions

Les prévisions ne doivent pas être présentées comme des mesures réellement observées.

Avant toute redistribution publique des données, les conditions applicables à l'offre Open-Meteo utilisée doivent être vérifiées.

Documentation officielle :
- API Forecast : https://open-meteo.com/en/docs
- Informations sur les licences : https://open-meteo.com/en/licence

## 5. Deuxième source candidate — Espaces verts de Paris

### Identification

| Critère | Informations |
|---|---|
| Nom du jeu de données | Espaces verts et assimilés |
| Producteur | Direction des Espaces Verts et de l'Environnement (DEVE) — Ville de Paris |
| Portail | https://opendata.paris.fr/explore/dataset/espaces_verts/ |
| Identifiant du jeu | `espaces_verts` |
| Mode d'accès | Portail Open Data Paris, consultation, export et API du portail |
| Formats disponibles | CSV, JSON et formats géographiques selon les possibilités d'export |
| Fréquence de mise à jour annoncée | Quotidienne |
| Licence | Open Database License (ODbL) |
| Territoire | Paris et périmètre indiqué dans les métadonnées du jeu |
| Données personnelles | Le jeu décrit des espaces géographiques et leurs caractéristiques ; aucune donnée personnelle n'est nécessaire à l'usage envisagé |

### Contenu et intérêt pour SmartBreak

Cette source décrit et géolocalise les emprises d'espaces verts publics : parcs, jardins, squares et promenades.

Les informations disponibles comprennent notamment :
- la géométrie et la localisation des espaces ;
- le nom et le type d'espace vert ;
- les informations de surface ;
- certaines caractéristiques et informations d'ouverture.

L'identifiant du jeu est `espaces_verts`. Le portail présente également un champ « Identifiant espace vert ». Sa stabilité et son unicité devront être vérifiées avant toute intégration.

Cette source est complémentaire à Open-Meteo :
- Open-Meteo décrit les conditions météorologiques prévues ;
- Espaces verts et assimilés décrit les lieux susceptibles d'accueillir une pause en extérieur.

Une future version de SmartBreak pourrait ainsi rapprocher les conditions météo des caractéristiques géographiques des espaces verts.

### Risques et précautions

- Vérifier la disponibilité du portail et de son API au moment de la collecte.
- Contrôler le système de coordonnées des géométries avant leur insertion dans PostGIS.
- Vérifier l'unicité et la stabilité de l'identifiant de chaque espace vert.
- Contrôler les valeurs manquantes, les géométries invalides et les éventuelles évolutions du schéma.
- Vérifier les conditions de réutilisation et les obligations d'attribution liées à la licence ODbL.
- Ne pas considérer automatiquement tous les enregistrements comme des lieux accessibles au public : certains types décrits peuvent nécessiter une interprétation ou un filtrage.

### Statut dans le projet

**Source candidate documentée — non intégrée dans la V1.**

Elle n'est pas collectée, transformée ni publiée dans la base de données actuelle. Son intégration est envisagée pour une future version du projet.

Source officielle et métadonnées :
https://opendata.paris.fr/explore/dataset/espaces_verts/
