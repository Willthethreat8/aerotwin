"""Tests unitaires de src/train.py — pas de .h5, pas de MLflow, juste les
fonctions pures (cross_validate, _metrics) sur des données synthétiques.
"""
import numpy as np
import pandas as pd
import pytest

from src import train

FAST_PARAMS = {"n_estimators": 10, "max_depth": 2, "random_state": 0}


def test_metrics_perfect_prediction_is_zero_error():
    y_true = pd.Series([10.0, 20.0, 30.0])
    y_pred = np.array([10.0, 20.0, 30.0])

    result = train._metrics(y_true, y_pred)

    assert result["rmse"] == pytest.approx(0.0)
    assert result["mae"] == pytest.approx(0.0)
    assert result["r2"] == pytest.approx(1.0)


def test_cross_validate_one_fold_per_group():
    """3 moteurs -> leave-one-unit-out doit produire exactement 3 folds."""
    X = pd.DataFrame({"f1": [0.0, 1.0, 2.0, 3.0, 4.0, 5.0], "f2": [5.0, 4.0, 3.0, 2.0, 1.0, 0.0]})
    y = pd.Series([0.0, 1.0, 2.0, 3.0, 4.0, 5.0])
    groups = pd.Series([1, 1, 2, 2, 3, 3])

    result = train.cross_validate(X, y, groups, params=FAST_PARAMS)

    assert len(result["per_fold"]) == 3
    assert set(result["mean"].keys()) == {"rmse", "mae", "r2"}
    assert result["mean"]["rmse"] >= 0.0
