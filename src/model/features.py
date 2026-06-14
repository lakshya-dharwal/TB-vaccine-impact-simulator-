"""Shared feature engineering for training and inference.

Keeping this in one place guarantees the model is trained and queried with an
identical column layout.
"""

import numpy as np
import pandas as pd

# Fixed region order so one-hot columns are stable across train and inference.
REGIONS = ["AFR", "AMR", "EMR", "EUR", "SEAR", "WPR"]

NUMERIC_FEATURES = [
    "bcg_coverage",
    "log_gdp",
    "health_expenditure",
    "hiv_prevalence",
    "year",
]

FEATURE_COLUMNS = NUMERIC_FEATURES + [f"region_{r}" for r in REGIONS]

# Sensible fallbacks when a country/year is missing a covariate.
DEFAULTS = {
    "gdp_per_capita": 5000.0,
    "health_expenditure": 6.0,
    "hiv_prevalence": 0.5,
}


def _safe(value, key):
    if value is None or (isinstance(value, float) and np.isnan(value)):
        return DEFAULTS.get(key, 0.0)
    try:
        if pd.isna(value):
            return DEFAULTS.get(key, 0.0)
    except (TypeError, ValueError):
        pass
    return float(value)


def build_feature_vector(row) -> dict:
    """Turn a country-year record (dict or pandas Series) into model features."""
    bcg = _safe(row.get("bcg_coverage"), "bcg_coverage")
    gdp = _safe(row.get("gdp_per_capita"), "gdp_per_capita")
    health = _safe(row.get("health_expenditure"), "health_expenditure")
    hiv = _safe(row.get("hiv_prevalence"), "hiv_prevalence")
    year = _safe(row.get("year"), "year")
    region = row.get("region", "OTHER")

    features = {
        "bcg_coverage": bcg,
        "log_gdp": float(np.log(max(gdp, 1.0))),
        "health_expenditure": health,
        "hiv_prevalence": hiv,
        "year": year,
    }
    for r in REGIONS:
        features[f"region_{r}"] = 1.0 if region == r else 0.0
    return features


def build_feature_matrix(df: pd.DataFrame) -> pd.DataFrame:
    """Build an aligned feature matrix for an entire dataframe."""
    rows = [build_feature_vector(r) for _, r in df.iterrows()]
    return pd.DataFrame(rows, columns=FEATURE_COLUMNS)


def vector_to_frame(features: dict) -> pd.DataFrame:
    """Order a single feature dict into a one-row DataFrame for prediction."""
    return pd.DataFrame([{col: features[col] for col in FEATURE_COLUMNS}])
