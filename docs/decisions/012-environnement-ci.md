# ADR-012 : MLflow local, Python 3.13, dépendances figées, CI sur fixtures
Date : 2026-11-10
Statut : acceptée

## Contexte
Tout chiffre publié doit être reproductible par une commande documentée. Le venv recréé sans versions figées a
remplacé `xgboost` 2.1.4 par 3.4.1 et fait passer le RMSE test de DS01 de 11.79 à 11.89. La version de MLflow installée
refuse par défaut le stockage `./mlruns`. Python 3.11, prévu pour la CI, n'était pas installé localement. Les `.h5`
ne sont pas dans le dépôt, alors que certains tests les lisaient.

## Options envisagées
- Suivi des expériences : stockage local en fichiers, migration vers une base SQLite, ou abandon de MLflow.
- Python : 3.11 (prévu, absent de la machine), 3.13, ou 3.14 (installé, sans vérification de compatibilité).
- Dépendances : versions libres, dépendances directes figées, ou verrouillage complet des dépendances transitives.
- CI : téléchargement des `.h5` à chaque exécution (environ 16 Go), ou tests sur fixtures uniquement.

## Décision
- MLflow reste en stockage local dans `mlruns/`, ignoré par Git. `MLFLOW_ALLOW_FILE_STORE=true` est défini dans
  `src/train.py` pour conserver ce mode. Un projet solo en clôture n'a pas besoin d'un serveur de suivi.
- Python 3.13 partout : développement, CI et déploiement.
- Dépendances directes figées dans `requirements.txt`, et quatre paquets figés dans `dashboard/requirements.txt`.
- CI GitHub Actions à chaque push : Pytest sur Python 3.13, avec une petite fixture HDF5 synthétique et les Parquet
  versionnés, sans aucun téléchargement.

## Conséquences
- Les chiffres de `docs/resultats.md` correspondent aux versions figées. Les dépendances transitives ne sont pas
  verrouillées, un écart reste donc possible à terme.
- Le stockage local de MLflow est en mode maintenance : à revoir si le projet reprenait, ce qui n'est pas prévu.
- Streamlit Community Cloud propose Python 3.12 par défaut : Python 3.13 doit être choisi au déploiement.
- La CI vérifie le code, les formats et l'absence de fuite, mais ne rejoue pas l'entraînement sur les données réelles.

## Sources
- `requirements.txt`, `dashboard/requirements.txt`, `.github/workflows/tests.yml`, `tests/test_phase3_etl.py`.
- `docs/CHRONOLOGIE.md`, ADR-006, ADR-009.
