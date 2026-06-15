"""Train the TB Futures models on the processed OWID + WHO dataset."""

import json
import os
import sys
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import RandomizedSearchCV, TimeSeriesSplit

# Allow running as a script (`python src/model/train.py`) as well as a module.
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src.model.features import build_feature_matrix, detect_schema

DATA_PATH = "data/processed/merged_tb_dataset.csv"
MODELS_DIR = "models"
DOCS_DIR = "docs"
TARGET = "tb_incidence"
TRAIN_END = 2018
N_SEARCH = 16


def _metrics(y_true, y_pred) -> dict:
    return {
        "r2": float(r2_score(y_true, y_pred)),
        "mae": float(mean_absolute_error(y_true, y_pred)),
        "rmse": float(np.sqrt(mean_squared_error(y_true, y_pred))),
    }


def _diagnostics_frame(df: pd.DataFrame, y_true, y_pred) -> pd.DataFrame:
    out = df[["country", "year", "region", "income_level"]].copy()
    out["actual"] = y_true
    out["predicted"] = y_pred
    out["residual"] = out["predicted"] - out["actual"]
    out["abs_error"] = np.abs(out["residual"])
    return out


def _group_diagnostics(df: pd.DataFrame, column: str) -> list[dict]:
    rows = []
    for key, group in df.groupby(column):
        rows.append(
            {
                column: key,
                "count": int(len(group)),
                "mae": round(float(group["abs_error"].mean()), 2),
                "bias": round(float(group["residual"].mean()), 2),
                "rmse": round(float(np.sqrt(np.mean(group["residual"] ** 2))), 2),
            }
        )
    return rows


def _write_model_card(schema: dict, metrics: dict, diagnostics: dict):
    os.makedirs(DOCS_DIR, exist_ok=True)
    text = f"""# TB Futures Model Card

## Intended Use

TB Futures is a country-level educational what-if simulator for tuberculosis prevention and prioritization.
It is appropriate for exploratory portfolio demos and directional screening, not for policy implementation,
clinical use, or causal claims.

## Data

- Target: {schema['target_display']}
- Time window: 2000-2023
- Features: {", ".join(schema['feature_columns'])}
- Context-only column: rapid diagnostic sites per million population

## Training Setup

- Target transform: log1p / expm1
- Train period: 2000-{TRAIN_END}
- Test period: {TRAIN_END + 1}-2023
- Random Forest tuned with RandomizedSearchCV + TimeSeriesSplit

## Held-out Metrics

- Random Forest: R²={metrics['rf']['r2']:.3f}, MAE={metrics['rf']['mae']:.1f}, RMSE={metrics['rf']['rmse']:.1f}
- Linear Regression: R²={metrics['lr']['r2']:.3f}, MAE={metrics['lr']['mae']:.1f}, RMSE={metrics['lr']['rmse']:.1f}
- Gradient Boosting: R²={metrics['gbm']['r2']:.3f}, MAE={metrics['gbm']['mae']:.1f}, RMSE={metrics['gbm']['rmse']:.1f}

## Key Limitations

- Country-level associations are not causal effects.
- BCG coverage and GDP are incomplete proxies for prevention and system strength.
- Rapid diagnostic site density is shown as context only and is not part of the trained model.
- Error is not uniform across regions and income bands; inspect the diagnostics tables in the app.

## Diagnostics Snapshot

- Region rows: {len(diagnostics['by_region'])}
- Income rows: {len(diagnostics['by_income'])}
"""
    with open(os.path.join(DOCS_DIR, "MODEL_CARD.md"), "w") as f:
        f.write(text)


def main():
    os.makedirs(MODELS_DIR, exist_ok=True)
    os.makedirs(DOCS_DIR, exist_ok=True)

    df = pd.read_csv(DATA_PATH).sort_values(["year", "country"]).reset_index(drop=True)
    schema = detect_schema(df)
    schema["log_target"] = True
    schema["target_transform"] = "log1p"

    print(f"Feature columns ({len(schema['feature_columns'])}): {schema['feature_columns']}")
    print(f"Scenarios: {schema['scenarios']}")

    train_df = df[df["year"] <= TRAIN_END].copy()
    test_df = df[df["year"] > TRAIN_END].copy()

    X_train = build_feature_matrix(train_df, schema)
    X_test = build_feature_matrix(test_df, schema)
    y_train = np.log1p(train_df[TARGET].values)
    y_test_raw = test_df[TARGET].values

    print(f"Training rows: {len(X_train)} | Test rows: {len(X_test)}")

    rf = RandomForestRegressor(random_state=42, n_jobs=-1)
    cv = TimeSeriesSplit(n_splits=5)
    search = RandomizedSearchCV(
        estimator=rf,
        param_distributions={
            "n_estimators": [200, 300, 400, 500],
            "max_depth": [None, 8, 12, 16, 20],
            "min_samples_leaf": [1, 2, 4, 8],
            "max_features": [0.5, 0.7, "sqrt", None],
        },
        n_iter=N_SEARCH,
        scoring="r2",
        cv=cv,
        random_state=42,
        n_jobs=-1,
        verbose=0,
    )
    search.fit(X_train, y_train)
    rf_best = search.best_estimator_

    lr = LinearRegression()
    lr.fit(X_train, y_train)

    gbm = GradientBoostingRegressor(random_state=42)
    gbm.fit(X_train, y_train)

    def predict_original(model, X):
        return np.maximum(np.expm1(model.predict(X)), 0.0)

    rf_pred = predict_original(rf_best, X_test)
    lr_pred = predict_original(lr, X_test)
    gbm_pred = predict_original(gbm, X_test)

    model_metrics = {
        "rf": _metrics(y_test_raw, rf_pred),
        "lr": _metrics(y_test_raw, lr_pred),
        "gbm": _metrics(y_test_raw, gbm_pred),
        "rf_best_params": search.best_params_,
        "rf_cv_best_score": float(search.best_score_),
        "rf_cv_scoring": "r2",
        "target_transform": "log1p",
        "train_rows": int(len(X_train)),
        "test_rows": int(len(X_test)),
    }

    feature_importance = {
        col: float(imp)
        for col, imp in zip(schema["feature_columns"], rf_best.feature_importances_)
    }

    diag_df = _diagnostics_frame(test_df, y_test_raw, rf_pred)
    diagnostics = {
        "by_region": _group_diagnostics(diag_df, "region"),
        "by_income": _group_diagnostics(diag_df, "income_level"),
        "scatter_sample": diag_df.sort_values("abs_error", ascending=False)
        .head(250)[["country", "year", "actual", "predicted", "region", "income_level"]]
        .to_dict(orient="records"),
    }

    _write_model_card(schema, model_metrics, diagnostics)

    joblib.dump(rf_best, os.path.join(MODELS_DIR, "rf_model.pkl"))
    joblib.dump(lr, os.path.join(MODELS_DIR, "lr_model.pkl"))
    joblib.dump(gbm, os.path.join(MODELS_DIR, "gbm_model.pkl"))
    with open(os.path.join(MODELS_DIR, "schema.json"), "w") as f:
        json.dump(schema, f, indent=2)
    with open(os.path.join(MODELS_DIR, "feature_importance.json"), "w") as f:
        json.dump(feature_importance, f, indent=2)
    with open(os.path.join(MODELS_DIR, "feature_columns.json"), "w") as f:
        json.dump(schema["feature_columns"], f, indent=2)
    with open(os.path.join(MODELS_DIR, "model_metrics.json"), "w") as f:
        json.dump(model_metrics, f, indent=2)
    with open(os.path.join(MODELS_DIR, "diagnostics.json"), "w") as f:
        json.dump(diagnostics, f, indent=2)

    print("\n" + "=" * 50)
    print(f"Model performance (test set {TRAIN_END + 1}-2023)")
    print("=" * 50)
    for name in ("rf", "lr", "gbm"):
        label = {
            "rf": "Random Forest",
            "lr": "Linear Regression",
            "gbm": "Gradient Boosting",
        }[name]
        m = model_metrics[name]
        print(f"{label:>18}:  R2={m['r2']:.3f}  MAE={m['mae']:.2f}  RMSE={m['rmse']:.2f}")
    print(f"\nBest RF params: {search.best_params_}")
    print(f"Best RF CV score ({model_metrics['rf_cv_scoring']}): {model_metrics['rf_cv_best_score']:.3f}")
    print("\nTop feature importances:")
    for col, imp in sorted(feature_importance.items(), key=lambda x: -x[1])[:8]:
        print(f"  {col:<22} {imp:.3f}")
    print(f"\nSaved models and metadata to {MODELS_DIR}/")


if __name__ == "__main__":
    main()
