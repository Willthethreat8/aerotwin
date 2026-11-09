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
    """Entraîne et évalue le baseline XGBoost, log tout dans MLflow.

    En plus de `test` (métriques sur l'échelle propre à ce run — cappée ou non),
    renvoie `comparable_test` : métriques évaluées contre une vérité terrain
    toujours cappée à RUL_CAP, pour pouvoir comparer un run capped et un run
    uncapped sur la même échelle (leurs RMSE bruts ne sont pas comparables,
    le non-cappé porte sur des valeurs de RUL beaucoup plus grandes).
    """
    logger.info("Construction des features dev/test ...")
    dev_cycles = build_cycle_features("dev", dataset_path)
    test_cycles = build_cycle_features("test", dataset_path)

    X_dev, y_dev, groups_dev = split_features_target(dev_cycles)
    X_test, y_test_raw, _ = split_features_target(test_cycles)

    y_dev_train = cap_rul(y_dev, cap) if cap is not None else y_dev
    y_test_eval = cap_rul(y_test_raw, cap) if cap is not None else y_test_raw

    logger.info("Cross-validation leave-one-unit-out sur dev (%s moteurs) ...", groups_dev.nunique())
    cv_results = cross_validate(X_dev, y_dev_train, groups_dev)

    logger.info("Entraînement final sur dev complet, évaluation sur test officiel ...")
    model = XGBRegressor(**XGB_PARAMS)
    model.fit(X_dev, y_dev_train)
    predictions = model.predict(X_test)
    test_metrics = _metrics(y_test_eval, predictions)
    comparable_metrics = _metrics(cap_rul(y_test_raw, RUL_CAP), predictions)

    mlflow.set_experiment(experiment_name)
    with mlflow.start_run(run_name=f"xgboost-cap{cap}" if cap else "xgboost-nocap") as run:
        mlflow.log_params({**XGB_PARAMS, "rul_cap": cap, "n_features": X_dev.shape[1]})
        mlflow.log_metrics({f"cv_{k}": v for k, v in cv_results["mean"].items()})
        mlflow.log_metrics({f"test_{k}": v for k, v in test_metrics.items()})
        mlflow.log_metrics({f"comparable_test_{k}": v for k, v in comparable_metrics.items()})
        signature = mlflow.models.infer_signature(X_dev, predictions)
        mlflow.xgboost.log_model(model, name="model", signature=signature, input_example=X_dev.head())
        run_id = run.info.run_id

    logger.info(
        "Test RMSE=%.2f MAE=%.2f R2=%.3f",
        test_metrics["rmse"], test_metrics["mae"], test_metrics["r2"],
    )
    return {"cv": cv_results, "test": test_metrics, "comparable_test": comparable_metrics, "run_id": run_id}


def compare_cap_variants(
    dataset_path: str = config.NCMAPSS_DS01_PATH,
    experiment_name: str = "aerotwin-phase4-xgboost",
) -> dict[str, object]:
    """Phase 4.2 — entraîne capped et non-capped, compare sur l'échelle cappée
    (seule échelle où les deux runs sont comparables), tague le meilleur run
    MLflow avec `best_model=true`."""
    logger.info("Run 1/2 : RUL cappée à %s ...", RUL_CAP)
    capped = run_baseline(dataset_path=dataset_path, cap=RUL_CAP, experiment_name=experiment_name)
    logger.info("Run 2/2 : RUL non cappée ...")
    uncapped = run_baseline(dataset_path=dataset_path, cap=None, experiment_name=experiment_name)

    rmse_capped = capped["comparable_test"]["rmse"]
    rmse_uncapped = uncapped["comparable_test"]["rmse"]
    winner = "capped" if rmse_capped <= rmse_uncapped else "uncapped"
    best_run_id = capped["run_id"] if winner == "capped" else uncapped["run_id"]

    mlflow.tracking.MlflowClient().set_tag(best_run_id, "best_model", "true")
    logger.info(
        "RMSE comparable (évalué sur RUL cappée à %s dans les deux cas) : capped=%.2f vs uncapped=%.2f -> meilleur = %s (run_id=%s)",
        RUL_CAP, rmse_capped, rmse_uncapped, winner, best_run_id,
    )
    return {"capped": capped, "uncapped": uncapped, "winner": winner, "best_run_id": best_run_id}


def main() -> None:
    parser = argparse.ArgumentParser(description="Phase 4 — Baseline XGBoost RUL")
    parser.add_argument("--dataset", type=str, default=str(config.NCMAPSS_DS01_PATH))
    parser.add_argument("--cap", type=int, default=RUL_CAP, help="Plafond RUL (défaut 125)")
    parser.add_argument("--no-cap", action="store_true", help="Désactive le plafonnement RUL")
    parser.add_argument("--compare", action="store_true", help="Phase 4.2 : compare capped vs non-capped, tague le meilleur")
    args = parser.parse_args()

    if args.compare:
        result = compare_cap_variants(dataset_path=args.dataset)
    else:
        cap = None if args.no_cap else args.cap
        result = run_baseline(dataset_path=args.dataset, cap=cap)
    print(result)


if __name__ == "__main__":
    main()
