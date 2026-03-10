# Projet AeroTwin ✈️

**Plateforme de Maintenance Prédictive Aéronautique — Architecture Lambda Spatiale** [cite: 18, 19]

## 🎯 Objectif
Construire une plateforme end-to-end de surveillance de l'usure des moteurs d'une flotte d'avions au départ de Toulouse[cite: 28]. 
Le système croise des données de capteurs en temps réel, des trajectoires géospatiales et la météo locale pour prédire la durée de vie restante (RUL - Remaining Useful Life) et alerter via une carte 3D[cite: 28, 46, 47].

## 🏗️ Stack Technique
* **Infrastructure & Stockage :** Docker, PostGIS 
* **Batch Layer (Données Froides) :** Airflow, dbt 
* **Speed Layer (Temps Réel) :** Kafka, Spark Structured Streaming
* **Machine Learning & MLOps :** XGBoost, MLflow 
* **Serving Layer (API & Viz) :** FastAPI, Kepler.gl, Grafana 

## 🚀 Plan de Développement & Avancement
*  **Phase 0 : Data Discovery & Setup** (Infrastructure Docker, PostGIS, initialisation du repo) 
* **Phase 1 : Fondation Spatiale** (Nettoyage C-MAPSS, trajectoires simulées, scraping METAR) 
*  **Phase 2 : Usine Automatisée** (Orchestration Airflow, transformations dbt) 
*  **Phase 3 : Intelligence Artificielle** (Entraînement XGBoost, MLflow, API FastAPI) 
*  **Phase 4 : Temps Réel** (Flux Kafka, Spark Streaming, détection d'anomalies) 
*  **Phase 5 : Tour de Contrôle 3D & Monitoring** (Carte Kepler.gl, Dashboards Grafana) 