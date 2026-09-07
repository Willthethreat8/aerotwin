"""Phase 4.1 — Baseline XGBoost pour la prédiction de RUL (N-CMAPSS DS01).

Choix XGBoost : c'est le modèle le plus utilisé dans la littérature C-MAPSS/
N-CMAPSS sur données tabulaires agrégées par cycle (robuste, peu de tuning,
rapide sur un dataset de cette taille). Une comparaison avec un autre modèle
(ex. Random Forest, LSTM) est prévue en 4.3, pas dans ce baseline.

CV : leave-one-unit-out sur le split dev (6 moteurs), aucune fuite entre
moteurs. Évaluation finale sur le split test officiel (moteurs 7-10), jamais
vu pendant l'entraînement ni le tuning.
"""
from __future__ import annotations

import argparse
import logging

import mlflow
import mlflow.xgboost
import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import LeaveOneGroupOut
from xgboost import XGBRegressor

from src import config
from src.features import build_cycle_features, cap_rul, split_features_target

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
logger = logging.getLogger("aerotwin.phase4")

RUL_CAP = 125
XGB_PARAMS = {
    "n_estimators": 300,
    "max_depth": 4,
    "learning_rate": 0.05,
    "subsample": 0.8,
    "colsample_bytree": 0.8,
    "random_state": 42,
}


def _metrics(y_true, y_pred) -> dict[str, float]:
    return {
        "rmse": float(np.sqrt(mean_squared_error(y_true, y_pred))),
        "mae": float(mean_absolute_error(y_true, y_pred)),
        "r2": float(r2_score(y_true, y_pred)),
    }


def cross_validate(
    X: pd.DataFrame, y: pd.Series, groups: pd.Series, params: dict = XGB_PARAMS
) -> dict[str, object]:
    """Leave-one-unit-out : chaque moteur du dev sert une fois de validation."""
    logo = LeaveOneGroupOut()
    fold_metrics = []
    for train_idx, val_idx in logo.split(X, y, groups):
        model = XGBRegressor(**params)
        model.fit(X.iloc[train_idx], y.iloc[train_idx])
        preds = model.predict(X.iloc[val_idx])
        fold_metrics.append(_metrics(y.iloc[val_idx], preds))

    fold_df = pd.DataFrame(fold_metrics)
    return {"per_fold": fold_metrics, "mean": fold_df.mean().to_dict(), "std": fold_df.std().to_dict()}


def run_baseline(
    dataset_path: str = config.NCMAPSS_DS01_PATH,
    cap: int | None = RUL_CAP,
    experiment_name: str = "aerotwin-phase4-xgboost",
) -> dict[str, object]:
    """Entraîne et évalue le baseline XGBoost, log tout dans MLflow."""
    logger.info("Construction des features dev/test ...")
    dev_cycles = build_cycle_features("dev", dataset_path)
    test_cycles = build_cycle_features("test", dataset_path)

    X_dev, y_dev, groups_dev = split_features_target(dev_cycles)
    X_test, y_test, _ = split_features_target(test_cycles)

    if cap is not None:
        y_dev = cap_rul(y_dev, cap)
        y_test = cap_rul(y_test, cap)

    logger.info("Cross-validation leave-one-unit-out sur dev (%s moteurs) ...", groups_dev.nunique())
    cv_results = cross_validate(X_dev, y_dev, groups_dev)

    logger.info("Entraînement final sur dev complet, évaluation sur test officiel ...")
    model = XGBRegressor(**XGB_PARAMS)
    model.fit(X_dev, y_dev)
    test_metrics = _metrics(y_test, model.predict(X_test))

    mlflow.set_experiment(experiment_name)
    with mlflow.start_run(run_name=f"xgboost-cap{cap}" if cap else "xgboost-nocap"):
        mlflow.log_params({**XGB_PARAMS, "rul_cap": cap, "n_features": X_dev.shape[1]})
        mlflow.log_metrics({f"cv_{k}": v for k, v in cv_results["mean"].items()})
        mlflow.log_metrics({f"test_{k}": v for k, v in test_metrics.items()})
        mlflow.xgboost.log_model(model, artifact_path="model")

    logger.info(
        "Test RMSE=%.2f MAE=%.2f R2=%.3f (référence à battre : RMSE 36.89)",
        test_metrics["rmse"], test_metrics["mae"], test_metrics["r2"],
    )
    return {"cv": cv_results, "test": test_metrics}


def main() -> None:
    parser = argparse.ArgumentParser(description="Phase 4 — Baseline XGBoost RUL")
    parser.add_argument("--dataset", type=str, default=str(config.NCMAPSS_DS01_PATH))
    parser.add_argument("--cap", type=int, default=RUL_CAP, help="Plafond RUL (défaut 125)")
    parser.add_argument("--no-cap", action="store_true", help="Désactive le plafonnement RUL")
    args = parser.parse_args()

    cap = None if args.no_cap else args.cap
    result = run_baseline(dataset_path=args.dataset, cap=cap)
    print(result)


if __name__ == "__main__":
    main()
