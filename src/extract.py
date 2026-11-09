"""Extraction des données sources (Extract du ETL).

Ce module lit les fichiers N-CMAPSS HDF5 et récupère les séries météo contextuelles
pour les conditions de vol ; il ne fait que l'extraction, pas la transformation.
"""
from __future__ import annotations

from pathlib import Path

import h5py
import numpy as np
import pandas as pd
import requests
from metar import Metar

from src import config


def _decode_names(raw_array: np.ndarray | None) -> list[str]:
    """Convertit les libellés HDF5 bytes en chaînes lisibles."""
    if raw_array is None:
        return []
    values = np.asarray(raw_array).ravel()
    return [value.decode("utf-8") if isinstance(value, bytes) else str(value) for value in values]


def resolve_ncmapss_path(ds_id: str, directory: Path | str = config.NCMAPSS_DIR) -> Path:
    """Trouve le fichier d'un DS par motif (le suffixe de version varie : DS01-005, DS03-012...)."""
    matches = sorted(Path(directory).glob(f"N-CMAPSS_{ds_id}*.h5"))
    if len(matches) != 1:
        raise FileNotFoundError(f"{len(matches)} fichier(s) N-CMAPSS pour {ds_id} dans {directory}")
    return matches[0]


def read_ncmapss(
    ds_id: str = "DS01",
    split: str = "dev",
    path: Path | str | None = None,
) -> pd.DataFrame:
    """Lit un fichier N-CMAPSS et renvoie un DataFrame 1 Hz.

    Groupes lus : A (unit, cycle, Fc, hs), W (alt, Mach, TRA, T2), X_s (capteurs physiques), Y (RUL).
    X_v et T ne sont pas lus (ADR-004). `path` force un fichier précis, sinon il est résolu depuis `ds_id`.
    """
    if ds_id not in config.NCMAPSS_FAULT_MODES:
        raise ValueError(f"ds_id inconnu : {ds_id}")
    split_key = split.lower()
    if split_key not in {"dev", "test"}:
        raise ValueError(f"split must be 'dev' or 'test', got '{split}'")

    file_path = Path(path) if path is not None else resolve_ncmapss_path(ds_id)
    if not file_path.exists():
        raise FileNotFoundError(f"Dataset N-CMAPSS introuvable : {file_path}")

    with h5py.File(file_path, "r") as handle:
        aux_key = f"A_{split_key}"
        weather_key = f"W_{split_key}"
        sensors_key = f"X_s_{split_key}"
        rul_key = f"Y_{split_key}"

        for key in (aux_key, weather_key, sensors_key, rul_key):
            if key not in handle:
                raise KeyError(f"Clé {key!r} absente du fichier HDF5 : {file_path}")

        aux_matrix = np.asarray(handle[aux_key])
        weather_matrix = np.asarray(handle[weather_key])
        sensors_matrix = np.asarray(handle[sensors_key])
        rul_vector = np.asarray(handle[rul_key]).reshape(-1, 1)

        aux_cols = _decode_names(handle["A_var"]) or ["unit", "cycle", "Fc", "hs"]
        weather_cols = _decode_names(handle["W_var"]) or ["alt", "Mach", "TRA", "T2"]
        sensor_cols = _decode_names(handle["X_s_var"]) or [f"sensor_{i}" for i in range(sensors_matrix.shape[1])]

        aux_df = pd.DataFrame(aux_matrix, columns=aux_cols)
        weather_df = pd.DataFrame(weather_matrix, columns=weather_cols)
        sensors_df = pd.DataFrame(sensors_matrix, columns=sensor_cols)
        rul_df = pd.DataFrame(rul_vector, columns=["RUL"])

    df = pd.concat([aux_df, weather_df, sensors_df, rul_df], axis=1)
    for col in ["unit", "cycle", "Fc", "hs", "RUL"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
    df["unit"] = df["unit"].astype("Int64").astype("int64")
    df["cycle"] = df["cycle"].astype("Int64").astype("int64")
    df["Fc"] = df["Fc"].astype("Int64").astype("int64")
    df["hs"] = df["hs"].astype("Int64").astype("int64")
    df["ds_id"] = ds_id
    df["fault_mode"] = config.NCMAPSS_FAULT_MODES[ds_id]
    return df.reset_index(drop=True)


def fetch_weather_history(
    start_date: str,
    end_date: str,
    lat: float = config.LFBO_LAT,
    lon: float = config.LFBO_LON,
) -> pd.DataFrame:
    """Récupère l'historique météo horaire via Open-Meteo.

    La météo est traitée comme contexte environnemental, elle n'est pas utilisée
    directement dans le modèle de RUL de la phase 3 ; elle sert à enrichir les
    analyses et le contexte de vol.
    """
    params = {
        "latitude": lat,
        "longitude": lon,
        "start_date": start_date,
        "end_date": end_date,
        "hourly": config.METEO_HOURLY_VARS,
        "timezone": "auto",
    }

    response = requests.get(config.OPEN_METEO_URL, params=params, timeout=30)
    response.raise_for_status()
    payload = response.json()

    hourly = payload.get("hourly", {})
    times = hourly.get("time", [])
    if not times:
        return pd.DataFrame(
            columns=[
                "date_heure",
                "temperature_c",
                "pression_hpa",
                "vent_vitesse_kt",
            ]
        )

    data = {
        "date_heure": pd.to_datetime(times),
        "temperature_c": hourly.get("temperature_2m", []),
        "pression_hpa": hourly.get("surface_pressure", []),
        "vent_vitesse_kt": [value * 0.539957 for value in hourly.get("windspeed_10m", [])],
    }

    df = pd.DataFrame(data)
    df = df.rename(columns={"date_heure": "date_heure"})
    return df


def fetch_metar_live(station: str = config.METAR_STATION) -> dict | None:
    """Récupère le METAR courant (dernière heure) via l'Aviation Weather Center.

    Phase 7 uniquement — usage dashboard temps réel, jamais comme feature du
    modèle RUL (la météo surface n'alimente pas le modèle, cf. ROADMAP.md).
    """
    url = "https://aviationweather.gov/api/data/metar"
    params = {"ids": station, "format": "json", "hours": 1}
    headers = {"User-Agent": "AeroTwin-Project/1.0"}

    response = requests.get(url, params=params, headers=headers, timeout=30)
    response.raise_for_status()
    payload = response.json()

    if not payload:
        return None

    observation = Metar.Metar(payload[0]["rawOb"])
    return {
        "aeroport": station,
        "date_heure": observation.time,
        "temperature_c": observation.temp.value() if observation.temp else None,
        "vent_vitesse_kt": observation.wind_speed.value() if observation.wind_speed else None,
        "pression_hpa": observation.press.value() if observation.press else None,
        "metar_brut": payload[0]["rawOb"],
    }
