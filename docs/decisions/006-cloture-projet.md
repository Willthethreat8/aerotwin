# ADR-006 : Abandon des phases 5 à 9 et clôture du projet
Date : 2026-11-09
Statut : acceptée

## Contexte
La ROADMAP prévoyait neuf phases : CI/CD, dashboard, streaming ADS-B (Kafka, Spark, lakehouse), API FastAPI et
déploiement cloud, couche GenAI. L'audit du 2026-11-06 a montré un périmètre trop large pour un projet solo,
des résultats à consolider (plafond RUL sans effet, écart test / CV) et des commits non poussés.

## Options envisagées
- Poursuivre la ROADMAP complète.
- Ramener le projet à son cœur (pronostic RUL sur N-CMAPSS), le finir proprement et le clôturer.

## Décision
Clôturer après : extension à six fichiers N-CMAPSS, modèle XGBoost finalisé avec métriques par moteur, export
Parquet, dashboard Streamlit, CI Pytest minimale, documentation. Les phases 7 (streaming), 8 (API, cloud) et 9
(GenAI) sont abandonnées. Les phases 5 et 6 sont réduites à une CI Pytest et un dashboard de trois pages.
Le propriétaire réoriente son portfolio et ne prépare aucune suite.

## Conséquences
- Trajectoires simulées et météo restent dans le dépôt mais sortent du dashboard.
- Le squelette Prefect est retiré ou marqué comme abandonné.
- Les idées non retenues sont listées dans le README, sans code. Tag `v1.0` en fin de projet.

## Sources
- `ROADMAP.md`, audit du 2026-11-06.
