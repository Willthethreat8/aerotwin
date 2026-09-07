"""Tests unitaires de src/transform.py — version N-CMAPSS.

Principe : on fabrique de PETITS DataFrames en mémoire dont on connaît
le résultat attendu à la main. Pas de fichier .h5, pas de réseau,
pas de base de données -> les tests tournent en <1s, partout, toujours.
"""
import pandas as pd
import pytest

from src import transform


@pytest.fixture
def mini_1hz() -> pd.DataFrame:
    """2 unités, 2 cycles chacune, 3 secondes par cycle — format 1 Hz."""
    return pd.DataFrame({
        "unit":  [1]*6 + [2]*6,
        "cycle": [1, 1, 1, 2, 2, 2] * 2,
        "Fc":    [1]*6 + [3]*6,
        "hs":    [1]*12,
        "alt":   [1000, 2000, 3000, 1100, 2100, 3100] * 2,
        "T40":   [1400.0, 1410.0, 1420.0, 1450.0, 1460.0, 1470.0,
                  1300.0, 1310.0, 1320.0, 1350.0, 1360.0, 1370.0],
        "RUL":   [99, 99, 99, 98, 98, 98, 49, 49, 49, 48, 48, 48],
    })


# --- EXEMPLE COMPLET : sers-toi de ce modèle pour écrire les autres ---
def test_aggregate_to_cycles_shape(mini_1hz):
    """12 lignes 1 Hz -> 4 lignes (2 unités x 2 cycles)."""
    result = transform.aggregate_to_cycles(mini_1hz)

    assert len(result) == 4
    # La RUL du cycle est conservée telle quelle
    row = result[(result["unit"] == 1) & (result["cycle"] == 1)]
    assert row["RUL"].iloc[0] == 99
    # La fonction ne doit PAS avoir muté l'entrée
    assert len(mini_1hz) == 12


# --- À TOI : les tests suivants, sur le même modèle ---

def test_aggregate_computes_mean(mini_1hz):
    """T40 moyen de (unit=1, cycle=1) == 1410.0.
    Vérifie aussi qu'une colonne de type T40_std existe."""
    result = transform.aggregate_to_cycles(mini_1hz)

    row = result[(result["unit"] == 1) & (result["cycle"] == 1)]
    assert row["T40_mean"].iloc[0] == pytest.approx(1410.0)
    assert "T40_std" in result.columns


def test_drop_constant_columns(mini_1hz):
    """La colonne hs (constante) disparaît, alt reste."""
    result = transform.drop_constant_columns(mini_1hz)

    assert "hs" not in result.columns
    assert "alt" in result.columns


def test_rolling_does_not_leak_between_units():
    """Le test qui impressionne en entretien : la rolling mean du
    cycle 1 de l'unité 2 ne doit PAS être influencée par l'unité 1.
    Sans le groupby("unit"), une fenêtre de 3 sur le cycle 1 de l'unité 2
    inclurait les 2 dernières valeurs (à 100.0) de l'unité 1."""
    df = pd.DataFrame({
        "unit":  [1, 1, 1, 1, 1, 2, 2, 2],
        "cycle": [1, 2, 3, 4, 5, 1, 2, 3],
        "val":   [100.0, 100.0, 100.0, 100.0, 100.0, 1.0, 1.0, 1.0],
    })

    result = transform.add_rolling_features(df, columns=["val"], window=3)

    row = result[(result["unit"] == 2) & (result["cycle"] == 1)]
    assert row["val_rolling_mean"].iloc[0] == pytest.approx(1.0)
    assert row["val_rolling_std"].iloc[0] == pytest.approx(0.0)


def test_generate_trajectories_fc_length():
    """Une unité Fc=3 (long courrier) produit une trajectoire plus longue
    (au sens géométrique) qu'une unité Fc=1. + reproductibilité : même
    seed -> géométries identiques."""
    flight_summary = pd.DataFrame({
        "unit": [1, 2],
        "Fc": [1, 3],
        "altitude_mean": [8000.0, 8000.0],
    })

    gdf = transform.generate_trajectories(flight_summary, n_points=50, seed=42)

    length_fc1 = gdf[gdf["unit"] == 1].geometry.iloc[0].length
    length_fc3 = gdf[gdf["unit"] == 2].geometry.iloc[0].length
    assert length_fc3 > length_fc1

    gdf_repeat = transform.generate_trajectories(flight_summary, n_points=50, seed=42)
    for unit in flight_summary["unit"]:
        coords_a = list(gdf[gdf["unit"] == unit].geometry.iloc[0].coords)
        coords_b = list(gdf_repeat[gdf_repeat["unit"] == unit].geometry.iloc[0].coords)
        assert coords_a == coords_b
