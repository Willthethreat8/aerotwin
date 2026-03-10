# Journal du projet AeroTwin

## Structure des dossiers
* **`data/`** : Contient les données de base (fichiers de la NASA, extractions météo).
* **`src/`** : Contient le code source (les scripts Python pour l'ingestion, le scraping et l'IA).
* **`notebooks/`** : Contient les brouillons d'analyse et d'exploration de données (fichiers Jupyter).
* **`tests/`** : Contient les scripts permettant de vérifier automatiquement que le code fonctionne.

## Explication de l'infrastructure (docker-compose.yml)
* **`version: '3.8'`** : Version du langage de configuration Docker.
* **`services:`** : Déclare les machines virtuelles à créer (`postgis` et `pgadmin`).
* **`image:`** : Indique le logiciel de base à télécharger (ex: l'image officielle PostGIS).
* **`environment:`** : Définit les variables (identifiants, mots de passe, nom de la base).
* **`ports:`** : Relie un port du Mac au port du conteneur (ex: 5432:5432).
* **`volumes:`** : Sauvegarde les données de manière permanente sur le disque dur.
* **`depends_on:`** : Définit l'ordre de démarrage (pgadmin s'allume après postgis).


## Dictionnaire de données (Dataset NASA CMAPSS)
Les fichiers de données brutes se présentent sous la forme de fichiers textes avec 26 colonnes de nombres, séparées par des espaces. Chaque ligne représente un cycle opérationnel[cite: 185]. Voici la cartographie exacte pour notre futur script d'ingestion :

* **Colonne 1** : `engine_id` (Numéro de l'unité / unit number).
* **Colonne 2** : `cycle` (Temps de vol exprimé en cycles / time, in cycles).
* **Colonnes 3 à 5** : `setting_1` à `setting_3` (Les 3 paramètres opérationnels ayant un effet sur les performances / operational setting ).
* **Colonnes 6 à 26** : `sensor_1` à `sensor_21` (Les relevés des 21 capteurs / sensor measurement  ).

**Note métier :** Dans le jeu de données d'entraînement, le moteur démarre dans un état normal, développe un défaut (usure), et l'anomalie grandit jusqu'à la panne complète du système.

## Schéma de la Base de Données (PostgreSQL / PostGIS)
Le schéma de la base `aerotwin_db` est structuré autour de 5 tables principales :
1. **`engines`** : Référentiel de la flotte.
2. **`sensor_readings`** : Historique des capteurs de la NASA (Couche Batch).
3. **`flight_trajectories`** : Tracés historiques des vols.
4. **`weather_metar`** : Historique des relevés météo.
5. **`live_positions`** : Suivi GPS en temps réel.

**Concepts SQL clés appliqués :**
* `CREATE EXTENSION postgis;` : Indispensable pour stocker et analyser des coordonnées géographiques.
* `PRIMARY KEY` et `SERIAL` : Définissent un identifiant unique pour chaque ligne, auto-incrémenté.
* `REFERENCES` (Clé étrangère) : Sécurise la base en empêchant, par exemple, d'ajouter un relevé de capteur pour un moteur qui n'existe pas dans la table `engines`.
* `geometry(LINESTRING, 4326)` et `geometry(POINT, 4326)` : Formats spatiaux pour stocker respectivement des lignes (trajectoires) et des points (positions instantanées) selon le standard GPS mondial (WGS 84).

## Outils d'exploration des données
* **Jupyter Notebook** : C'est une interface web interactive qui permet de coder en Python. Au lieu d'exécuter un long script d'un seul coup, Jupyter découpe le code en "cellules" indépendantes. C'est l'outil de référence en Data Science car il permet d'afficher les résultats (tableaux, graphiques) directement sous le code, ce qui est idéal pour l'exploration visuelle des données.
* **Pandas** : C'est la bibliothèque Python reine pour la manipulation de données. Elle transforme nos fichiers textes bruts en "DataFrames" (des tableaux structurés avec des lignes et des colonnes, similaires à Excel mais manipulables par le code).