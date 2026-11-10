"""Tests de l'export du dashboard : données synthétiques, puis Parquet versionnés (jamais de .h5)."""
import numpy as np
import pandas as pd
import pytest

from src import config, export_dashboard

CYCLE_COLS = {"ds_id", "fault_mode", "unit", "cycle", "split", "hs", "rul_true", "rul_pred", "in_fleet"}


def _result(ds_id: str) -> dict:
    predictions = pd.DataFrame({
        "ds_id": ds_id, "fault_mode": config.NCMAPSS_FAULT_MODES[ds_id], "unit": [1, 2], "cycle": [1, 1], "hs": [1, 0],
        "rul_true": [10.0, 5.0], "rul_pred": [9.0, 7.0], "split": ["cv", "test"],
    })
    per_unit = pd.DataFrame({"split": ["cv", "test"], "unit": [1, 2], "n_cycles": [1, 1], "rmse": [1.0, 2.0], "mae": [1.0, 2.0]})
    return {
        "predictions": predictions, "per_unit": per_unit, "summary": {"cv_rmse_mean": 1.0, "test_rmse_mean": 2.0},
        "importance": pd.Series([0.7, 0.3], index=["T50_mean", "alt_mean"]),
    }


def test_build_tables_format():
    tables = export_dashboard.build_tables({"DS01": _result("DS01"), "DS02": _result("DS02")})

    assert CYCLE_COLS <= set(tables["cycles"].columns)
    assert set(tables["cycles"]["split"]) == {"dev", "test"}
    assert set(tables["per_unit"]["split"]) == {"dev", "test"}
    assert list(tables["importance"].columns[:2]) == ["feature", "importance"]
    for table in tables.values():
        assert table.set_index("ds_id")["in_fleet"].groupby(level=0).first().to_dict() == {"DS01": True, "DS02": False}


def test_exported_parquet_is_consistent():
    path = export_dashboard.OUT_DIR / "cycles.parquet"
    if not path.exists():
        pytest.skip("export absent")
    cycles = pd.read_parquet(path)
    per_unit = pd.read_parquet(export_dashboard.OUT_DIR / "per_unit.parquet")

    assert CYCLE_COLS <= set(cycles.columns)
    assert not cycles[list(CYCLE_COLS)].isna().any().any()
    assert not cycles.duplicated(["ds_id", "unit", "cycle"]).any()
    assert cycles.loc[cycles["in_fleet"], ["ds_id", "unit"]].drop_duplicates().shape[0] == 65

    # Les métriques exportées se recalculent à partir des prédictions exportées
    errors = cycles["rul_true"] - cycles["rul_pred"]
    rmse = np.sqrt((errors ** 2).groupby([cycles["ds_id"], cycles["split"], cycles["unit"]]).mean())
    exported = per_unit.set_index(["ds_id", "split", "unit"])["rmse"]
    assert exported.sort_index().to_numpy() == pytest.approx(rmse.sort_index().to_numpy())
