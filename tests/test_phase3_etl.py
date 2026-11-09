import pandas as pd
import pytest

from src.extract import read_ncmapss, resolve_ncmapss_path
from src.transform import add_rolling_features, aggregate_to_cycles, drop_constant_columns


def test_read_ncmapss_extracts_expected_columns():
    df = read_ncmapss("DS01", split="dev")

    required = {"unit", "cycle", "Fc", "hs", "RUL"}
    assert required.issubset(df.columns)
    assert len(df) > 0
    assert df["unit"].dtype.kind in "iu"
    assert (df["ds_id"] == "DS01").all()
    assert (df["fault_mode"] == "HPT").all()


def test_resolve_ncmapss_path_by_pattern(tmp_path):
    (tmp_path / "N-CMAPSS_DS03-012.h5").touch()
    assert resolve_ncmapss_path("DS03", tmp_path).name == "N-CMAPSS_DS03-012.h5"
    with pytest.raises(FileNotFoundError):
        resolve_ncmapss_path("DS04", tmp_path)


def test_aggregate_to_cycles_reduces_rows_and_keeps_structure():
    raw = read_ncmapss("DS01", split="dev")
    cycle_df = aggregate_to_cycles(raw)
    cycle_df = drop_constant_columns(cycle_df)

    assert len(cycle_df) > 0
    assert {"ds_id", "fault_mode", "unit", "cycle", "RUL"}.issubset(cycle_df.columns)
    assert len(cycle_df) < len(raw)


def test_rolling_features_are_added():
    raw = read_ncmapss("DS01", split="dev")
    cycle_df = aggregate_to_cycles(raw)
    cycle_df = drop_constant_columns(cycle_df)
    columns = [col for col in cycle_df.columns if col.endswith("_mean")][:3]

    enriched = add_rolling_features(cycle_df, columns=columns, window=3)
    for col in columns:
        assert f"{col}_rolling_mean" in enriched.columns
        assert f"{col}_rolling_std" in enriched.columns
