# ADR-013 : Trajectoires simulées et météo écartées du modèle et du dashboard
Date : 2026-11-10
Statut : acceptée

## Contexte
La phase 1 a ingéré dans PostGIS des trajectoires simulées autour de Toulouse-Blagnac et une météo historique
(Open-Meteo), et prévu un METAR en direct. N-CMAPSS est un jeu simulé : ses moteurs ne correspondent à aucun vol réel,
mais il fournit déjà les conditions de vol (`alt`, `Mach`, `TRA`, `T2`) et la classe de vol `Fc`.

## Options envisagées
- Ajouter la météo de surface aux variables du modèle.
- Associer de vraies trajectoires ADS-B aux moteurs simulés.
- Afficher une carte des trajectoires et une vue météo dans le dashboard.
- Laisser ces données hors du modèle et du dashboard, en conservant le code d'ingestion.

## Décision
Ni les trajectoires ni la météo n'alimentent le modèle ou le dashboard. Le code d'ingestion reste dans `src/`
(`fetch_weather_history`, `fetch_metar_live`, `generate_trajectories`, `load.py`).

- Météo : les conditions à l'altitude de vol figurent déjà dans `W`. La météo de surface à Toulouse n'a aucun lien
  avec ces moteurs simulés : l'ajouter reviendrait à une association arbitraire.
- Trajectoires simulées : générées à partir de la classe de vol et de l'altitude, elles n'apportent aucune information
  nouvelle au modèle.
- Trajectoires ADS-B réelles : associer des vols réels à des moteurs simulés introduirait un biais.
- Dashboard : une carte laisserait croire à des vols observés, alors que ces données sont simulées.

## Conséquences
- Le modèle ne dépend que de N-CMAPSS, et le dashboard que des Parquet exportés (ADR-009).
- PostGIS, GeoPandas et les API météo ne servent qu'à la chaîne ETL optionnelle (ADR-001).
- La carte des trajectoires et le streaming ADS-B figurent dans les pistes non retenues du README (ADR-006).

## Sources
- `src/extract.py`, `src/transform.py`, `src/load.py`.
- `ROADMAP.md`, section « Architecture météo ».
- ADR-001, ADR-006, ADR-009.
