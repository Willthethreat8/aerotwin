"""Transformations de l'ETL N-CMAPSS. Fonctions pures, sans I/O.

La RUL est fournie par le jeu de données ; la transformation principale est l'agrégation 1 Hz vers cycle
(ADR-003).
"""
from __future__ import annotations

import geopandas as gpd
import numpy as np
import pandas as pd
from shapely.geometry import LineString

from src import config


def aggregate_to_cycles(df: pd.DataFrame) -> pd.DataFrame:
    """Agrège les mesures 1 Hz en une ligne par moteur et par cycle (moyenne, écart-type, min, max)."""
    if df.empty:
        return df.copy()

    required = {"unit", "cycle"}
    missing = required.difference(df.columns)
    if missing:
        raise ValueError(f"Le DataFrame ne contient pas les colonnes de groupage : {sorted(missing)}")

    features = [col for col in df.columns if col not in {"unit", "cycle"}]
    agg_spec = {}
    for col in features:
        if col in {"Fc", "hs", "RUL"}:
            agg_spec[col] = "first"
        elif pd.api.types.is_numeric_dtype(df[col]):
            agg_spec[col] = ["mean", "std", "min", "max"]
        else:
            agg_spec[col] = "first"

    aggregated = df.groupby(["unit", "cycle"], as_index=False).agg(agg_spec)
    aggregated.columns = [
        f"{col}_{stat}" if stat != "first" else col
        for col, stat in aggregated.columns.to_flat_index()
    ]

    aggregated = aggregated.rename(columns={"unit_": "unit", "cycle_": "cycle", "RUL_first": "RUL", "Fc_first": "Fc", "hs_first": "hs"})
    aggregated["unit"] = aggregated["unit"].astype(int)
    aggregated["cycle"] = aggregated["cycle"].astype(int)
    if "Fc" in aggregated.columns:
        aggregated["Fc"] = pd.to_numeric(aggregated["Fc"], errors="coerce").fillna(0).astype(int)
    if "hs" in aggregated.columns:
        aggregated["hs"] = pd.to_numeric(aggregated["hs"], errors="coerce").fillna(0).astype(int)
    return aggregated.sort_values(["unit", "cycle"]).reset_index(drop=True)


def drop_constant_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Retire les colonnes sans variance, qui n'apportent rien au modèle."""
    if df.empty:
        return df.copy()

    keep_cols = [col for col in ("ds_id", "fault_mode", "unit", "cycle") if col in df.columns]
    for col in df.columns:
        if col in keep_cols:
            continue
        if df[col].nunique(dropna=False) > 1:
            keep_cols.append(col)
    return df[keep_cols].copy()


def add_rolling_features(
    df: pd.DataFrame,
    columns: list[str],
    window: int = config.ROLLING_WINDOW,
) -> pd.DataFrame:
    """Ajoute les rolling means/std par moteur dans l'ordre cyclique."""
    if df.empty:
        return df.copy()

    output = df.sort_values(["unit", "cycle"]).copy()
    for col in columns:
        if col not in output.columns:
            continue
        output[f"{col}_rolling_mean"] = output.groupby("unit")[col].transform(
            lambda s: s.rolling(window=window, min_periods=1).mean()
        )
        output[f"{col}_rolling_std"] = output.groupby("unit")[col].transform(
            lambda s: s.rolling(window=window, min_periods=1).std().fillna(0.0)
        )
    return output.reset_index(drop=True)


def generate_trajectories(
    flight_summary: pd.DataFrame,
    n_points: int = 50,
    seed: int | None = 42,
) -> gpd.GeoDataFrame:
    """Génère une LineString par moteur, à partir de LFBO.

    La route reste synthétique mais se base sur les conditions de vol observées
    (classe de vol / altitude / Mach / cycle). L'objectif est de conserver un
    support visuel cohérent pour la flotte sans dépendre d'un générateur de
    trajectoires purement aléatoire.
    """
    if flight_summary.empty:
        return gpd.GeoDataFrame(columns=["unit", "Fc", "geometry"], geometry="geometry", crs="EPSG:4326")

    rng = np.random.default_rng(seed)
    records: list[dict] = []
    base_lat = config.LFBO_LAT
    base_lon = config.LFBO_LON

    for unit, group in flight_summary.groupby("unit", sort=True):
        fc_value = int(group["Fc"].iloc[0]) if "Fc" in group.columns else 1
        altitude_mean = float(group.get("alt_mean", pd.Series([0.0])).iloc[0]) if "alt_mean" in group.columns else 0.0

        progression = np.linspace(0.0, 1.0, n_points)
        lateral = 0.0008 * (1.0 + fc_value) * progression
        longitudinal = 0.0012 * (1.0 + fc_value / 3.0) * progression

        offset_lat = np.sin(progression * np.pi * 0.5 + 0.3 * fc_value) * 0.0025
        offset_lon = np.cos(progression * np.pi * 0.7 + 0.2 * fc_value) * 0.0030

        if altitude_mean > 0:
            offset_lat *= 0.5 + min(altitude_mean / 10000.0, 1.0)
            offset_lon *= 0.5 + min(altitude_mean / 10000.0, 1.0)

        drift_lat = rng.normal(0.0, 1e-4, size=n_points)
        drift_lon = rng.normal(0.0, 1e-4, size=n_points)

        coords = [
            (
                base_lon + lateral_i + offset_lon_i + drift_lon_i,
                base_lat + longitudinal_i + offset_lat_i + drift_lat_i,
            )
            for lateral_i, longitudinal_i, offset_lon_i, offset_lat_i, drift_lon_i, drift_lat_i in zip(
                lateral, longitudinal, offset_lon, offset_lat, drift_lon, drift_lat
            )
        ]

        records.append({
            "unit": int(unit),
            "Fc": fc_value,
            "geometry": LineString(coords),
        })

    gdf = gpd.GeoDataFrame(records, geometry="geometry", crs="EPSG:4326")
    return gdf[["unit", "Fc", "geometry"]]
