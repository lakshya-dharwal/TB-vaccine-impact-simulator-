"""Plain-English narrative helpers for TB Futures."""

SCENARIO_LABELS = {
    "baseline": "no change",
    "vaccine_push": "a vaccination push",
    "hiv_control": "stronger HIV control",
    "health_boost": "more healthcare investment",
    "income_up": "broader economic development",
    "combined": "a combined prevention effort",
    "custom": "your custom adjustments",
}

INCOME_WORDS = {
    "L": "low-income",
    "LM": "lower-middle-income",
    "UM": "upper-middle-income",
    "H": "high-income",
}


def _num(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _burden_level(tb_incidence: float) -> str:
    if tb_incidence >= 150:
        return "high"
    if tb_incidence >= 40:
        return "moderate"
    return "low"


def generate_country_story(country: str, row) -> str:
    """Explain, in one short paragraph, why a country has its TB burden."""
    bcg = _num(row.get("bcg_coverage"))
    tb = _num(row.get("tb_incidence")) or 0.0
    gdp = _num(row.get("gdp_per_capita"))
    rapid_dx = _num(row.get("rapid_dx_sites"))
    income = row.get("income_level")
    region = row.get("region", "its region")

    high_tb = tb >= 150
    low_tb = tb < 40
    low_income = income in ("L", "LM") or (gdp is not None and gdp < 4000)

    if low_income and high_tb:
        descriptor = INCOME_WORDS.get(income, "lower-income")
        return (
            f"As a {descriptor} country, {country}'s high TB burden reflects the "
            f"compounding effects of limited economic resources, delayed diagnosis, and "
            f"ongoing transmission pressure."
        )
    if bcg is not None and gdp is not None and bcg >= 90 and gdp >= 12000 and low_tb:
        return (
            f"{country} demonstrates how strong vaccination infrastructure combined with "
            f"a stronger economy can suppress TB incidence even in {region}."
        )
    if bcg is not None and bcg < 60 and low_tb:
        return (
            f"{country} has low BCG coverage, but TB incidence remains low due to strong "
            f"health-system capacity, lower transmission risk, and robust detection and "
            f"treatment systems."
        )
    if rapid_dx is not None and rapid_dx < 3 and high_tb:
        return (
            f"{country} pairs high TB burden with limited rapid diagnostic capacity, which "
            f"can make early detection and treatment harder."
        )
    return (
        f"{country} has {_burden_level(tb)} TB incidence influenced by a combination of "
        f"vaccination coverage, economic conditions, income level, and broader regional context."
    )


def generate_scenario_explanation(
    country: str,
    scenario: str,
    current_incidence: float,
    predicted_incidence: float,
    cases_prevented: float,
) -> str:
    """One-sentence, plain-English summary of a simulation result."""
    label = SCENARIO_LABELS.get(scenario, "this scenario")

    if scenario == "baseline":
        return (
            f"With no changes, the model estimates {country}'s TB incidence stays near "
            f"{predicted_incidence:.0f} cases per 100,000 people."
        )

    change = current_incidence - predicted_incidence
    if change > 0.5:
        prevented = max(int(round(cases_prevented)), 0)
        return (
            f"Under {label}, the model estimates {country}'s TB incidence could fall from "
            f"about {current_incidence:.0f} to {predicted_incidence:.0f} cases per 100,000 "
            f"people — roughly {prevented:,} fewer cases each year."
        )
    if change < -0.5:
        return (
            f"Under {label}, the model does not estimate a reduction for {country}; "
            f"predicted incidence is about {predicted_incidence:.0f} cases per 100,000 people."
        )
    return (
        f"Under {label}, the model estimates little change for {country}, with incidence "
        f"staying near {predicted_incidence:.0f} cases per 100,000 people."
    )
