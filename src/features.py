"""Feature engineering pour le baseline ML (Phase 4.1).

Sépare la construction des features ML de l'ETL (src/transform.py) : ici on
fige la liste de colonnes attendue par le modèle, indépendamment de ce que
drop_constant_columns garderait dynamiquement (qui peut varier entre dev/test).
"""
from __future__ import annotations

import pandas as pd

from src import config
from src.extract import read_ncmapss
from src.transform import add_rolling_features, aggregate_to_cycles

# Conditions de vol N-CMAPSS (groupe W) — cf. ROADMAP.md, la colonne est "alt", pas "altitude"
FLIGHT_CONDITION_COLS = ["alt", "Mach", "TRA", "T2"]
# Capteurs physiques (groupe X_s) — X_v et T exclus : data leakage (cf. ROADMAP.md)
SENSOR_COLS = ["T24", "T30", "T48", "T50", "P15", "P2", "P21", "P24", "Ps30", "P40", "P50", "Nf", "Nc", "Wf"]
FC_CATEGORIES = [1, 2, 3]


def build_cycle_features(split: str, dataset_path: str = config.NCMAPSS_DS01_PATH) -> pd.DataFrame:
    """Lit un split N-CMAPSS et renvoie une ligne par (unit, cycle) avec les features 4.1."""
    raw = read_ncmapss(path=dataset_path, split=split)
    cycles = aggregate_to_cycles(raw)

    rolling_cols = [f"{col}_mean" for col in SENSOR_COLS]
    cycles = add_rolling_features(cycles, columns=rolling_cols, window=config.ROLLING_WINDOW)
    return cycles


def encode_fc(X: pd.DataFrame) -> pd.DataFrame:
    """One-hot Fc sur des catégories fixes, pour garder les mêmes colonnes entre dev et test."""
    fc = pd.Categorical(X["Fc"], categories=FC_CATEGORIES)
    dummies = pd.get_dummies(fc, prefix="Fc").astype(int)
    return pd.concat([X.drop(columns=["Fc"]), dummies], axis=1)


def split_features_target(cycles: pd.DataFrame) -> tuple[pd.DataFrame, pd.Series, pd.Series]:
    """Sépare features / cible RUL / groupes moteur (pour un split GroupKFold sans leakage)."""
    exclude = {"unit", "cycle", "hs", "RUL"}
    feature_cols = [col for col in cycles.columns if col not in exclude]
    X = encode_fc(cycles[feature_cols])
    y = cycles["RUL"]
    groups = cycles["unit"]
    return X, y, groups


def cap_rul(y: pd.Series, cap: int = 125) -> pd.Series:
    """Plafonne la RUL — pratique standard C-MAPSS/N-CMAPSS pour stabiliser l'entraînement."""
    return y.clip(upper=cap)
