"""Chargement vers PostGIS (Load du ETL).

Ce module est volontairement minimaliste : il fournit le moteur DB et les
méthodes de persistance pour les DataFrames tabulaires et géospatiaux.
"""
from __future__ import annotations

import geopandas as gpd
import pandas as pd
from sqlalchemy import Engine, create_engine

from src import config


def get_engine() -> Engine:
    """Crée le moteur SQLAlchemy vers la base de données PostGIS."""
    return create_engine(config.get_db_url(), pool_pre_ping=True)


def load_dataframe(df: pd.DataFrame, table_name: str, engine: Engine) -> int:
    """Insère un DataFrame en base avec `if_exists='replace'` pour un MVP fiable."""
    if df.empty:
        return 0
    df.to_sql(table_name, con=engine, if_exists="replace", index=False)
    return len(df)


def load_geodataframe(gdf: gpd.GeoDataFrame, table_name: str, engine: Engine) -> int:
    """Insère un GeoDataFrame dans PostGIS via `to_postgis`."""
    if gdf.empty:
        return 0
    gdf.to_postgis(table_name, con=engine, if_exists="replace", index=False)
    return len(gdf)
