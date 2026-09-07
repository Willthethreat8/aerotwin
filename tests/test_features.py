"""Tests unitaires de src/features.py — DataFrames synthétiques, pas de .h5."""
import pandas as pd
import pytest

from src import features


@pytest.fixture
def mini_cycles() -> pd.DataFrame:
    """3 moteurs, 2 cycles chacun — déjà agrégé au niveau cycle."""
    return pd.DataFrame({
        "unit": [1, 1, 2, 2, 3, 3],
        "cycle": [1, 2, 1, 2, 1, 2],
        "Fc": [1, 1, 2, 2, 3, 3],
        "hs": [1, 1, 1, 1, 1, 0],
        "alt_mean": [8000.0, 8100.0, 9000.0, 9100.0, 10000.0, 10100.0],
        "RUL": [50, 49, 80, 79, 20, 19],
    })


def test_encode_fc_produces_fixed_columns(mini_cycles):
    encoded = features.encode_fc(mini_cycles.drop(columns=["unit", "cycle", "hs", "RUL"]))

    assert {"Fc_1", "Fc_2", "Fc_3"}.issubset(encoded.columns)
    assert "Fc" not in encoded.columns
    # Un seul Fc actif par ligne
    assert (encoded[["Fc_1", "Fc_2", "Fc_3"]].sum(axis=1) == 1).all()


def test_split_features_target_excludes_ids(mini_cycles):
    X, y, groups = features.split_features_target(mini_cycles)

    assert "unit" not in X.columns
    assert "cycle" not in X.columns
    assert "hs" not in X.columns
    assert "RUL" not in X.columns
    assert list(y) == [50, 49, 80, 79, 20, 19]
    assert list(groups) == [1, 1, 2, 2, 3, 3]


def test_cap_rul_clips_above_threshold():
    y = pd.Series([10, 50, 125, 200, 300])

    capped = features.cap_rul(y, cap=125)

    assert capped.max() == 125
    assert capped.iloc[0] == 10  # inchangée sous le plafond
