"""Shared feature engineering for training and inference.

Features after the WHO-data refactor:
  bcg_coverage, hiv_prevalence, year,
  income_level one-hot (L / LM / UM / H),
  WHO region one-hot (AFR / AMR / EMR / EUR / SEA / WPR).

GDP per capita and health expenditure have been removed in favour of the WHO
`income_level` band.
"""

import numpy as np
import pandas as pd

# Fixed orders so one-hot columns are stable across train and inference.
INCOME_LEVELS = ["L", "LM", "UM", "H"]
REGIONS = ["AFR", "AMR", "EMR", "EUR", "SEA", "WPR"]

# Ordered income ladder for the "income up" scenario.
INCOME_LADDER = ["L", "LM", "UM", "H"]

NUMERIC_FEATURES = ["bcg_coverage", "hiv_prevalence", "year"]

FEATURE_COLUMNS = (
    NUMERIC_FEATURES
    + [f"income_{lvl}" for lvl in INCOME_LEVELS]
    + [f"region_{r}" for r in REGIONS]
)

DEFAULTS = {"hiv_prevalence": 0.5}


def _safe(value, key):
    if value is None or (isinstance(value, float) and np.isnan(value)):
        return DEFAULTS.get(key, 0.0)
    try:
        if pd.isna(value):
            return DEFAULTS.get(key, 0.0)
    except (TypeError, ValueError):
        pass
    return float(value)


def income_up(level: str) -> str:
    """Bump an income band up one tier (L->LM->UM->H); H stays H."""
    if level in INCOME_LADDER:
        idx = INCOME_LADDER.index(level)
        return INCOME_LADDER[min(idx + 1, len(INCOME_LADDER) - 1)]
    return level


def build_feature_vector(row) -> dict:
    """Turn a country-year record (dict or pandas Series) into model features."""
    features = {
        "bcg_coverage": _safe(row.get("bcg_coverage"), "bcg_coverage"),
        "hiv_prevalence": _safe(row.get("hiv_prevalence"), "hiv_prevalence"),
        "year": _safe(row.get("year"), "year"),
    }
    income = row.get("income_level")
    for lvl in INCOME_LEVELS:
        features[f"income_{lvl}"] = 1.0 if income == lvl else 0.0

    region = row.get("region")
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
