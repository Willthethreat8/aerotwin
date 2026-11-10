"""Exporte prédictions, métriques et importances en Parquet : seule source de données du dashboard.

Moteurs dev : prédictions hors échantillon de la CV. Moteurs test : modèle final.

Usage : python -m src.export_dashboard
"""
from __future__ import annotations

import pandas as pd

from src import config
from src.train import train_ds

OUT_DIR = config.PROJECT_ROOT / "data" / "dashboard"


def build_tables(results: dict[str, dict]) -> dict[str, pd.DataFrame]:
    """Assemble les résultats de train_ds. `in_fleet` est faux pour les fichiers réservés à la comparaison."""
    cycles = pd.concat([r["predictions"] for r in results.values()], ignore_index=True)
    per_unit = pd.concat([r["per_unit"].assign(ds_id=ds_id) for ds_id, r in results.items()], ignore_index=True)
    for table in (cycles, per_unit):
        table["split"] = table["split"].replace({"cv": "dev"})
    per_unit["fault_mode"] = per_unit["ds_id"].map(config.NCMAPSS_FAULT_MODES)

    summary = pd.DataFrame([
        {"ds_id": ds_id, "fault_mode": config.NCMAPSS_FAULT_MODES[ds_id], **r["summary"]} for ds_id, r in results.items()
    ])
    importance = pd.concat([
        r["importance"].rename_axis("feature").reset_index(name="importance").assign(ds_id=ds_id)
        for ds_id, r in results.items()
    ], ignore_index=True)

    tables = {"cycles": cycles, "per_unit": per_unit, "summary": summary, "importance": importance}
    for table in tables.values():
        table["in_fleet"] = ~table["ds_id"].isin(config.NCMAPSS_COMPARISON_ONLY)
    return tables


def main() -> None:
    results = {ds_id: train_ds(ds_id, log_mlflow=False) for ds_id in config.NCMAPSS_FAULT_MODES}
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for name, table in build_tables(results).items():
        path = OUT_DIR / f"{name}.parquet"
        table.to_parquet(path, index=False)
        print(f"{path.name} : {len(table)} lignes, {path.stat().st_size / 1e6:.2f} Mo")


if __name__ == "__main__":
    main()
