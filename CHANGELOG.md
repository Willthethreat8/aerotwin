# Changelog

Les changements notables du projet sont consignés dans ce fichier.

Le format suit [Keep a Changelog](https://keepachangelog.com/fr/1.1.0/). Le contenu ci-dessous constituera la version `1.0` une fois le tag posé.

## [Unreleased]

### Added

- Infrastructure Docker PostGIS et pgAdmin, ingestion des trajectoires simulées et de la météo historique (mars 2026).
- ETL `src/` sur N-CMAPSS : extraction HDF5, agrégation par cycle, chargement PostGIS.
- Script `scripts/download_ncmapss.py` : téléchargement officiel, extraction sélective, tailles et SHA-256 dans `docs/data.md`.
- Fichiers DS03 à DS07, puis DS02 uniquement pour la comparaison à la littérature.
- Un modèle XGBoost par fichier (`python -m src.train --ds DS03`, `python -m src.train --all`), suivi MLflow local.
- Métriques par moteur et écart-type entre moteurs, en CV et en test, dans `docs/resultats.md`.
- Paragraphe « Situation par rapport à la littérature » dans `docs/resultats.md`.
- Export `src/export_dashboard.py` vers `data/dashboard/*.parquet`.
- Dashboard Streamlit à trois pages (Flotte, Moteur, Modèle) et `dashboard/requirements.txt` pour Community Cloud.
- CI GitHub Actions : Pytest sur Python 3.13 à chaque push, sur fixtures uniquement.
- Documentation : ADR-001 à ADR-010, `docs/CHRONOLOGIE.md`, `docs/data.md`, captures dans `docs/img/`.

### Changed

- Pivot de C-MAPSS FD001 vers N-CMAPSS (ADR-002).
- Périmètre réduit : phases 5 et 6 ramenées à une CI Pytest et à un dashboard de trois pages (ADR-006).
- Jeux de données : l'ADR-007 est remplacée par l'ADR-010, qui ajoute DS02.
- Statuts de la page Flotte calculés sur une RUL prudente, RUL prédite moins le RMSE test du fichier (ADR-009).
- Dépendances directes figées dans `requirements.txt`, environnement sur Python 3.13.
- README réécrit, ROADMAP marquée terminée.

### Removed

- Plafond RUL à 125, sans effet sur ces données (ADR-008), et la comparaison capped / uncapped.
- Notebooks 01 à 04 et traitement de FD001 (ADR-002).
- Squelette Prefect `src/pipelines/`, jamais implémenté.
- Phases 7 à 9 de la feuille de route : streaming, API et cloud, IA générative (ADR-006).

### Fixed

- Rolling features calculées sur la cible `RUL` dans `src/pipeline.py`.
- Nom de colonne `alt` au lieu de `altitude`.
- Référence « RMSE 36.89 » retirée : elle venait d'un projet FD001 en split aléatoire, non comparable.
- `.gitignore` complété.
