"""Tests for the trained model and simulation logic."""

import os

import joblib
import pandas as pd
import pytest

from src.model.predict import simulate

DATA_PATH = "data/processed/merged_tb_dataset.csv"
MODEL_PATH = "models/rf_model.pkl"

pytestmark = pytest.mark.skipif(
    not (os.path.exists(DATA_PATH) and os.path.exists(MODEL_PATH)),
    reason="Model/data artifacts not built. Run the data + train pipeline first.",
)

EXPECTED_KEYS = {
    "country", "scenario", "current_bcg_coverage", "simulated_bcg_coverage",
    "current_hiv_prevalence", "simulated_hiv_prevalence", "current_income_level",
    "simulated_income_level", "current_tb_incidence", "predicted_tb_incidence",
    "absolute_reduction", "relative_reduction_pct", "ci_lower", "ci_upper",
    "population", "cases_prevented_per_year", "country_story",
    "scenario_explanation", "disclaimer",
}

SCENARIOS = ["baseline", "vaccine_push", "hiv_control", "income_up", "combined"]


@pytest.fixture(scope="module")
def df():
    return pd.read_csv(DATA_PATH)


@pytest.fixture(scope="module")
def model():
    return joblib.load(MODEL_PATH)


def _some_countries(df, n=3):
    return df["country"].drop_duplicates().head(n).tolist()


def test_model_loads(model):
    assert model is not None
    assert hasattr(model, "predict")


def test_prediction_has_all_keys(df, model):
    country = _some_countries(df, 1)[0]
    result = simulate(country, "vaccine_push", {}, df, model)
    assert EXPECTED_KEYS.issubset(set(result.keys()))


def test_predicted_is_positive_float(df, model):
    country = _some_countries(df, 1)[0]
    result = simulate(country, "combined", {}, df, model)
    assert isinstance(result["predicted_tb_incidence"], float)
    assert result["predicted_tb_incidence"] >= 0


def test_ci_brackets_prediction(df, model):
    country = _some_countries(df, 1)[0]
    result = simulate(country, "baseline", {}, df, model)
    assert result["ci_lower"] <= result["predicted_tb_incidence"] <= result["ci_upper"]


def test_all_scenarios_run_for_several_countries(df, model):
    for country in _some_countries(df, 3):
        for scenario in SCENARIOS:
            result = simulate(country, scenario, {}, df, model)
            assert result["predicted_tb_incidence"] >= 0
