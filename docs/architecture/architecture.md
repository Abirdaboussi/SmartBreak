# Architecture SmartBreak

## 1. Architecture V1 — Version implémentée

Cette architecture représente le pipeline météo actuellement développé et testé.

```mermaid
flowchart TD
    A["Open-Meteo Forecast API"] --> B["Collecte Python"]
    B --> C["RAW - JSON horodaté"]
    C --> D["Validation - Contrat YAML"]
    D -->|Observations acceptées| E["Transformation Python"]
    D -->|Observations rejetíes| F["REJECTED - JSON + motifs"]
    E --> G["CURATED - JSON"]
    G --> H["Publication - UPSERT"]
    H --> I[("PostgreSQL + PostGIS")]
    I --> J["Vues SQL"]
    B --> K["Logs"]
    D --> L["Rapport JSON"]
    H --> L
```

## 2. Architecture V2 — Architecture cible envisagée

Cette architecture représente les évolutions possibles. Elle n'est pas encore implémentée.

```mermaid
flowchart TD
    A["Open-Meteo API"] --> C["Collecte multi-sources"]
    B["Open Data - Espaces verts de Paris"] --> C
    C --> D["Zone RAW"]
    D --> E["Validation et contrôle qualité"]
    E --> F["Zone REJECTED"]
    E --> G["Transformation et enrichissement"]
    G --> H[("PostgreSQL + PostGIS")]
    H --> I["Calcul du score de confort"]
    I --> J["Moteur de recommandation"]
    J --> K["Interface utilisateur"]
    K --> L["Suggestions de pauses et balades"]
```

## 3. Lineage — Traçabilité des données

Le lineage décrit le chemin suivi par une observation depuis sa collecte jusqu'à sa consultation.

```mermaid
flowchart LR
    A["Open-Meteo API"] --> B["RAW JSON"]
    B --> C["Extraction des observations"]
    C --> D{"Validation Q01-Q08"}
    D-->|Non conforme| E["REJECTED JSON"]
    D -->|Conforme| F["Transformation"]
    F --> G["CURATED JSON"]
    G --> H["UPSERT PostgreSQL"]
    H --> I["weather_forecasts"]
    I --> J["vw_weather_latest_forecasts"]
    I --> K["vw_weather_daily_summary"]
```

### Métadonnées de traçabilité

| Élément | Røle |
|---|---|
| `source` | Identifie le fournisseur |
| `source_url` | Identifie l'API utilisée |
| `retrieved_at` | Date et heure de collecte |
| `forecast_time` | Date et heure de la prévision |
| `run_id` | Identifie la collecte et ses fichiers associés |
| `rule_violations` | Compte les violations des rèples de qualité |
| `logs/pipeline.log` | Trace les étapes d'exécution |
| `reports/run_report.json` | Résume le résultat du pipeline |


### Gestion temporelle

Deux dates doivent être distinguées :

- `retrieved_at` : moment où les prévisions ont été collectées.
- `forecast_time` : moment auquel les conditions météorologiques sont prévues.

Cette distinction permet de conserver plusieurs versions d'une même prévision lorsque plusieurs collectes sont effectuées.
