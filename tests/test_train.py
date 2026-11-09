"""Tests de src/train.py sur données synthétiques (pas de .h5, pas de MLflow)."""
import numpy as np
import pandas as pd
import pytest

from src import train

FAST_PARAMS = {"n_estimators": 20, "max_depth": 2, "random_state": 0}


def test_cross_validate_is_out_of_fold():
    # Chaque moteur a une cible propre, identifiable par f1 : un modèle qui l'a vu la retrouve,
    # un modèle hors échantillon non.
    X = pd.DataFrame({"f1": [0.0, 0.0, 1.0, 1.0, 2.0, 2.0]})
    y = pd.Series([10.0, 10.0, 50.0, 50.0, 90.0, 90.0])
    groups = pd.Series([1, 1, 2, 2, 3, 3])

    oof = train.cross_validate(X, y, groups, params=FAST_PARAMS)

    assert oof.shape == (6,)
    assert np.abs(oof - y.to_numpy()).min() > 1.0


def test_per_unit_metrics_and_summary():
    predictions = pd.DataFrame({
        "split": ["cv", "cv", "cv", "cv", "test", "test"],
        "unit": [1, 1, 2, 2, 3, 3],
        "rul_true": [10.0, 20.0, 10.0, 20.0, 5.0, 5.0],
        "rul_pred": [10.0, 20.0, 14.0, 24.0, 8.0, 2.0],
    })

    per_unit = train.per_unit_metrics(predictions)
    summary = train.summarize(per_unit, predictions)

    assert per_unit.set_index("unit").loc[2, "rmse"] == pytest.approx(4.0)
    assert per_unit.set_index("unit").loc[1, "mae"] == pytest.approx(0.0)
    assert summary["cv_rmse_mean"] == pytest.approx(2.0)
    assert summary["cv_rmse_std"] == pytest.approx(np.std([0.0, 4.0], ddof=1))
    assert summary["test_rmse_all_cycles"] == pytest.approx(3.0)
