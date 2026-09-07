# Phase 3 — ETL production (N-CMAPSS)

La phase 3 vise à sortir les notebooks en code exploitable, réutilisable et traçable.
Le point d'entrée est le dataset NASA N-CMAPSS, qui contient des profils de vol réalistes
et des conditions de vol complètes (altitude, Mach, T2, etc.).

## Objectif

- Lire le HDF5 sans charger tout le fichier en mémoire
- Normaliser les colonnes et les variables N-CMAPSS
- Agréger les mesures par moteur (`unit`) et par cycle
- Ajouter des rolling features pour préparer la phase 4 ML
- Enregistrer les données dans PostGIS si la base est disponible

## Données de référence

Le dataset est fourni dans :

- `data/raw/ncmapss/N-CMAPSS_DS01-005.h5`

Les colonnes principales sont :

- `unit` : identifiant du moteur
- `cycle` : cycle de vol
- `Fc` : classe ou type de vol
- `hs` : health state
- `RUL` : remaining useful life fournie par le dataset
- `alt`, `Mach`, `TRA`, `T2` : conditions de vol
- `X_s` : capteurs physiques

## Pipeline

### 1. Extraction

Le module `src/extract.py` lit le HDF5 avec `h5py`, reconstruit les DataFrames
et renvoie un DataFrame à la fois lisible et prêt à être transformé.

### 2. Transformation

Le module `src/transform.py` réalise :

- l'agrégation par `(unit, cycle)`
- la suppression des colonnes constantes
- les rolling features par moteur
- la génération d'une trajectoire syntaxique par moteur pour l'outil de visualisation

### 3. Chargement

Le module `src/load.py` connecte une base PostGIS via SQLAlchemy et insère les
DataFrames. Cela permet de passer d'un environnement local à un environnement cloud
avec un seul changement de configuration.

## Exécution

```bash
cd /chemin/vers/aerotwin_project
source venv/bin/activate
python -m src.pipeline --dataset data/raw/ncmapss/N-CMAPSS_DS01-005.h5 --split dev
```

Ouverture possible depuis un script Python :

```python
from src.pipeline import run_phase3_pipeline

summary = run_phase3_pipeline(
    dataset_path="data/raw/ncmapss/N-CMAPSS_DS01-005.h5",
    split="dev",
)
print(summary)
```

## Points de vigilance

- Les nombres de lignes sont élevés : le dataset est volumineux et nécessite une
  agrégation rapide au niveau cycle.
- Les conditions de vol doivent être conservées dans le pipeline et nagent au cœur
  de la qualité métier.
- Les notebooks restent utiles pour l'exploration et la validation locale, mais
  le code de production est désormais dans `src/`.
