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

N_BOOTSTRAP = 100


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
    if scenario in ("income_up", "combined") and schema["use_income"]:
        v["income_level"] = income_up(v.get("income_level"))
    return v


def _inverse_target(value: float, schema: dict) -> float:
    """Invert the trained target transform back into TB incidence space."""
    if schema.get("log_target"):
        return max(float(np.expm1(value)), 0.0)
    return max(float(value), 0.0)


def _predict_point(model, feature_frame, schema: dict) -> float:
    return _inverse_target(float(model.predict(feature_frame)[0]), schema)


def _bootstrap_ci(model, feature_frame, schema: dict):
    """95% interval from resampling the forest's trees 100 times."""
    estimators = getattr(model, "estimators_", None)
    if not estimators:
        point = _predict_point(model, feature_frame, schema)
        return point, point

    rng = np.random.default_rng(42)
    n = len(estimators)
    values = feature_frame.values
    tree_preds = np.array([est.predict(values)[0] for est in estimators], dtype=float)

    boot_means = []
    for _ in range(N_BOOTSTRAP):
        idx = rng.integers(0, n, size=n)
        boot_means.append(_inverse_target(float(np.mean(tree_preds[idx])), schema))

    lower = float(np.percentile(boot_means, 2.5))
    upper = float(np.percentile(boot_means, 97.5))
    return max(lower, 0.0), max(upper, 0.0)


def _round(value, ndigits=1):
    return round(float(value), ndigits) if value is not None else None


def simulate(
    country,
    scenario,
    custom_overrides,
    df,
    model,
    schema,
    include_ci: bool = True,
    include_story: bool = True,
):
    """Run a counterfactual simulation and return a full result dict."""
    row = get_country_row(df, country)

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
        for key in ("bcg_coverage", "hiv_prevalence", "gdp_per_capita", "health_expenditure", "income_level"):
            val = custom_overrides.get(key)
            if val is not None:
                modified[key] = val if key == "income_level" else float(val)

    features = build_feature_vector(modified, schema)
    frame = vector_to_frame(features, schema)

    predicted = _predict_point(model, frame, schema)
    ci_lower, ci_upper = _bootstrap_ci(model, frame, schema) if include_ci else (predicted, predicted)

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
        return _round(current, 2 if key in ("hiv_prevalence", "health_expenditure") else 1), \
            _round(sim, 2 if key in ("hiv_prevalence", "health_expenditure") else 1)

    cur_bcg, sim_bcg = cov("bcg_coverage", row.get("bcg_coverage"))
    cur_hiv, sim_hiv = cov("hiv_prevalence", row.get("hiv_prevalence"))
    cur_gdp, sim_gdp = cov("gdp_per_capita", row.get("gdp_per_capita"))
    cur_health, sim_health = cov("health_expenditure", row.get("health_expenditure"))
    cur_income, sim_income = cov("income_level", row.get("income_level"))

    story = generate_country_story(country, row) if include_story else ""
    explanation = (
        generate_scenario_explanation(country, scenario, current_tb, predicted, cases_prevented_per_year)
        if include_story else ""
    )

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
        "country_story": story,
        "scenario_explanation": explanation,
        "disclaimer": DISCLAIMER,
    }


def prioritize(df, model, schema, bcg_target: float = 90.0, top: int = 20):
    """Rank countries by estimated cases prevented under a BCG target."""
    latest = df.sort_values("year").groupby("country", as_index=False).last()
    rows = []
    for _, row in latest.iterrows():
        if "bcg_coverage" not in row or np.isnan(row["bcg_coverage"]):
            continue
        result = simulate(
            row["country"],
            "custom",
            {"bcg_coverage": min(float(bcg_target), 99.0)},
            df,
            model,
            schema,
            include_ci=False,
            include_story=False,
        )
        rows.append(
            {
                "country": row["country"],
                "iso3": row["iso3"],
                "region": row["region"],
                "income_level": row["income_level"] if schema["use_income"] else None,
                "population": float(row.get("population") or 0),
                "current_tb_incidence": result["current_tb_incidence"],
                "predicted_tb_incidence": result["predicted_tb_incidence"],
                "cases_prevented_per_year": max(float(result["cases_prevented_per_year"]), 0.0),
                "relative_reduction_pct": max(float(result["relative_reduction_pct"]), 0.0),
                "current_bcg_coverage": row.get("bcg_coverage"),
                "rapid_dx_sites": row.get("rapid_dx_sites"),
            }
        )

    rows = sorted(rows, key=lambda item: item["cases_prevented_per_year"], reverse=True)
    return rows[:max(1, int(top))]
