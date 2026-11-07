# Simulation d'incident et procédure de récupération

## 1. Contexte

Une simulation d'incident a été réalisée le 7 novembre 2026 sur un
échantillon RAW du jeu de données météorologiques SmartBreak.

Fichier utilisé :
`sample_open_meteo_paris_20261107_180722.json`

L'objectif est de vérifier la capacité du système à détecter une donnée
invalide, à l'isoler et à retrouver un état valide après correction.

## 2. Incident simulé

Une valeur volontairement invalide a été introduite en mémoire dans le
champ `weather_code` :

- Valeur initiale : code météo valide issu du fichier RAW.
- Valeur injectée : `999`.
- Règle de qualité concernée : `Q07` — validité du code météo WMO.

Le fichier RAW original n'a pas été modifié.

## 3. Détection et résultat

La validation a détecté l'anomalie et rejeté l'observation concernée.

| Indicateur | État initial | Pendant l'incident |
|---|---:|---:|
| Observations totales | 48 | 48 |
| Observations acceptées | 48 | 47 |
| Observations rejetées | 0 | 1 |
| Violations Q07 | 0 | 1 |
| Taux d'acceptation | 100 % | 97,92 % |

Motif enregistré :

`Code météo WMO invalide : 999`

La règle Q07 a donc correctement empêché l'intégration de cette
observation invalide dans les données acceptées.

## 4. Procédure de récupération

La valeur initiale du champ `weather_code` a été restaurée dans la copie
en mémoire utilisée pour le test.

Une nouvelle validation a ensuite été exécutée.

Résultat après correction :

| Indicateur | Résultat |
|---|---:|
| Observations totales | 48 |
| Observations acceptées | 48 |
| Observations rejetées | 0 |
| Violations Q07 | 0 |
| Taux d'acceptation | 100 % |
| Statut | passed |

## 5. Bilan

La simulation confirme que :

- Le contrôle Q07 détecte un code météo WMO invalide.
- L'observation concernée est rejetée sans bloquer les 47 autres.
- La correction permet de retrouver une validation complète.
- Le fichier RAW original reste intact.

**Limite du test :** cette simulation a été réalisée en mémoire.
Elle valide le comportement de la fonction de contrôle qualité et la
récupération après correction, mais ne constitue pas un test de
restauration d'une sauvegarde PostgreSQL.

## 6. Améliorations possibles

Pour une version ultérieure, il serait pertinent d'ajouter :

- Une alerte automatique en cas de hausse du taux de rejet.
- Un suivi historique des incidents.
- Une procédure de rejeu des données corrigées.
- Des tests automatisés dédiés aux scénarios d'incident.
