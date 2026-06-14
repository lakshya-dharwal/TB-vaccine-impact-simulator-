"""Counterfactual simulation and bootstrap uncertainty for TB Futures."""

import numpy as np

from src.model.country_story import (
    generate_country_story,
    generate_scenario_explanation,
)
from src.model.features import build_feature_vector, income_up, vector_to_frame

DISCLAIMER = (
    "Predictions are model estimates based on historical population-level data. "
    "Not for clinical, policy, or research use without expert review."
)

N_BOOTSTRAP = 100  # exactly 100 bootstrap iterations
SCENARIOS = ["baseline", "vaccine_push", "hiv_control", "income_up", "combined"]


def get_country_row(df, country: str):
    """Return the most recent year's record for a country (as a dict)."""
    sub = df[df["country"] == country]
    if sub.empty:
        raise KeyError(f"Country not found: {country}")
    row = sub.sort_values("year").iloc[-1]
    return row.to_dict()


def _apply_scenario(values: dict, scenario: str) -> dict:
    """Return modified covariate values for a named scenario."""
    v = dict(values)
    if scenario in ("vaccine_push", "combined"):
        v["bcg_coverage"] = min((v.get("bcg_coverage") or 0) + 30, 99)
    if scenario in ("hiv_control", "combined"):
        v["hiv_prevalence"] = (v.get("hiv_prevalence") or 0) * 0.75
    if scenario in ("income_up", "combined"):
        v["income_level"] = income_up(v.get("income_level"))
    return v


def _bootstrap_ci(model, feature_frame):
    """95% interval from resampling the forest's trees 100 times."""
    estimators = getattr(model, "estimators_", None)
    if not estimators:
        point = float(model.predict(feature_frame)[0])
        return point, point

    rng = np.random.default_rng(42)
    n = len(estimators)
    # Trees are fitted on raw arrays internally; predict on values to avoid
    # sklearn's feature-name warning.
    values = feature_frame.values
    tree_preds = np.array([est.predict(values)[0] for est in estimators])

    boot_means = []
    for _ in range(N_BOOTSTRAP):
        idx = rng.integers(0, n, size=n)
        boot_means.append(float(np.mean(tree_preds[idx])))

    lower = float(np.percentile(boot_means, 2.5))
    upper = float(np.percentile(boot_means, 97.5))
    return max(lower, 0.0), max(upper, 0.0)


def simulate(country, scenario, custom_overrides, df, model, feature_columns=None):
    """Run a counterfactual simulation and return a full result dict."""
    row = get_country_row(df, country)

    current_bcg = float(row.get("bcg_coverage") or 0)
    current_hiv = float(row.get("hiv_prevalence") or 0)
    current_income = row.get("income_level")
    current_tb = float(row.get("tb_incidence") or 0)
    population = float(row.get("population") or 0)

    base_values = {
        "bcg_coverage": current_bcg,
        "hiv_prevalence": current_hiv,
        "income_level": current_income,
        "year": row.get("year"),
        "region": row.get("region"),
    }

    modified = _apply_scenario(base_values, scenario)

    # Individual slider/selector overrides take precedence over the scenario.
    if custom_overrides:
        if custom_overrides.get("bcg_coverage") is not None:
            modified["bcg_coverage"] = float(custom_overrides["bcg_coverage"])
        if custom_overrides.get("hiv_prevalence") is not None:
            modified["hiv_prevalence"] = float(custom_overrides["hiv_prevalence"])
        if custom_overrides.get("income_level") is not None:
            modified["income_level"] = custom_overrides["income_level"]

    features = build_feature_vector(modified)
    frame = vector_to_frame(features)

    predicted = max(float(model.predict(frame)[0]), 0.0)
    ci_lower, ci_upper = _bootstrap_ci(model, frame)

    absolute_reduction = current_tb - predicted
    relative_reduction_pct = (
        (absolute_reduction / current_tb * 100) if current_tb > 0 else 0.0
    )
    cases_prevented_per_year = absolute_reduction / 100000.0 * population

    story = generate_country_story(country, row)
    explanation = generate_scenario_explanation(
        country, scenario, current_tb, predicted, cases_prevented_per_year
    )

    return {
        "country": country,
        "scenario": scenario,
        "current_bcg_coverage": round(current_bcg, 1),
        "simulated_bcg_coverage": round(float(modified["bcg_coverage"]), 1),
        "current_hiv_prevalence": round(current_hiv, 2),
        "simulated_hiv_prevalence": round(float(modified["hiv_prevalence"]), 2),
        "current_income_level": current_income,
        "simulated_income_level": modified["income_level"],
        "current_tb_incidence": round(current_tb, 1),
        "predicted_tb_incidence": round(predicted, 1),
        "absolute_reduction": round(absolute_reduction, 1),
        "relative_reduction_pct": round(relative_reduction_pct, 1),
        "ci_lower": round(ci_lower, 1),
        "ci_upper": round(ci_upper, 1),
        "population": population,
        "cases_prevented_per_year": round(cases_prevented_per_year, 0),
        "country_story": story,
        "scenario_explanation": explanation,
        "disclaimer": DISCLAIMER,
    }
