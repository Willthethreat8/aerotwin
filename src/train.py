"""Modèle XGBoost de RUL, un modèle par fichier N-CMAPSS.

CV leave-one-unit-out sur les moteurs dev (ADR-005), puis modèle final entraîné sur tout le dev et évalué sur
les moteurs test officiels. Métriques par moteur et écart-type entre moteurs.

Usage : python -m src.train --ds DS03    ou    python -m src.train --all (écrit docs/resultats.md)
"""
from __future__ import annotations

import argparse
import logging
import os

os.environ.setdefault("MLFLOW_ALLOW_FILE_STORE", "true")  # conserve le suivi local dans mlruns/

import mlflow
import mlflow.xgboost
import numpy as np
import pandas as pd
from sklearn.model_selection import LeaveOneGroupOut
from xgboost import XGBRegressor

from src import config
from src.features import build_cycle_features, cap_rul, split_features_target

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
logger = logging.getLogger("aerotwin.train")

RUL_CAP = None  # ADR-008
XGB_PARAMS = {
    "n_estimators": 300,
    "max_depth": 4,
    "learning_rate": 0.05,
    "subsample": 0.8,
    "colsample_bytree": 0.8,
    "random_state": 42,
}
RESULTS_PATH = config.PROJECT_ROOT / "docs" / "resultats.md"


def _rmse(y_true, y_pred) -> float:
    return float(np.sqrt(np.mean((np.asarray(y_true) - np.asarray(y_pred)) ** 2)))


def _mae(y_true, y_pred) -> float:
    return float(np.mean(np.abs(np.asarray(y_true) - np.asarray(y_pred))))


def cross_validate(X: pd.DataFrame, y: pd.Series, groups: pd.Series, params: dict = XGB_PARAMS) -> np.ndarray:
    """Prédictions hors échantillon : chaque moteur est prédit par un modèle entraîné sans lui."""
    oof = np.zeros(len(y))
    for train_idx, val_idx in LeaveOneGroupOut().split(X, y, groups):
        model = XGBRegressor(**params)
        model.fit(X.iloc[train_idx], y.iloc[train_idx])
        oof[val_idx] = model.predict(X.iloc[val_idx])
    return oof


def per_unit_metrics(predictions: pd.DataFrame) -> pd.DataFrame:
    """RMSE et MAE par (split, moteur), contre la RUL réelle."""
    rows = [
        {"split": split, "unit": unit, "n_cycles": len(g),
         "rmse": _rmse(g["rul_true"], g["rul_pred"]), "mae": _mae(g["rul_true"], g["rul_pred"])}
        for (split, unit), g in predictions.groupby(["split", "unit"])
    ]
    return pd.DataFrame(rows)


def summarize(per_unit: pd.DataFrame, predictions: pd.DataFrame) -> dict[str, float]:
    """Moyenne et écart-type entre moteurs, plus le RMSE calculé sur tous les cycles."""
    out = {}
    for split, g in per_unit.groupby("split"):
        pred = predictions[predictions["split"] == split]
        out.update({
            f"{split}_rmse_mean": g["rmse"].mean(), f"{split}_rmse_std": g["rmse"].std(),
            f"{split}_mae_mean": g["mae"].mean(), f"{split}_mae_std": g["mae"].std(),
            f"{split}_rmse_all_cycles": _rmse(pred["rul_true"], pred["rul_pred"]),
        })
    return {k: float(v) for k, v in out.items()}


def train_ds(ds_id: str, cap: int | None = RUL_CAP, log_mlflow: bool = True) -> dict[str, object]:
    """Entraîne et évalue le modèle d'un fichier. `split` vaut "cv" pour les moteurs dev prédits hors échantillon."""
    dev = build_cycle_features("dev", ds_id)
    test = build_cycle_features("test", ds_id)
    X_dev, y_dev, groups = split_features_target(dev)
    X_test, _, _ = split_features_target(test)
    y_fit = cap_rul(y_dev, cap) if cap is not None else y_dev

    logger.info("%s : CV leave-one-unit-out sur %s moteurs dev", ds_id, groups.nunique())
    oof = cross_validate(X_dev, y_fit, groups)
    model = XGBRegressor(**XGB_PARAMS)
    model.fit(X_dev, y_fit)

    keep = ["ds_id", "fault_mode", "unit", "cycle", "hs", "RUL"]
    predictions = pd.concat([
        dev[keep].assign(split="cv", rul_pred=oof),
        test[keep].assign(split="test", rul_pred=model.predict(X_test)),
    ], ignore_index=True).rename(columns={"RUL": "rul_true"})

    per_unit = per_unit_metrics(predictions)
    summary = summarize(per_unit, predictions)
    importance = pd.Series(model.feature_importances_, index=X_dev.columns).sort_values(ascending=False)

    if log_mlflow:
        mlflow.set_experiment("aerotwin-xgboost")
        with mlflow.start_run(run_name=ds_id):
            mlflow.log_params({**XGB_PARAMS, "ds_id": ds_id, "rul_cap": cap, "n_features": X_dev.shape[1]})
            mlflow.log_metrics(summary)
            mlflow.xgboost.log_model(model, name="model", signature=mlflow.models.infer_signature(X_dev, oof))

    logger.info("%s : CV RMSE %.2f ± %.2f, test RMSE %.2f ± %.2f", ds_id,
                summary["cv_rmse_mean"], summary["cv_rmse_std"], summary["test_rmse_mean"], summary["test_rmse_std"])
    return {"predictions": predictions, "per_unit": per_unit, "summary": summary, "importance": importance}


def write_results(results: dict[str, dict]) -> None:
    lines = [
        "# Résultats",
        "",
        "Généré par `python -m src.train --all`. Moyenne ± écart-type des métriques par moteur ; « tous cycles » est le",
        "RMSE calculé sur l'ensemble des cycles du split. CV : leave-one-unit-out sur les moteurs dev.",
        "",
        "| DS | Mode de panne | Moteurs CV / test | RMSE CV | MAE CV | RMSE test | MAE test | RMSE test tous cycles |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for ds_id, r in results.items():
        s, pu = r["summary"], r["per_unit"]
        n_cv, n_test = (pu["split"] == "cv").sum(), (pu["split"] == "test").sum()
        lines.append(
            f"| {ds_id} | {config.NCMAPSS_FAULT_MODES[ds_id]} | {n_cv} / {n_test} "
            f"| {s['cv_rmse_mean']:.2f} ± {s['cv_rmse_std']:.2f} | {s['cv_mae_mean']:.2f} ± {s['cv_mae_std']:.2f} "
            f"| {s['test_rmse_mean']:.2f} ± {s['test_rmse_std']:.2f} | {s['test_mae_mean']:.2f} ± {s['test_mae_std']:.2f} "
            f"| {s['test_rmse_all_cycles']:.2f} |"
        )
    lines += ["", "## Par moteur", "", "| DS | Split | Moteur | Cycles | RMSE | MAE |", "|---|---|---|---|---|---|"]
    for ds_id, r in results.items():
        for row in r["per_unit"].itertuples():
            lines.append(f"| {ds_id} | {row.split} | {row.unit} | {row.n_cycles} | {row.rmse:.2f} | {row.mae:.2f} |")
    RESULTS_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="XGBoost RUL par fichier N-CMAPSS")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--ds", choices=sorted(config.NCMAPSS_FAULT_MODES))
    group.add_argument("--all", action="store_true", help="Tous les fichiers, écrit docs/resultats.md")
    args = parser.parse_args()

    if args.all:
        write_results({ds_id: train_ds(ds_id) for ds_id in config.NCMAPSS_FAULT_MODES})
    else:
        print(train_ds(args.ds)["per_unit"].to_string(index=False))


if __name__ == "__main__":
    main()
