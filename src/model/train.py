"""Train the TB Futures models.

Fits a Random Forest (primary) and a Linear Regression (comparison baseline)
to predict TB incidence per 100k from whatever covariates the dataset contains.
Temporal split: train 2000-2017, test 2018-2022. The detected feature schema is
saved so inference uses an identical layout.
"""

import json
import os
import sys
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

# Allow running as a script (`python src/model/train.py`) as well as a module.
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src.model.features import build_feature_matrix, detect_schema

DATA_PATH = "data/processed/merged_tb_dataset.csv"
MODELS_DIR = "models"
TARGET = "tb_incidence"
TRAIN_END = 2017  # train 2000-2017, test 2018-2022


def metrics(y_true, y_pred) -> dict:
    return {
        "r2": float(r2_score(y_true, y_pred)),
        "mae": float(mean_absolute_error(y_true, y_pred)),
        "rmse": float(np.sqrt(mean_squared_error(y_true, y_pred))),
    }


def main():
    os.makedirs(MODELS_DIR, exist_ok=True)
    df = pd.read_csv(DATA_PATH)

    schema = detect_schema(df)
    print(f"Feature columns ({len(schema['feature_columns'])}): {schema['feature_columns']}")
    print(f"Scenarios: {schema['scenarios']}")

    train_df = df[df["year"] <= TRAIN_END].copy()
    test_df = df[df["year"] > TRAIN_END].copy()

    X_train = build_feature_matrix(train_df, schema)
    y_train = train_df[TARGET].values
    X_test = build_feature_matrix(test_df, schema)
    y_test = test_df[TARGET].values

    print(f"Training rows: {len(X_train)} | Test rows: {len(X_test)}")

    rf = RandomForestRegressor(n_estimators=200, random_state=42)
    rf.fit(X_train, y_train)

    lr = LinearRegression()
    lr.fit(X_train, y_train)

    rf_metrics = metrics(y_test, rf.predict(X_test))
    lr_metrics = metrics(y_test, lr.predict(X_test))
    model_metrics = {"rf": rf_metrics, "lr": lr_metrics}

    feature_importance = {
        col: float(imp)
        for col, imp in zip(schema["feature_columns"], rf.feature_importances_)
    }

    joblib.dump(rf, os.path.join(MODELS_DIR, "rf_model.pkl"))
    joblib.dump(lr, os.path.join(MODELS_DIR, "lr_model.pkl"))
    with open(os.path.join(MODELS_DIR, "schema.json"), "w") as f:
        json.dump(schema, f, indent=2)
    with open(os.path.join(MODELS_DIR, "feature_importance.json"), "w") as f:
        json.dump(feature_importance, f, indent=2)
    with open(os.path.join(MODELS_DIR, "feature_columns.json"), "w") as f:
        json.dump(schema["feature_columns"], f, indent=2)
    with open(os.path.join(MODELS_DIR, "model_metrics.json"), "w") as f:
        json.dump(model_metrics, f, indent=2)

    print("\n" + "=" * 50)
    print("Model performance (test set 2018-2022)")
    print("=" * 50)
    for name, m in model_metrics.items():
        label = "Random Forest" if name == "rf" else "Linear Regression"
        print(f"{label:>18}:  R2={m['r2']:.3f}  MAE={m['mae']:.2f}  RMSE={m['rmse']:.2f}")
    print("\nTop feature importances:")
    for col, imp in sorted(feature_importance.items(), key=lambda x: -x[1])[:8]:
        print(f"  {col:<22} {imp:.3f}")
    print(f"\nSaved models and metadata to {MODELS_DIR}/")


if __name__ == "__main__":
    main()
