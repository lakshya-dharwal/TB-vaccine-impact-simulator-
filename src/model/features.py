"""Data-adaptive feature engineering for TB Futures.

The set of model features depends on which raw data files were available when
the dataset was built. The WHO file always supplies year, region, income level,
population, and the TB target. Each of BCG coverage, HIV prevalence, GDP per
capita, and health expenditure is included only if its column carries data.

`detect_schema` inspects the processed dataframe and returns the exact feature
layout, available scenarios, and category levels. The schema is saved at train
time (models/schema.json) and reused everywhere downstream so training and
inference always agree.
"""

import numpy as np
import pandas as pd

INCOME_ORDER = ["L", "LM", "UM", "H"]

# Optional numeric covariates and the raw column each derives from.
# (feature_name, source_column)
OPTIONAL_NUMERIC = [
    ("bcg_coverage", "bcg_coverage"),
    ("hiv_prevalence", "hiv_prevalence"),
    ("log_gdp", "gdp_per_capita"),
    ("health_expenditure", "health_expenditure"),
]

DEFAULTS = {"hiv_prevalence": 0.5, "health_expenditure": 6.0, "gdp_per_capita": 5000.0}

# Which scenario each optional numeric lever unlocks. Income level is a model
# feature for context, NOT an intervention lever (a one-tier jump is not a
# credible, graded what-if), so it is deliberately absent here.
LEVER_SCENARIO = {
    "bcg_coverage": "vaccine_push",
    "hiv_prevalence": "hiv_control",
    "health_expenditure": "health_boost",
    "log_gdp": "econ_dev",
}


def _has_data(df: pd.DataFrame, col: str) -> bool:
    return col in df.columns and df[col].notna().any()


def detect_schema(df: pd.DataFrame) -> dict:
    """Inspect the processed dataframe and return the feature/scenario layout."""
    numeric = []
    for feat, source in OPTIONAL_NUMERIC:
        if _has_data(df, source):
            numeric.append(feat)
    numeric.append("year")  # always present

    use_income = bool(_has_data(df, "income_level"))
    income_levels = (
        [lvl for lvl in INCOME_ORDER if (df["income_level"] == lvl).any()]
        if use_income else []
    )
    regions = sorted(df["region"].dropna().unique().tolist()) if "region" in df else []

    feature_columns = (
        list(numeric)
        + [f"income_{lvl}" for lvl in income_levels]
        + [f"region_{r}" for r in regions]
    )

    scenarios = ["baseline"]
    for lever in ("bcg_coverage", "hiv_prevalence", "health_expenditure", "log_gdp"):
        if lever in numeric:
            scenarios.append(LEVER_SCENARIO[lever])
    if len(scenarios) > 1:
        scenarios.append("combined")

    return {
        "numeric": numeric,
        "income_levels": income_levels,
        "regions": regions,
        "feature_columns": feature_columns,
        "scenarios": scenarios,
        "use_income": use_income,
        # raw covariate (source) names actually modelled — used by the UI/API
        "covariates": [src for feat, src in OPTIONAL_NUMERIC if feat in numeric]
        + (["income_level"] if use_income else []),
    }


def _safe(value, default=0.0):
    if value is None:
        return default
    try:
        if pd.isna(value):
            return default
    except (TypeError, ValueError):
        pass
    return float(value)


def income_up(level: str) -> str:
    """Bump an income band up one tier (L->LM->UM->H); H stays H."""
    if level in INCOME_ORDER:
        return INCOME_ORDER[min(INCOME_ORDER.index(level) + 1, len(INCOME_ORDER) - 1)]
    return level


def build_feature_vector(values: dict, schema: dict) -> dict:
    """Turn raw covariate values into the schema's feature columns."""
    out = {}
    for feat in schema["numeric"]:
        if feat == "log_gdp":
            gdp = _safe(values.get("gdp_per_capita"), DEFAULTS["gdp_per_capita"])
            out[feat] = float(np.log(max(gdp, 1.0)))
        elif feat == "year":
            out[feat] = _safe(values.get("year"))
        else:
            out[feat] = _safe(values.get(feat), DEFAULTS.get(feat, 0.0))

    income = values.get("income_level")
    for lvl in schema["income_levels"]:
        out[f"income_{lvl}"] = 1.0 if income == lvl else 0.0

    region = values.get("region")
    for r in schema["regions"]:
        out[f"region_{r}"] = 1.0 if region == r else 0.0
    return out


def build_feature_matrix(df: pd.DataFrame, schema: dict) -> pd.DataFrame:
    """Build an aligned feature matrix for an entire dataframe."""
    rows = [build_feature_vector(r.to_dict(), schema) for _, r in df.iterrows()]
    return pd.DataFrame(rows, columns=schema["feature_columns"])


def vector_to_frame(features: dict, schema: dict) -> pd.DataFrame:
    """Order a single feature dict into a one-row DataFrame for prediction."""
    return pd.DataFrame([{col: features[col] for col in schema["feature_columns"]}])
