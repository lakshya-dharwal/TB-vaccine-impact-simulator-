"""Tests for the trained model and simulation logic."""

import json
import os

import joblib
import pandas as pd
import pytest

from src.model.predict import prioritize, simulate

DATA_PATH = "data/processed/merged_tb_dataset.csv"
MODEL_PATH = "models/rf_model.pkl"
SCHEMA_PATH = "models/schema.json"

pytestmark = pytest.mark.skipif(
    not (os.path.exists(DATA_PATH) and os.path.exists(MODEL_PATH)
         and os.path.exists(SCHEMA_PATH)),
    reason="Model/data artifacts not built. Run the data + train pipeline first.",
)

# Keys always returned by simulate (covariate pairs may be None but are present).
EXPECTED_KEYS = {
    "country", "scenario", "current_tb_incidence", "predicted_tb_incidence",
    "absolute_reduction", "relative_reduction_pct", "ci_lower", "ci_upper",
    "population", "cases_prevented_per_year", "country_story",
    "scenario_explanation", "disclaimer",
}


@pytest.fixture(scope="module")
def df():
    return pd.read_csv(DATA_PATH)


@pytest.fixture(scope="module")
def model():
    return joblib.load(MODEL_PATH)


@pytest.fixture(scope="module")
def schema():
    with open(SCHEMA_PATH) as f:
        return json.load(f)


def _some_countries(df, n=3):
    return df["country"].drop_duplicates().head(n).tolist()


def test_model_loads(model):
    assert model is not None and hasattr(model, "predict")


def test_prediction_has_all_keys(df, model, schema):
    country = _some_countries(df, 1)[0]
    result = simulate(country, schema["scenarios"][-1], {}, df, model, schema)
    assert EXPECTED_KEYS.issubset(set(result.keys()))


def test_predicted_is_positive_float(df, model, schema):
    country = _some_countries(df, 1)[0]
    result = simulate(country, "baseline", {}, df, model, schema)
    assert isinstance(result["predicted_tb_incidence"], float)
    assert result["predicted_tb_incidence"] >= 0


def test_ci_brackets_prediction(df, model, schema):
    country = _some_countries(df, 1)[0]
    result = simulate(country, "baseline", {}, df, model, schema)
    assert result["ci_lower"] <= result["predicted_tb_incidence"] <= result["ci_upper"]


def test_all_scenarios_run_for_several_countries(df, model, schema):
    for country in _some_countries(df, 3):
        for scenario in schema["scenarios"]:
            result = simulate(country, scenario, {}, df, model, schema)
            assert result["predicted_tb_incidence"] >= 0


def test_schema_uses_log_target(schema):
    assert schema["log_target"] is True
    assert schema["target_transform"] == "log1p"


def test_prioritize_returns_ranked_rows(df, model, schema):
    rows = prioritize(df, model, schema, bcg_target=90, top=10)
    assert len(rows) == 10
    assert rows[0]["cases_prevented_per_year"] >= rows[-1]["cases_prevented_per_year"]
