"""Plain-English narrative helpers for TB Futures.

No ML jargon, no bare numbers without units. These produce human-readable
explanations shown in the UI.
"""

SCENARIO_LABELS = {
    "baseline": "no change",
    "vaccine_push": "a vaccination push",
    "hiv_control": "stronger HIV control",
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


def _burden_level(tb_incidence: float) -> str:
    if tb_incidence >= 150:
        return "high"
    if tb_incidence >= 40:
        return "moderate"
    return "low"


def generate_country_story(country: str, row) -> str:
    """Explain, in one short paragraph, why a country has its TB burden."""
    bcg = float(row.get("bcg_coverage") or 0)
    tb = float(row.get("tb_incidence") or 0)
    hiv = float(row.get("hiv_prevalence") or 0)
    income = row.get("income_level")
    region = row.get("region", "its region")

    high_tb = tb >= 150
    low_tb = tb < 40
    low_income = income in ("L", "LM")

    if hiv > 5 and high_tb:
        return (
            f"Despite {bcg:.0f}% BCG coverage, {country} has a high TB burden largely "
            f"because an HIV prevalence of {hiv:.1f}% significantly increases the risk "
            f"that latent TB becomes active disease."
        )
    if low_income and high_tb:
        return (
            f"As a {INCOME_WORDS.get(income, 'lower-income')} country, {country}'s high "
            f"TB burden reflects the compounding effects of limited economic resources "
            f"and healthcare access, where delayed diagnosis and incomplete treatment "
            f"allow transmission to persist."
        )
    if bcg >= 90 and low_tb:
        return (
            f"{country} demonstrates how strong vaccination infrastructure combined with "
            f"a stronger economy and lower HIV burden can suppress TB incidence even in "
            f"{region}."
        )
    if bcg < 60 and low_tb:
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
