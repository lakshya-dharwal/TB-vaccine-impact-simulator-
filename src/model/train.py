"""Train the TB Futures models.

Predicts WHO-estimated TB incidence per 100k from BCG coverage, log(GDP), income
band, and WHO region. The right-skewed target is modelled in log space. The
Random Forest is tuned with a year-grouped cross-validation; a Linear Regression
and a Gradient Boosting model are trained as comparison baselines. Temporal
split: train 2000-2017, test 2018-2023.
"""

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
from sklearn.model_selection import GroupKFold, RandomizedSearchCV

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src.model.features import build_feature_matrix, detect_schema

DATA_PATH = "data/processed/merged_tb_dataset.csv"
MODELS_DIR = "models"
DOCS_DIR = "docs"
TARGET = "tb_incidence"
TRAIN_END = 2017

RF_PARAM_DIST = {
    "n_estimators": [200, 300, 400, 600],
    "max_depth": [None, 8, 12, 16, 24],
    "min_samples_leaf": [1, 2, 4, 8],
    "max_features": [0.5, 0.7, 1.0, "sqrt"],
}


def metrics(y_true, y_pred) -> dict:
    return {
        "r2": float(r2_score(y_true, y_pred)),
        "r2_log": float(r2_score(np.log1p(y_true), np.log1p(np.clip(y_pred, 0, None)))),
        "mae": float(mean_absolute_error(y_true, y_pred)),
        "rmse": float(np.sqrt(mean_squared_error(y_true, y_pred))),
    }


def main():
    os.makedirs(MODELS_DIR, exist_ok=True)
    os.makedirs(DOCS_DIR, exist_ok=True)
    df = pd.read_csv(DATA_PATH)

    schema = detect_schema(df)
    schema["log_target"] = True  # right-skewed target modelled in log space
    print(f"Feature columns ({len(schema['feature_columns'])}): {schema['feature_columns']}")
    print(f"Scenarios: {schema['scenarios']}")

    train_df = df[df["year"] <= TRAIN_END].copy()
    test_df = df[df["year"] > TRAIN_END].copy()

    X_train = build_feature_matrix(train_df, schema)
    X_test = build_feature_matrix(test_df, schema)
    y_train = train_df[TARGET].values
    y_test = test_df[TARGET].values
    y_train_log = np.log1p(y_train)
    print(f"Training rows: {len(X_train)} | Test rows: {len(X_test)}")

    # Year-grouped CV avoids leaking the same year across folds (panel data).
    groups = train_df["year"].values
    cv = GroupKFold(n_splits=5)

    search = RandomizedSearchCV(
        RandomForestRegressor(random_state=42, n_jobs=-1),
        RF_PARAM_DIST, n_iter=25, cv=cv, scoring="r2",
        random_state=42, n_jobs=-1,
    )
    search.fit(X_train, y_train_log, groups=groups)
    rf = search.best_estimator_
    print(f"Best RF params: {search.best_params_} | CV R2(log): {search.best_score_:.3f}")

    lr = LinearRegression().fit(X_train, y_train_log)
    gbm = GradientBoostingRegressor(random_state=42).fit(X_train, y_train_log)

    def predict_orig(model):
        return np.clip(np.expm1(model.predict(X_test)), 0, None)

    model_metrics = {
        "rf": metrics(y_test, predict_orig(rf)),
        "lr": metrics(y_test, predict_orig(lr)),
        "gbm": metrics(y_test, predict_orig(gbm)),
        "rf_best_params": search.best_params_,
        "rf_cv_r2_log": float(search.best_score_),
    }

    feature_importance = {
        col: float(imp) for col, imp in zip(schema["feature_columns"], rf.feature_importances_)
    }

    # Diagnostics: test predictions + error broken down by region and income.
    y_pred_rf = predict_orig(rf)
    diag_df = test_df.assign(y_true=y_test, y_pred=y_pred_rf,
                             abs_err=np.abs(y_test - y_pred_rf))
    by_region = diag_df.groupby("region")["abs_err"].mean().round(1).to_dict()
    by_income = diag_df.groupby("income_level")["abs_err"].mean().round(1).to_dict()
    diagnostics = {
        "y_true": [round(float(v), 1) for v in y_test],
        "y_pred": [round(float(v), 1) for v in y_pred_rf],
        "mae_by_region": by_region,
        "mae_by_income": by_income,
    }

    joblib.dump(rf, os.path.join(MODELS_DIR, "rf_model.pkl"))
    joblib.dump(lr, os.path.join(MODELS_DIR, "lr_model.pkl"))
    joblib.dump(gbm, os.path.join(MODELS_DIR, "gbm_model.pkl"))
    for name, obj in [
        ("schema.json", schema),
        ("feature_columns.json", schema["feature_columns"]),
        ("feature_importance.json", feature_importance),
        ("model_metrics.json", model_metrics),
        ("diagnostics.json", diagnostics),
    ]:
        with open(os.path.join(MODELS_DIR, name), "w") as f:
            json.dump(obj, f, indent=2)

    _write_model_card(model_metrics, schema, len(X_train), len(X_test), df)

    print("\n" + "=" * 50)
    print("Model performance (test set 2018-2023, original scale)")
    print("=" * 50)
    for key, label in [("rf", "Random Forest"), ("lr", "Linear Regression"),
                       ("gbm", "Gradient Boosting")]:
        m = model_metrics[key]
        print(f"{label:>18}:  R2={m['r2']:.3f}  R2(log)={m['r2_log']:.3f}  "
              f"MAE={m['mae']:.2f}  RMSE={m['rmse']:.2f}")
    print("\nTop feature importances:")
    for col, imp in sorted(feature_importance.items(), key=lambda x: -x[1])[:8]:
        print(f"  {col:<22} {imp:.3f}")
    print(f"\nSaved models, metadata, diagnostics, and model card.")


def _write_model_card(m, schema, n_train, n_test, df):
    rf = m["rf"]
    card = f"""# TB Futures — Model Card

## Intended use
Educational / portfolio what-if exploration of how vaccination coverage, income,
and economic conditions relate to national tuberculosis burden, and prioritisation
of where BCG scale-up could avert the most cases. **Not** for clinical, policy, or
research decisions without expert review.

## Model
- Algorithm: Random Forest Regressor (tuned), with Linear Regression and Gradient
  Boosting as comparison baselines.
- Target: WHO modeled TB incidence per 100,000 (OWID SDG series), modelled in
  log space (`log1p`/`expm1`).
- Features: {", ".join(schema['feature_columns'])}.
- Tuning: randomized search over forest hyperparameters with 5-fold year-grouped
  cross-validation. Best params: {m['rf_best_params']}.

## Data
- {df['country'].nunique()} countries, {int(df['year'].min())}–{int(df['year'].max())}.
- Train rows (2000–2017): {n_train}. Test rows (2018–2023, held out): {n_test}.
- Sources: WHO Global TB Programme (incidence, income band, region),
  WHO/UNICEF (BCG), World Bank/OWID (GDP, population). Rapid-diagnostics-sites is
  shown as context only (too sparse to model).

## Performance (held-out test set, original scale)
| Metric | Random Forest | Linear Regression | Gradient Boosting |
|---|---|---|---|
| R² | {rf['r2']:.3f} | {m['lr']['r2']:.3f} | {m['gbm']['r2']:.3f} |
| MAE (/100k) | {rf['mae']:.1f} | {m['lr']['mae']:.1f} | {m['gbm']['mae']:.1f} |
| RMSE (/100k) | {rf['rmse']:.1f} | {m['lr']['rmse']:.1f} | {m['gbm']['rmse']:.1f} |

## Limitations
The model captures population-level statistical associations, not causation.
BCG is a childhood vaccine with limited adult efficacy, so its modelled effect is
partly a proxy for broader health-system strength. HIV prevalence and health
expenditure — both important TB drivers — are absent from the current data.
Counterfactual scenarios hold all other factors fixed, which rarely holds in
reality. Uncertainty intervals reflect model variance, not epidemiological certainty.
"""
    with open(os.path.join(DOCS_DIR, "MODEL_CARD.md"), "w") as f:
        f.write(card)


if __name__ == "__main__":
    main()
