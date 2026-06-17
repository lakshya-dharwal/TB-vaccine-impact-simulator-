"""Counterfactual simulation, bootstrap uncertainty, and prioritisation."""

import numpy as np

from src.model.country_story import (
    generate_country_story,
    generate_scenario_explanation,
)
from src.model.features import build_feature_vector, vector_to_frame

DISCLAIMER = (
    "Predictions are model estimates based on historical population-level data. "
    "Not for clinical, policy, or research use without expert review."
)

N_BOOTSTRAP = 100  # exactly 100 bootstrap iterations


def get_country_row(df, country: str):
    """Return the most recent year's record for a country (as a dict)."""
    sub = df[df["country"] == country]
    if sub.empty:
        raise KeyError(f"Country not found: {country}")
    return sub.sort_values("year").iloc[-1].to_dict()


def _apply_scenario(values: dict, scenario: str, schema: dict) -> dict:
    """Return modified covariate values for a named scenario, honouring the schema."""
    v = dict(values)
    numeric = schema["numeric"]
    if scenario in ("vaccine_push", "combined") and "bcg_coverage" in numeric:
        v["bcg_coverage"] = min((v.get("bcg_coverage") or 0) + 30, 99)
    if scenario in ("hiv_control", "combined") and "hiv_prevalence" in numeric:
        v["hiv_prevalence"] = (v.get("hiv_prevalence") or 0) * 0.75
    if scenario in ("health_boost", "combined") and "health_expenditure" in numeric:
        v["health_expenditure"] = (v.get("health_expenditure") or 0) * 1.25
    if scenario in ("econ_dev", "combined") and "log_gdp" in numeric:
        v["gdp_per_capita"] = (v.get("gdp_per_capita") or 0) * 1.25
    return v


def _predict_with_ci(model, frame, log_target):
    """Point prediction and 95% interval (100 tree-bootstraps) in original units."""
    estimators = getattr(model, "estimators_", None)
    if not estimators:
        point = float(model.predict(frame)[0])
        if log_target:
            point = float(np.expm1(point))
        point = max(point, 0.0)
        return point, point, point

    values = frame.values
    tree_preds = np.array([est.predict(values)[0] for est in estimators])
    if log_target:
        tree_preds = np.expm1(tree_preds)
    tree_preds = np.clip(tree_preds, 0, None)

    point = float(tree_preds.mean())
    rng = np.random.default_rng(42)
    n = len(tree_preds)
    boot = [float(tree_preds[rng.integers(0, n, size=n)].mean())
            for _ in range(N_BOOTSTRAP)]
    return point, max(float(np.percentile(boot, 2.5)), 0.0), \
        max(float(np.percentile(boot, 97.5)), 0.0)


def _round(value, ndigits=1):
    return round(float(value), ndigits) if value is not None else None


def simulate(country, scenario, custom_overrides, df, model, schema):
    """Run a counterfactual simulation and return a full result dict."""
    row = get_country_row(df, country)
    log_target = schema.get("log_target", False)

    current_tb = float(row.get("tb_incidence") or 0)
    population = float(row.get("population") or 0)

    base_values = {
        "bcg_coverage": row.get("bcg_coverage"),
        "hiv_prevalence": row.get("hiv_prevalence"),
        "gdp_per_capita": row.get("gdp_per_capita"),
        "health_expenditure": row.get("health_expenditure"),
        "income_level": row.get("income_level"),
        "year": row.get("year"),
        "region": row.get("region"),
    }
    modified = _apply_scenario(base_values, scenario, schema)

    if custom_overrides:
        for key in ("bcg_coverage", "hiv_prevalence", "gdp_per_capita",
                    "health_expenditure", "income_level"):
            val = custom_overrides.get(key)
            if val is not None:
                modified[key] = val if key == "income_level" else float(val)

    # Counterfactual anchoring: the model estimates the CHANGE from the country's
    # own baseline (both predicted by the model, so model error cancels), and that
    # change is applied to the real observed incidence. This isolates the
    # intervention effect instead of conflating it with the model's baseline error.
    base_frame = vector_to_frame(build_feature_vector(base_values, schema), schema)
    mod_frame = vector_to_frame(build_feature_vector(modified, schema), schema)
    base_point, _, _ = _predict_with_ci(model, base_frame, log_target)
    mod_point, mod_lo, mod_hi = _predict_with_ci(model, mod_frame, log_target)

    delta = mod_point - base_point  # negative = reduction
    predicted = max(current_tb + delta, 0.0)
    ci_lower = max(predicted + (mod_lo - mod_point), 0.0)
    ci_upper = max(predicted + (mod_hi - mod_point), 0.0)

    absolute_reduction = current_tb - predicted
    relative_reduction_pct = (
        (absolute_reduction / current_tb * 100) if current_tb > 0 else 0.0
    )
    cases_prevented_per_year = absolute_reduction / 100000.0 * population

    numeric = schema["numeric"]

    def cov(key, current):
        if key == "income_level":
            present = schema["use_income"]
        else:
            present = key in numeric or (key == "gdp_per_capita" and "log_gdp" in numeric)
        if not present:
            return None, None
        sim = modified.get(key)
        if key == "income_level":
            return current, sim
        nd = 2 if key in ("hiv_prevalence", "health_expenditure") else 1
        return _round(current, nd), _round(sim, nd)

    cur_bcg, sim_bcg = cov("bcg_coverage", row.get("bcg_coverage"))
    cur_hiv, sim_hiv = cov("hiv_prevalence", row.get("hiv_prevalence"))
    cur_gdp, sim_gdp = cov("gdp_per_capita", row.get("gdp_per_capita"))
    cur_health, sim_health = cov("health_expenditure", row.get("health_expenditure"))
    cur_income, sim_income = cov("income_level", row.get("income_level"))

    return {
        "country": country,
        "scenario": scenario,
        "current_bcg_coverage": cur_bcg,
        "simulated_bcg_coverage": sim_bcg,
        "current_hiv_prevalence": cur_hiv,
        "simulated_hiv_prevalence": sim_hiv,
        "current_gdp_per_capita": cur_gdp,
        "simulated_gdp_per_capita": sim_gdp,
        "current_health_expenditure": cur_health,
        "simulated_health_expenditure": sim_health,
        "current_income_level": cur_income,
        "simulated_income_level": sim_income,
        "current_tb_incidence": round(current_tb, 1),
        "predicted_tb_incidence": round(predicted, 1),
        "absolute_reduction": round(absolute_reduction, 1),
        "relative_reduction_pct": round(relative_reduction_pct, 1),
        "ci_lower": round(ci_lower, 1),
        "ci_upper": round(ci_upper, 1),
        "population": population,
        "cases_prevented_per_year": round(cases_prevented_per_year, 0),
        "country_story": generate_country_story(country, row),
        "scenario_explanation": generate_scenario_explanation(
            country, scenario, current_tb, predicted, cases_prevented_per_year),
        "disclaimer": DISCLAIMER,
    }


def prioritize(df, model, schema, bcg_target=90.0, top=None):
    """Rank countries by estimated TB cases prevented per year under a BCG target.

    For each country the most recent year's BCG coverage is raised to `bcg_target`
    (only where that is an increase) and the resulting reduction in predicted
    incidence is converted to cases prevented using population.
    """
    rows = []
    for country in df["country"].unique():
        latest = df[df["country"] == country].sort_values("year").iloc[-1]
        current_bcg = float(latest.get("bcg_coverage") or 0)
        res = simulate(country, "custom", {"bcg_coverage": max(current_bcg, bcg_target)},
                       df, model, schema)
        rows.append({
            "country": country,
            "iso3": latest["iso3"],
            "region": latest.get("region"),
            "income_level": latest.get("income_level"),
            "current_bcg_coverage": res["current_bcg_coverage"],
            "target_bcg_coverage": round(max(current_bcg, bcg_target), 1),
            "current_tb_incidence": res["current_tb_incidence"],
            "predicted_tb_incidence": res["predicted_tb_incidence"],
            "relative_reduction_pct": res["relative_reduction_pct"],
            "population": res["population"],
            "cases_prevented_per_year": max(res["cases_prevented_per_year"], 0),
        })
    rows.sort(key=lambda r: r["cases_prevented_per_year"], reverse=True)
    return rows[:top] if top else rows
