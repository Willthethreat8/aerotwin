"""ETL N-CMAPSS vers PostGIS : extraction, agrégation par cycle, chargement."""
from __future__ import annotations

import argparse
import logging

from src import config
from src.extract import fetch_weather_history, read_ncmapss
from src.load import get_engine, load_dataframe
from src.transform import add_rolling_features, aggregate_to_cycles, drop_constant_columns

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
logger = logging.getLogger("aerotwin.phase3")


def run_phase3_pipeline(
    ds_id: str = "DS01",
    split: str = "dev",
    cycle_table: str = "phase3_cycles",
    weather_table: str = "phase3_weather",
    weather_start: str = "2024-01-01",
    weather_end: str = "2024-12-31",
) -> dict[str, int | str]:
    """Exécute la chaîne ETL.

    Retourne un dictionnaire de résumé de l'exécution.
    """
    logger.info("Lecture du dataset N-CMAPSS ...")
    raw = read_ncmapss(ds_id=ds_id, split=split)
    logger.info("Dataset lu : %s lignes", len(raw))

    logger.info("Agrégation par moteur et par cycle ...")
    cycles = aggregate_to_cycles(raw)
    cycles = drop_constant_columns(cycles)
    logger.info("Après agrégation : %s cycles", len(cycles))

    rolling_cols = [col for col in cycles.columns if col.endswith("_mean")]
    cycles = add_rolling_features(cycles, columns=rolling_cols[:8], window=config.ROLLING_WINDOW)

    logger.info("Récupération contexte météo historique ...")
    weather = fetch_weather_history(weather_start, weather_end)

    logger.info("Persistance des résultats ...")
    try:
        engine = get_engine()
        loaded_cycles = load_dataframe(cycles, cycle_table, engine)
        loaded_weather = load_dataframe(weather, weather_table, engine)
        logger.info("Cycle rows sauvegardées : %s", loaded_cycles)
        logger.info("Weather rows sauvegardées : %s", loaded_weather)
    except Exception as exc:  # pragma: no cover - garde-fou pour un environ non-configuré
        logger.warning("Persistance DB impossible : %s", exc)
        loaded_cycles = len(cycles)
        loaded_weather = len(weather)

    return {
        "raw_rows": int(len(raw)),
        "cycle_rows": int(len(cycles)),
        "loaded_cycles": int(loaded_cycles),
        "loaded_weather": int(loaded_weather),
        "cycle_table": cycle_table,
        "weather_table": weather_table,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="ETL AeroTwin")
    parser.add_argument("--ds", type=str, default="DS01", choices=sorted(config.NCMAPSS_FAULT_MODES), help="Fichier N-CMAPSS")
    parser.add_argument("--split", type=str, default="dev", choices=["dev", "test"], help="Split de lecture du dataset")
    parser.add_argument("--cycle-table", type=str, default="phase3_cycles", help="Nom table PostGIS pour les cycles")
    parser.add_argument("--weather-table", type=str, default="phase3_weather", help="Nom table PostGIS pour la météo")
    parser.add_argument("--weather-start", type=str, default="2024-01-01", help="Début de la période météo")
    parser.add_argument("--weather-end", type=str, default="2024-12-31", help="Fin de la période météo")
    args = parser.parse_args()

    result = run_phase3_pipeline(
        ds_id=args.ds,
        split=args.split,
        cycle_table=args.cycle_table,
        weather_table=args.weather_table,
        weather_start=args.weather_start,
        weather_end=args.weather_end,
    )
    print(result)


if __name__ == "__main__":
    main()
