"""Evaluate the saved TB Futures models on the held-out test set (2018-2022)."""

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
TRAIN_END = 2017


def _metrics(y_true, y_pred):
    return {
        "r2": float(r2_score(y_true, y_pred)),
        "mae": float(mean_absolute_error(y_true, y_pred)),
        "rmse": float(np.sqrt(mean_squared_error(y_true, y_pred))),
    }


def main():
    df = pd.read_csv(DATA_PATH)
    with open(os.path.join(MODELS_DIR, "schema.json")) as f:
        schema = json.load(f)
    test_df = df[df["year"] > TRAIN_END].copy()
    X_test = build_feature_matrix(test_df, schema)
    y_test = test_df[TARGET].values

    rf = joblib.load(os.path.join(MODELS_DIR, "rf_model.pkl"))
    lr = joblib.load(os.path.join(MODELS_DIR, "lr_model.pkl"))

    rf_m = _metrics(y_test, rf.predict(X_test))
    lr_m = _metrics(y_test, lr.predict(X_test))

    print("=" * 50)
    print(f"Evaluation on held-out test set ({TRAIN_END + 1}-2022)")
    print("=" * 50)
    print(f"Test rows: {len(X_test)}\n")
    for label, m in [("Random Forest", rf_m), ("Linear Regression", lr_m)]:
        print(f"{label:>18}:  R2={m['r2']:.3f}  MAE={m['mae']:.2f}  RMSE={m['rmse']:.2f}")

    with open(os.path.join(MODELS_DIR, "model_metrics.json")) as f:
        saved = json.load(f)
    print("\nSaved metrics on file:")
    print(json.dumps(saved, indent=2))


if __name__ == "__main__":
    main()
