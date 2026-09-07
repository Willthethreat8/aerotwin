import pandas as pd

from src.extract import read_ncmapss
from src.transform import add_rolling_features, aggregate_to_cycles, drop_constant_columns


def test_read_ncmapss_extracts_expected_columns():
    df = read_ncmapss("data/raw/ncmapss/N-CMAPSS_DS01-005.h5", split="dev")

    required = {"unit", "cycle", "Fc", "hs", "RUL"}
    assert required.issubset(df.columns)
    assert len(df) > 0
    assert df["unit"].dtype.kind in "iu"


def test_aggregate_to_cycles_reduces_rows_and_keeps_structure():
    raw = read_ncmapss("data/raw/ncmapss/N-CMAPSS_DS01-005.h5", split="dev")
    cycle_df = aggregate_to_cycles(raw)
    cycle_df = drop_constant_columns(cycle_df)

    assert len(cycle_df) > 0
    assert {"unit", "cycle", "RUL"}.issubset(cycle_df.columns)
    assert len(cycle_df) < len(raw)


def test_rolling_features_are_added():
    raw = read_ncmapss("data/raw/ncmapss/N-CMAPSS_DS01-005.h5", split="dev")
    cycle_df = aggregate_to_cycles(raw)
    cycle_df = drop_constant_columns(cycle_df)
    columns = [col for col in cycle_df.columns if col.endswith("_mean")][:3]

    enriched = add_rolling_features(cycle_df, columns=columns, window=3)
    for col in columns:
        assert f"{col}_rolling_mean" in enriched.columns
        assert f"{col}_rolling_std" in enriched.columns
