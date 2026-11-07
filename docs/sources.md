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

## 5. Sources envisagées pour les versions futures

| Source | Usage envisagé | Statut |
|---|---|---|
| Données ouvertes de la Ville de Paris | Localisation et caractéristiques des espaces verts | Non intégrée |
| Autres sources géographiques officielles | Accessibilité et équipements des lieux | Non intégrées |

Ces sources futures ne sont pas utilisées par le pipeline actuel.