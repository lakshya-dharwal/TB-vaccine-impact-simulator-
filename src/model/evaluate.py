"""Evaluate the saved TB Futures models on the held-out test set."""

import json
import os
import sys
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

# Allow running as a script (`python src/model/evaluate.py`) as well as a module.
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src.model.features import build_feature_matrix

DATA_PATH = "data/processed/merged_tb_dataset.csv"
MODELS_DIR = "models"
TARGET = "tb_incidence"
TRAIN_END = 2018


def _metrics(y_true, y_pred):
    return {
        "r2": float(r2_score(y_true, y_pred)),
        "mae": float(mean_absolute_error(y_true, y_pred)),
        "rmse": float(np.sqrt(mean_squared_error(y_true, y_pred))),
    }


def _predict(model, X, log_target: bool):
    pred = model.predict(X)
    return np.maximum(np.expm1(pred), 0.0) if log_target else np.maximum(pred, 0.0)


def main():
    df = pd.read_csv(DATA_PATH).sort_values(["year", "country"]).reset_index(drop=True)
    with open(os.path.join(MODELS_DIR, "schema.json")) as f:
        schema = json.load(f)
    log_target = bool(schema.get("log_target"))

    test_df = df[df["year"] > TRAIN_END].copy()
    X_test = build_feature_matrix(test_df, schema)
    y_test = test_df[TARGET].values

    models = {
        "Random Forest": joblib.load(os.path.join(MODELS_DIR, "rf_model.pkl")),
        "Linear Regression": joblib.load(os.path.join(MODELS_DIR, "lr_model.pkl")),
        "Gradient Boosting": joblib.load(os.path.join(MODELS_DIR, "gbm_model.pkl")),
    }

    print("=" * 50)
    print(f"Evaluation on held-out test set ({TRAIN_END + 1}-2023)")
    print("=" * 50)
    print(f"Test rows: {len(X_test)}")
    print(f"Target transform: {'log1p' if log_target else 'none'}\n")

    for label, model in models.items():
        pred = _predict(model, X_test, log_target)
        m = _metrics(y_test, pred)
        print(f"{label:>18}:  R2={m['r2']:.3f}  MAE={m['mae']:.2f}  RMSE={m['rmse']:.2f}")

    with open(os.path.join(MODELS_DIR, "model_metrics.json")) as f:
        saved = json.load(f)
    print("\nSaved metrics on file:")
    print(json.dumps(saved, indent=2))


if __name__ == "__main__":
    main()
