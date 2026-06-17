"""Evaluate the saved TB Futures models on the held-out test set (2018-2023)."""

import json
import os
import sys
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src.model.features import build_feature_matrix

DATA_PATH = "data/processed/merged_tb_dataset.csv"
MODELS_DIR = "models"
TARGET = "tb_incidence"
TRAIN_END = 2017


def _metrics(y_true, y_pred):
    y_pred = np.clip(y_pred, 0, None)
    return {
        "r2": float(r2_score(y_true, y_pred)),
        "r2_log": float(r2_score(np.log1p(y_true), np.log1p(y_pred))),
        "mae": float(mean_absolute_error(y_true, y_pred)),
        "rmse": float(np.sqrt(mean_squared_error(y_true, y_pred))),
    }


def main():
    df = pd.read_csv(DATA_PATH)
    with open(os.path.join(MODELS_DIR, "schema.json")) as f:
        schema = json.load(f)
    log_target = schema.get("log_target", False)

    test_df = df[df["year"] > TRAIN_END].copy()
    X_test = build_feature_matrix(test_df, schema)
    y_test = test_df[TARGET].values

    print("=" * 60)
    print(f"Evaluation on held-out test set ({TRAIN_END + 1}-2023) | rows: {len(X_test)}")
    print("=" * 60)
    for fname, label in [("rf_model.pkl", "Random Forest"),
                         ("lr_model.pkl", "Linear Regression"),
                         ("gbm_model.pkl", "Gradient Boosting")]:
        path = os.path.join(MODELS_DIR, fname)
        if not os.path.exists(path):
            continue
        pred = joblib.load(path).predict(X_test)
        if log_target:
            pred = np.expm1(pred)
        m = _metrics(y_test, pred)
        print(f"{label:>18}:  R2={m['r2']:.3f}  R2(log)={m['r2_log']:.3f}  "
              f"MAE={m['mae']:.2f}  RMSE={m['rmse']:.2f}")

    diag_path = os.path.join(MODELS_DIR, "diagnostics.json")
    if os.path.exists(diag_path):
        with open(diag_path) as f:
            diag = json.load(f)
        print("\nRandom Forest mean abs error by region:")
        for k, v in sorted(diag["mae_by_region"].items()):
            print(f"  {k:<6} {v}")
        print("Mean abs error by income band:")
        for k, v in sorted(diag["mae_by_income"].items()):
            print(f"  {k:<6} {v}")


if __name__ == "__main__":
    main()
