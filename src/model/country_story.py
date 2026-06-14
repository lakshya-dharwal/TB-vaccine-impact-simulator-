"""Plain-English narrative helpers for TB Futures.

No ML jargon, no bare numbers without units. Robust to whichever covariates the
dataset happens to include (HIV, GDP, and income level are all optional).
"""

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
    hiv = _num(row.get("hiv_prevalence"))
    gdp = _num(row.get("gdp_per_capita"))
    income = row.get("income_level")
    region = row.get("region", "its region")

    high_tb = tb >= 150
    low_tb = tb < 40
    low_income = income in ("L", "LM") or (gdp is not None and gdp < 2000)

    if hiv is not None and hiv > 5 and high_tb:
        bcg_txt = f"{bcg:.0f}% BCG coverage" if bcg is not None else "its vaccination programme"
        return (
            f"Despite {bcg_txt}, {country} has a high TB burden largely because an HIV "
            f"prevalence of {hiv:.1f}% significantly increases the risk that latent TB "
            f"becomes active disease."
        )
    if low_income and high_tb:
        descriptor = INCOME_WORDS.get(income, "lower-income")
        return (
            f"As a {descriptor} country, {country}'s high TB burden reflects the "
            f"compounding effects of limited economic resources and healthcare access, "
            f"where delayed diagnosis and incomplete treatment allow transmission to "
            f"persist."
        )
    if bcg is not None and bcg >= 90 and low_tb:
        return (
            f"{country} demonstrates how strong vaccination infrastructure combined with "
            f"a stronger economy and lower HIV burden can suppress TB incidence even in "
            f"{region}."
        )
    if bcg is not None and bcg < 60 and low_tb:
        return (
            f"{country} has low BCG coverage, but TB incidence remains low due to strong "
            f"healthcare access, lower transmission risk, and robust detection and "
            f"treatment systems."
        )
    return (
        f"{country} has {_burden_level(tb)} TB incidence influenced by a combination of "
        f"vaccination coverage, income level, HIV burden, and healthcare system capacity."
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
