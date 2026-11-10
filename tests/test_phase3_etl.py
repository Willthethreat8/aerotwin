import h5py
import numpy as np
import pytest

from src.extract import read_ncmapss, resolve_ncmapss_path
from src.transform import add_rolling_features, aggregate_to_cycles, drop_constant_columns


@pytest.fixture
def mini_h5(tmp_path):
    """Fichier au format N-CMAPSS : 2 moteurs, 3 cycles de 4 secondes, avec les groupes X_v et T à ne pas lire."""
    n = 24
    rng = np.random.default_rng(0)
    groupes = {
        "W": ["alt", "Mach", "TRA", "T2"],
        "X_s": ["T24", "T30", "T48"],
        "X_v": ["T40", "P30"],
        "T": ["fan_eff_mod", "HPT_eff_mod"],
    }
    path = tmp_path / "N-CMAPSS_DS01-005.h5"
    with h5py.File(path, "w") as handle:
        for groupe, noms in groupes.items():
            handle[f"{groupe}_dev"] = rng.normal(size=(n, len(noms)))
            handle[f"{groupe}_var"] = np.array(noms, dtype="S12")
        handle["A_var"] = np.array(["unit", "cycle", "Fc", "hs"], dtype="S5")
        unit = np.repeat([1.0, 2.0], 12)
        cycle = np.tile(np.repeat([1.0, 2.0, 3.0], 4), 2)
        handle["A_dev"] = np.column_stack([unit, cycle, np.ones(n), (cycle < 3).astype(float)])
        handle["Y_dev"] = (3 - cycle).astype(np.int64).reshape(-1, 1)
    return path


def test_read_ncmapss_extracts_expected_columns(mini_h5):
    df = read_ncmapss("DS01", split="dev", path=mini_h5)

    required = {"unit", "cycle", "Fc", "hs", "RUL"}
    assert required.issubset(df.columns)
    assert len(df) == 24
    assert df["unit"].dtype.kind in "iu"
    assert (df["ds_id"] == "DS01").all()
    assert (df["fault_mode"] == "HPT").all()


def test_read_ncmapss_excludes_leaky_groups(mini_h5):
    df = read_ncmapss("DS01", split="dev", path=mini_h5)
    assert not {"T40", "P30", "fan_eff_mod", "HPT_eff_mod"} & set(df.columns)


def test_resolve_ncmapss_path_by_pattern(tmp_path):
    (tmp_path / "N-CMAPSS_DS03-012.h5").touch()
    assert resolve_ncmapss_path("DS03", tmp_path).name == "N-CMAPSS_DS03-012.h5"
    with pytest.raises(FileNotFoundError):
        resolve_ncmapss_path("DS04", tmp_path)


def test_aggregate_to_cycles_reduces_rows_and_keeps_structure(mini_h5):
    raw = read_ncmapss("DS01", split="dev", path=mini_h5)
    cycle_df = aggregate_to_cycles(raw)
    cycle_df = drop_constant_columns(cycle_df)

    assert len(cycle_df) == 6
    assert {"ds_id", "fault_mode", "unit", "cycle", "RUL"}.issubset(cycle_df.columns)
    assert len(cycle_df) < len(raw)


def test_rolling_features_are_added(mini_h5):
    raw = read_ncmapss("DS01", split="dev", path=mini_h5)
    cycle_df = aggregate_to_cycles(raw)
    cycle_df = drop_constant_columns(cycle_df)
    columns = [col for col in cycle_df.columns if col.endswith("_mean")][:3]

    enriched = add_rolling_features(cycle_df, columns=columns, window=3)
    for col in columns:
        assert f"{col}_rolling_mean" in enriched.columns
        assert f"{col}_rolling_std" in enriched.columns
