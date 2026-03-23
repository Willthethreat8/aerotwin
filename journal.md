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



## Phase 1 : Décision technique sur les trajectoires GPS

**Problème constaté :**
Le dataset C-MAPSS de la NASA contient la télémétrie de l'usure des moteurs, mais aucune coordonnée spatiale (secret industriel). Les données de vols réels (ex: OpenSky) fournissent des trajectoires exactes, mais aucune donnée de maintenance. 

# Journal de bord - Projet AeroTwin

## Phase 1 : Justification du choix de simulation spatiale vs. Données réelles

**Le Problème : Le paradoxe de la confidentialité spatiale**
Les données de télémétrie moteur (températures, pressions, vibrations) couplées à des coordonnées GPS exactes sont couvertes par le secret industriel (Airbus, Safran, compagnies aériennes). Le dataset NASA C-MAPSS est la référence absolue pour modéliser la dégradation, mais il a été totalement anonymisé et dépouillé de sa dimension spatio-temporelle. 

**Pourquoi nous avons écarté la jointure avec des données radar réelles (OpenSky / ADS-B) :**

1. **Risque de destruction du modèle Machine Learning (XGBoost) :**
   Si nous associons arbitrairement une vraie trajectoire (ex: un vol Toulouse-Montréal dans le froid) aux données d'usure de la NASA, nous allons introduire un biais massif. L'usure du moteur dans le dataset de la NASA est le résultat de conditions opérationnelles précises (bien que masquées). Si l'on force XGBoost à apprendre une fausse corrélation entre la météo scrapée sur une vraie trajectoire et une dégradation qui n'a rien à voir, le modèle sera confus et ses prédictions seront faussées.

2. **La contrainte d'alignement des cycles (ex: Moteur à 192 cycles) :**
   La NASA compte la durée de vie en "cycles" (1 cycle = 1 vol). Si le moteur #1 tombe en panne exactement au bout de 192 cycles, il faudrait trouver un historique de vol réel qui correspond parfaitement à cette séquence sans briser la logique de temps. La simulation nous permet de générer de manière chirurgicale exactement 192 trajectoires pour ce moteur précis.

3. **La dette technique du nettoyage (Données très bruitées) :**
   Les historiques de vols radar open source (ADS-B) sont notoirement bruités : pertes de signal au-dessus des océans, points GPS aberrants, altitudes erronées. Utiliser ces données réelles imposerait un pipeline de nettoyage lourd et fastidieux qui nous éloignerait de l'objectif principal du projet : démontrer la maîtrise d'une architecture Lambda avec PostGIS et du streaming temps réel.

**Conclusion (Choix V1) :**
Nous optons pour la génération de trajectoires synthétiques avec `GeoPandas`. Cela garantit l'intégrité de notre modèle XGBoost tout en permettant de valider toute notre infrastructure spatiale (ingestion de `LineString`, PostGIS, visualisation 3D).

**Perspectives d'évolution (V2) : N-CMAPSS et OpenSky**
Pour accroître le réalisme physique du modèle prédictif, une V2 pourrait s'appuyer sur le dataset N-CMAPSS (profils de vols complets, données massives en HDF5). Ces données pourraient être fusionnées avec des historiques radar réels (OpenSky Network) via des techniques de *Dynamic Time Warping*. Ce choix a été écarté pour la V1 afin de concentrer l'effort technique sur le déploiement de l'Architecture Lambda (Kafka, Airflow, PostGIS).


##  Collecte de la météo (METAR)

**Initialement prévu : Web Scraping (BeautifulSoup)**
L'idée était d'extraire les bulletins météo aéronautiques (METAR) depuis les pages HTML de la NOAA.
* **Limites constatées :** Fragilité face aux changements de structure HTML du site source et instabilité des serveurs FTP historiques.

**Pivot technique : API REST (Aviation Weather Center)**
Nous avons migré vers l'utilisation de l'API officielle de la NOAA (Aviation Weather Center API).
* **Avantages :** Données reçues au format JSON structuré, plus grande fiabilité, et respect des standards modernes de développement.
* **Implémentation :** Utilisation de la bibliothèque `requests` pour l'appel API et de `metar` pour le parsing des codes aéronautiques complexes.
* **Résultat :** Ingestion d'un historique de 24h dans PostGIS pour corréler l'usure moteur avec les conditions environnementales réelles (température, pression, vent).

## Tests et Qualité (Pytest)
Mise en place de tests unitaires pour sécuriser le pipeline :
* Validation du décodage des chaînes METAR (extraction correcte des températures/pressions).
* Validation de la structure géométrique des trajectoires (vérification des types `LineString`).
* Validation de l'intégrité des DataFrames avant ingestion (schéma attendu par XGBoost).