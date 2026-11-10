"""Constantes et paramètres du projet AeroTwin."""
import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

# --- Chemins ---
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_RAW = PROJECT_ROOT / "data" / "raw"
DATA_PROCESSED = PROJECT_ROOT / "data" / "processed"

# --- Dataset NASA N-CMAPSS ---
NCMAPSS_DIR = DATA_RAW / "ncmapss"
# Fichiers retenus (ADR-010) et composant(s) dégradé(s)
NCMAPSS_FAULT_MODES = {
    "DS01": "HPT",
    "DS02": "HPT ou HPT+LPT",
    "DS03": "HPT+LPT",
    "DS04": "Fan",
    "DS05": "HPC",
    "DS06": "LPC+HPC",
    "DS07": "LPT",
}
# Absent de la page Flotte, visible seulement sur la page Modèle (ADR-010)
NCMAPSS_COMPARISON_ONLY = {"DS02"}

# C-MAPSS FD001, plus utilisé depuis ADR-002
CMAPSS_COLUMNS = (
    ["engine_id", "cycle", "setting_1", "setting_2", "setting_3"]
    + [f"sensor_{i}" for i in range(1, 22)]
)
FD001_TRAIN_PATH = DATA_RAW / "train_FD001.txt"

# --- Feature engineering ---
ROLLING_WINDOW = 5

# --- Toulouse-Blagnac (LFBO) ---
LFBO_LAT = 43.629
LFBO_LON = 1.367

# --- Météo (Open-Meteo ERA5) ---
OPEN_METEO_URL = "https://archive-api.open-meteo.com/v1/archive"
METEO_HOURLY_VARS = "temperature_2m,surface_pressure,windspeed_10m"

# --- Météo live (Aviation Weather Center) ---
METAR_STATION = os.getenv("METAR_STATION", "LFBO")

# --- Base de données ---
DB_USER = os.getenv("POSTGRES_USER")
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD")
DB_HOST = os.getenv("POSTGRES_HOST", "localhost")
DB_PORT = os.getenv("POSTGRES_PORT", "5432")
DB_NAME = os.getenv("POSTGRES_DB", "aerotwin_db")


def get_db_url() -> str:
    """Construit l'URL SQLAlchemy de connexion à PostGIS."""
    return (
        f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}"
        f"@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    )
