"""TB Futures — Streamlit frontend."""

import html
import os
import sys
from pathlib import Path

import httpx
import pandas as pd
import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src.ui.charts import (
    _pct,
    _usd,
    _val,
    before_after_figure,
    ci_figure,
    gauge_figure,
    importance_figure,
    model_compare_figure,
    predicted_vs_actual_figure,
    prioritization_bar_figure,
    prioritization_scatter_figure,
    residual_diagnostic_figure,
    world_map,
)

API_BASE = os.environ.get("TB_API_BASE", "http://localhost:8000")

st.set_page_config(page_title="TB Futures", page_icon="🫁", layout="wide")

INK = "#1A1A1A"
BODY = "#4B5563"
MUTED = "#9CA3AF"
ACCENT = "#F26B3A"
ACCENT_SOFT = "#FEF6F2"
BORDER = "#F0EDE8"

SCENARIO_LABELS = {
    "baseline": "Baseline",
    "vaccine_push": "Vaccine Push",
    "hiv_control": "HIV Control",
    "health_boost": "Health System Boost",
    "income_up": "Income Level Up",
    "combined": "Combined",
}

INCOME_LABELS = {
    "L": "Low income",
    "LM": "Lower-middle income",
    "UM": "Upper-middle income",
    "H": "High income",
}

COVARIATE_INFO = {
    "bcg_coverage": ("BCG Coverage", lambda v: _pct(v), "Childhood protection, not full adult prevention"),
    "gdp_per_capita": ("GDP per capita", lambda v: _usd(v), "Lower income can mean higher exposure, crowding, and delayed care"),
    "income_level": ("Income Level", lambda v: INCOME_LABELS.get(v, "—"), "Income bands proxy broad structural conditions"),
}

PLOT_CONFIG = {"displayModeBar": False, "responsive": True}

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Fraunces:opsz,wght,SOFT@9..144,500,100&display=swap');

:root {
  --bg: #FDFCFA;
  --surface: #FFFFFF;
  --accent: #F26B3A;
  --accent-soft: #FEF6F2;
  --text: #1A1A1A;
  --body: #4B5563;
  --muted: #9CA3AF;
  --border: #F0EDE8;
  --shadow: 0 4px 24px rgba(0,0,0,0.04);
  --radius: 16px;
}

html, body, [class*="css"]  {
  font-family: 'Inter', sans-serif;
}

.stApp, [data-testid="stAppViewContainer"], .main, .block-container {
  background: var(--bg) !important;
  color: var(--text) !important;
}

.block-container {
  max-width: 1200px;
  padding-top: 2.2rem;
  padding-bottom: 4rem;
}

#MainMenu, footer, header, [data-testid="stToolbar"] {
  display: none !important;
}

p, li, label, [data-testid="stMarkdownContainer"], [data-testid="stText"] {
  color: var(--body);
  line-height: 1.6;
}

.hero {
  padding: 1.4rem 0 1.8rem 0;
  animation: fadeUp .45s ease;
}

.eyebrow {
  font-size: 12px;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: var(--muted);
  margin-bottom: 0.7rem;
  font-weight: 600;
}

.hero h1, .section-title, .metric-value, .display-stat {
  font-family: 'Fraunces', serif;
  color: var(--text);
}

.hero h1 {
  font-size: 56px;
  font-weight: 600;
  letter-spacing: -0.02em;
  line-height: 1.02;
  margin: 0;
}

.hero h1 span {
  color: var(--accent);
  font-style: italic;
}

.hero p {
  max-width: 760px;
  margin: 1rem 0 0 0;
  font-size: 15px;
  color: var(--body);
}

.hero-divider {
  height: 1px;
  background: rgba(242, 107, 58, 0.55);
  margin-top: 1.35rem;
}

.section-title {
  font-size: 28px;
  font-weight: 500;
  margin: 0;
}

.section-copy {
  margin-top: 0.45rem;
  font-size: 15px;
  color: var(--body);
}

.surface-card, div[data-testid="stPlotlyChart"], div[data-testid="stDataFrame"], div[data-testid="stTable"] {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  box-shadow: var(--shadow);
}

.surface-card {
  padding: 28px;
  animation: fadeUp .4s ease;
}

.surface-card.soft {
  background: var(--accent-soft);
}

.surface-card + .surface-card {
  margin-top: 0.85rem;
}

.step-card {
  min-height: 152px;
}

.card-title {
  color: var(--text);
  font-weight: 600;
  font-size: 18px;
  margin-bottom: 0.45rem;
}

.card-copy {
  font-size: 15px;
}

.metric-tile {
  background: var(--accent-soft);
  border: 1px solid rgba(242, 107, 58, 0.12);
  border-radius: var(--radius);
  padding: 24px 22px;
  min-height: 150px;
  animation: fadeUp .45s ease;
}

.metric-label {
  font-size: 12px;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: var(--muted);
  font-weight: 600;
  margin-bottom: 0.75rem;
}

.metric-value {
  font-size: 40px;
  line-height: 1.05;
  margin: 0;
}

.metric-sub {
  margin-top: 0.7rem;
  font-size: 14px;
  color: var(--body);
}

.quote {
  font-size: 16px;
  font-style: italic;
  color: var(--body);
}

.stat-line {
  padding: 0.45rem 0;
  border-bottom: 1px solid var(--border);
  font-size: 15px;
}

.stat-line:last-child {
  border-bottom: none;
}

.stat-line strong {
  color: var(--text);
}

.callout {
  background: var(--accent-soft);
  border: 1px solid rgba(242, 107, 58, 0.14);
  border-radius: var(--radius);
  padding: 24px 26px;
}

.callout-title {
  color: var(--text);
  font-weight: 600;
  margin-bottom: 0.6rem;
}

.badge {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 999px;
  padding: 0.42rem 0.8rem;
  display: inline-block;
  font-size: 12px;
  color: var(--body);
  margin-right: 0.45rem;
  margin-bottom: 0.45rem;
}

.trust-badge {
  border-radius: 14px;
  padding: 14px 16px;
  font-size: 14px;
  margin-bottom: 0.7rem;
}

.trust-badge strong {
  color: inherit;
}

.trust-good { background: #F2FBF5; color: #1E6A44; }
.trust-warn { background: #FFF9EA; color: #8A5C00; }
.trust-stop { background: #FFF1EF; color: #A03F35; }

div[data-testid="stTabs"] [data-baseweb="tab-list"] {
  gap: 0.5rem;
  background: var(--accent-soft);
  border: 1px solid var(--border);
  padding: 0.38rem;
  border-radius: 999px;
  margin: 0.6rem 0 1.7rem 0;
}

div[data-testid="stTabs"] [data-baseweb="tab"] {
  border-radius: 999px;
  color: var(--body);
  font-weight: 600;
  padding: 0.55rem 1rem;
  transition: all 0.2s ease;
}

div[data-testid="stTabs"] [aria-selected="true"] {
  background: var(--surface) !important;
  color: var(--text) !important;
  box-shadow: 0 4px 16px rgba(0,0,0,0.05);
}

.stButton > button {
  background: var(--accent) !important;
  color: #FFFFFF !important;
  border: none !important;
  border-radius: 12px !important;
  padding: 0.8rem 1.75rem !important;
  font-weight: 600 !important;
  box-shadow: 0 10px 24px rgba(242,107,58,0.18) !important;
  transition: all 0.2s ease !important;
}

.stButton > button:hover {
  transform: translateY(-1px);
  box-shadow: 0 14px 28px rgba(242,107,58,0.22) !important;
}

.stButton > button p {
  color: #FFFFFF !important;
}

[data-testid="stSelectbox"] > div > div,
[data-testid="stNumberInput"] > div > div,
[data-testid="stTextInput"] > div > div,
[data-testid="stDateInput"] > div > div,
div[data-baseweb="select"] > div,
[data-testid="stSlider"] > div,
[data-testid="stExpander"],
div[data-testid="stRadio"] {
  transition: all 0.2s ease;
}

div[data-baseweb="select"] > div,
[data-testid="stNumberInput"] input,
[data-testid="stTextInput"] input {
  border-radius: 14px !important;
}

[data-testid="stSelectbox"] label p,
[data-testid="stRadio"] label p,
[data-testid="stSlider"] label p,
[data-testid="stCheckbox"] label p,
[data-testid="stExpander"] summary p {
  font-size: 12px !important;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--muted) !important;
  font-weight: 600;
}

div[data-baseweb="select"] > div {
  background: var(--surface) !important;
  border: 1px solid var(--border) !important;
  min-height: 50px !important;
  box-shadow: none !important;
}

div[data-baseweb="select"] > div:hover {
  border-color: rgba(242, 107, 58, 0.35) !important;
}

[data-testid="stRadio"] [role="radiogroup"] {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
}

[data-testid="stRadio"] label {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 999px;
  padding: 0.55rem 0.9rem;
}

[data-testid="stRadio"] label:hover {
  border-color: rgba(242, 107, 58, 0.35);
}

[data-testid="stCheckbox"] label {
  color: var(--body) !important;
}

[data-testid="stExpander"] {
  border: 1px solid var(--border) !important;
  border-radius: var(--radius) !important;
  background: var(--surface) !important;
}

[data-baseweb="slider"] [role="slider"] {
  background: var(--accent) !important;
  box-shadow: 0 0 0 4px rgba(242,107,58,0.12) !important;
}

[data-baseweb="slider"] > div > div > div {
  background: rgba(242,107,58,0.18) !important;
}

div[data-testid="stPlotlyChart"] {
  padding: 0.9rem 0.9rem 0.4rem 0.9rem;
  animation: fadeUp .45s ease;
}

div[data-testid="stDataFrame"], div[data-testid="stTable"] {
  padding: 0.35rem;
}

.stAlert {
  border-radius: var(--radius);
  border: 1px solid var(--border);
}

@keyframes fadeUp {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)


def esc(text) -> str:
    return html.escape(str(text)) if text is not None else "—"


def section_heading(eyebrow: str, title: str, body: str | None = None):
    st.markdown(
        f"""
        <div class="eyebrow">{esc(eyebrow)}</div>
        <div class="section-title">{esc(title)}</div>
        {'<div class="section-copy">' + esc(body) + '</div>' if body else ''}
        """,
        unsafe_allow_html=True,
    )


def surface_card(title: str, body: str, eyebrow: str | None = None, soft: bool = False):
    eyebrow_html = f'<div class="eyebrow">{esc(eyebrow)}</div>' if eyebrow else ""
    klass = "surface-card soft" if soft else "surface-card"
    return (
        f'<div class="{klass}">{eyebrow_html}'
        f'<div class="card-title">{esc(title)}</div>'
        f'<div class="card-copy">{body}</div></div>'
    )


def metric_tile(label: str, value: str, sub: str):
    return (
        '<div class="metric-tile">'
        f'<div class="metric-label">{esc(label)}</div>'
        f'<div class="metric-value">{esc(value)}</div>'
        f'<div class="metric-sub">{esc(sub)}</div>'
        '</div>'
    )


def trust_badges():
    for klass, label, body in [
        ("trust-good", "Good for", "Learning broad TB risk patterns and testing scenarios."),
        ("trust-warn", "Use caution for", "Comparing exact outcomes between countries or over-reading rank order."),
        ("trust-stop", "Not for", "Clinical decisions, implementation plans, or research claims."),
    ]:
        st.markdown(
            f'<div class="trust-badge {klass}"><strong>{label}:</strong> {esc(body)}</div>',
            unsafe_allow_html=True,
        )


def fmt_pop(pop):
    if not pop:
        return "—"
    if pop >= 1e9:
        return f"{pop / 1e9:.2f}B"
    if pop >= 1e6:
        return f"{pop / 1e6:.1f}M"
    if pop >= 1e3:
        return f"{pop / 1e3:.0f}K"
    return f"{pop:.0f}"


def plot(fig):
    st.plotly_chart(fig, use_container_width=True, config=PLOT_CONFIG)


@st.cache_data(ttl=300)
def api_get(path: str, params: dict | None = None):
    r = httpx.get(f"{API_BASE}{path}", params=params, timeout=180)
    r.raise_for_status()
    return r.json()


def api_post(path: str, payload: dict):
    r = httpx.post(f"{API_BASE}{path}", json=payload, timeout=180)
    if r.status_code == 422:
        return None
    r.raise_for_status()
    return r.json()


if "selected_country" not in st.session_state:
    st.session_state.selected_country = None
if "scenario" not in st.session_state:
    st.session_state.scenario = "baseline"
if "result" not in st.session_state:
    st.session_state.result = None

try:
    COUNTRIES = api_get("/countries")
    CONFIG = api_get("/config")
    API_OK = True
except Exception as exc:  # noqa: BLE001
    COUNTRIES, CONFIG, API_OK = [], {}, False
    st.error(
        f"Could not reach the TB Futures API at {API_BASE}. "
        f"Start it with `uvicorn src.api.main:app --port 8000`.\n\n{exc}"
    )
    st.stop()

COVARIATES = CONFIG.get("covariates", [])
SCENARIOS = CONFIG.get("scenarios", ["baseline"])
TARGET_DISPLAY = CONFIG.get("target_display", "TB incidence per 100,000")
TARGET_SOURCE = CONFIG.get("target_source", "owid_who_estimated_incidence")
TARGET_IS_MODELED = TARGET_SOURCE == "owid_who_estimated_incidence"

st.markdown(
    f"""
    <section class="hero">
      <div class="eyebrow">Global Health Scenario Lab</div>
      <h1>Explore TB <span>futures</span></h1>
      <p>
        Probe how vaccination, income, and structural conditions shift
        tuberculosis risk across countries. The app centers on <strong>{esc(TARGET_DISPLAY)}</strong>
        and turns a trained model into an interpretable what-if interface.
      </p>
      <div style="margin-top:1rem;">
        <span class="badge">{esc(TARGET_DISPLAY)}</span>
        <span class="badge">Random Forest + held-out evaluation</span>
        <span class="badge">Country prioritization view</span>
      </div>
      <div class="hero-divider"></div>
    </section>
    """,
    unsafe_allow_html=True,
)

tab1, tab2, tab3, tab4 = st.tabs(
    ["Scenario Explorer", "Prioritization", "World Map", "Model Info"]
)


with tab1:
    section_heading(
        "Interactive simulation",
        "Scenario Explorer",
        "Start from the latest country profile, choose a scenario, and inspect the modelled shift.",
    )

    intro_cols = st.columns(3)
    for col, (title, body) in zip(
        intro_cols,
        [
            ("Pick a country", "Use the most recent WHO-backed country profile in the dataset."),
            ("Choose a lever", "Switch between baseline, BCG improvement, income shift, or a combined move."),
            ("Read the output", "See incidence change, uncertainty, and a plain-language interpretation."),
        ],
    ):
        with col:
            st.markdown(
                f'<div class="surface-card step-card"><div class="card-title">{esc(title)}</div>'
                f'<div class="card-copy">{esc(body)}</div></div>',
                unsafe_allow_html=True,
            )

    left, right = st.columns([0.95, 1.05], gap="large")

    with left:
        section_heading("Inputs", "Country context", "Pick the country and intervention frame.")
        default_idx = (
            COUNTRIES.index(st.session_state.selected_country)
            if st.session_state.selected_country in COUNTRIES else 0
        )
        chosen = st.selectbox("Select a country", COUNTRIES, index=default_idx)
        st.session_state.selected_country = chosen
        stats = api_get(f"/country/{chosen}")

        stat_lines = [
            f'<div class="stat-line">Target measure <strong>{esc(stats.get("tb_target_display", TARGET_DISPLAY))}</strong></div>',
            f'<div class="stat-line">Latest year <strong>{esc(stats.get("year"))}</strong></div>',
            f'<div class="stat-line">TB incidence <strong>{esc(_val(stats.get("tb_incidence")))} / 100k</strong></div>',
            f'<div class="stat-line">Population <strong>{esc(fmt_pop(stats.get("population")))}</strong></div>',
            f'<div class="stat-line">Region <strong>{esc(stats.get("region"))}</strong></div>',
        ]
        if stats.get("rapid_dx_sites") is not None:
            rapid_dx_text = f'{float(stats.get("rapid_dx_sites")):.2f} / million'
            stat_lines.append(
                f'<div class="stat-line">Rapid Dx sites <strong>{esc(rapid_dx_text)}</strong></div>'
            )
        for cov in COVARIATES:
            label, fmt, _ = COVARIATE_INFO[cov]
            stat_lines.append(
                f'<div class="stat-line">{esc(label)} <strong>{esc(fmt(stats.get(cov)))}</strong></div>'
            )

        st.markdown(
            surface_card(
                f"{chosen} at a glance",
                "".join(stat_lines),
                eyebrow="Latest profile",
            ),
            unsafe_allow_html=True,
        )
        st.markdown(
            f'<div class="surface-card"><div class="eyebrow">Country story</div>'
            f'<div class="quote">{esc(stats.get("country_story", ""))}</div></div>',
            unsafe_allow_html=True,
        )

        section_heading("Scenario", "Choose the intervention frame")
        scenario_idx = SCENARIOS.index(st.session_state.scenario) if st.session_state.scenario in SCENARIOS else 0
        st.session_state.scenario = st.radio(
            "Scenario",
            SCENARIOS,
            index=scenario_idx,
            horizontal=True,
            format_func=lambda key: SCENARIO_LABELS.get(key, key.replace("_", " ").title()),
        )

        overrides = {}
        use_custom = False
        with st.expander("Adjust individual factors"):
            st.markdown(
                '<div class="section-copy">These values override the selected scenario.</div>',
                unsafe_allow_html=True,
            )
            use_custom = st.checkbox("Use custom values", value=False)
            if "bcg_coverage" in COVARIATES:
                overrides["bcg_override"] = st.slider(
                    "BCG Coverage (%)",
                    0.0,
                    100.0,
                    float(stats.get("bcg_coverage") or 0),
                )
            if "hiv_prevalence" in COVARIATES:
                overrides["hiv_override"] = st.slider(
                    "HIV Prevalence (%)",
                    0.0,
                    30.0,
                    float(stats.get("hiv_prevalence") or 0),
                )
            if "gdp_per_capita" in COVARIATES:
                overrides["gdp_override"] = st.slider(
                    "GDP per capita ($)",
                    0.0,
                    100000.0,
                    float(stats.get("gdp_per_capita") or 0),
                )
            if "health_expenditure" in COVARIATES:
                overrides["health_override"] = st.slider(
                    "Health expenditure (% GDP)",
                    0.0,
                    20.0,
                    float(stats.get("health_expenditure") or 0),
                )
            if "income_level" in COVARIATES:
                opts = CONFIG.get("income_levels", ["L", "LM", "UM", "H"])
                cur = stats.get("income_level")
                idx = opts.index(cur) if cur in opts else 0
                overrides["income_override"] = st.selectbox(
                    "Income level",
                    opts,
                    index=idx,
                    format_func=lambda x: INCOME_LABELS.get(x, x),
                )

        if st.button("Explore Scenario", use_container_width=True):
            payload = {
                "country": chosen,
                "scenario": "custom" if use_custom else st.session_state.scenario,
            }
            if use_custom:
                payload.update(overrides)
            st.session_state.result = api_post("/simulate", payload)

    with right:
        result = st.session_state.result
        section_heading(
            "Outputs",
            "Scenario readout",
            "The model returns a simulated incidence, a relative change, and an uncertainty band.",
        )
        if result:
            row1 = st.columns(2)
            row2 = st.columns(2)
            row1[0].markdown(
                metric_tile("Current TB Incidence", f'{result["current_tb_incidence"]:.0f}', "Per 100,000"),
                unsafe_allow_html=True,
            )
            row1[1].markdown(
                metric_tile("Simulated TB Incidence", f'{result["predicted_tb_incidence"]:.0f}', "Per 100,000"),
                unsafe_allow_html=True,
            )
            row2[0].markdown(
                metric_tile("Cases Prevented / Year", f'~{max(result["cases_prevented_per_year"], 0):,.0f}', "Population-scaled estimate"),
                unsafe_allow_html=True,
            )
            row2[1].markdown(
                metric_tile("Relative Reduction", f'{result["relative_reduction_pct"]:.1f}%', "Compared with current burden"),
                unsafe_allow_html=True,
            )

            plot_cols = st.columns(2, gap="large")
            with plot_cols[0]:
                plot(ci_figure(result))
            with plot_cols[1]:
                plot(gauge_figure(result))

            plot(before_after_figure(result))

            factors = "".join(
                f'<div class="stat-line">{esc(COVARIATE_INFO[c][0])} <strong>{esc(COVARIATE_INFO[c][2])}</strong></div>'
                for c in COVARIATES
            )
            st.markdown(
                surface_card(
                    "Reality check",
                    "This is a counterfactual model estimate, not causal proof. It changes selected levers while holding all "
                    "other observed country context fixed."
                    + ('<div style="height:0.6rem"></div>' + factors if factors else ""),
                    eyebrow="Interpret carefully",
                    soft=True,
                ),
                unsafe_allow_html=True,
            )
            st.markdown(
                f'<div class="surface-card"><div class="eyebrow">Plain-language summary</div>'
                f'<div class="card-copy">{esc(result["scenario_explanation"])}</div>'
                f'<div class="section-copy" style="margin-top:0.85rem;">{esc(result["disclaimer"])}</div></div>',
                unsafe_allow_html=True,
            )
            trust_badges()
        else:
            st.markdown(
                surface_card(
                    "No scenario run yet",
                    "Choose a country, set the scenario, and run the simulation to populate the result panel.",
                    eyebrow="Ready when you are",
                ),
                unsafe_allow_html=True,
            )


with tab2:
    section_heading(
        "Ranking view",
        "Prioritization",
        "Rank countries by estimated cases prevented per year if BCG coverage reached a target level. Use it as directional screening, not a policy recommendation.",
    )

    p1, p2 = st.columns([1.4, 1], gap="large")
    with p1:
        bcg_target = st.slider("BCG target (%)", 70, 99, 90, step=1)
    with p2:
        top_n = st.slider("Top countries", 10, 40, 20, step=5)

    priority = api_get("/prioritize", {"bcg_target": bcg_target, "top": top_n})
    priority_rows = priority["rows"]
    total_cases_prevented = sum(row["cases_prevented_per_year"] for row in priority_rows)

    metric_cols = st.columns(3)
    metric_cols[0].markdown(
        metric_tile("Countries shown", f'{len(priority_rows)}', "Top ranked by estimated impact"),
        unsafe_allow_html=True,
    )
    metric_cols[1].markdown(
        metric_tile("BCG target", f"{bcg_target}%", "Applied as a country-by-country what-if"),
        unsafe_allow_html=True,
    )
    metric_cols[2].markdown(
        metric_tile("Cases prevented / year", f'~{total_cases_prevented:,.0f}', "Across displayed countries"),
        unsafe_allow_html=True,
    )

    chart_cols = st.columns(2, gap="large")
    with chart_cols[0]:
        plot(prioritization_bar_figure(priority_rows, bcg_target))
    with chart_cols[1]:
        plot(prioritization_scatter_figure(priority_rows))

    table_df = pd.DataFrame(priority_rows).rename(
        columns={
            "country": "Country",
            "region": "Region",
            "income_level": "Income",
            "current_bcg_coverage": "Current BCG %",
            "current_tb_incidence": "Current TB / 100k",
            "predicted_tb_incidence": "Simulated TB / 100k",
            "cases_prevented_per_year": "Cases Prevented / Year",
            "relative_reduction_pct": "Relative Reduction %",
            "population": "Population",
            "rapid_dx_sites": "Rapid Dx / million",
        }
    )
    if not table_df.empty:
        for col in [
            "Current BCG %",
            "Current TB / 100k",
            "Simulated TB / 100k",
            "Cases Prevented / Year",
            "Relative Reduction %",
            "Rapid Dx / million",
        ]:
            if col in table_df.columns:
                table_df[col] = table_df[col].map(lambda x: f"{float(x):,.1f}")
        if "Population" in table_df.columns:
            table_df["Population"] = table_df["Population"].map(fmt_pop)
        if "Income" in table_df.columns:
            table_df["Income"] = table_df["Income"].map(lambda x: INCOME_LABELS.get(x, x or "—"))

    st.dataframe(table_df, use_container_width=True, hide_index=True)


with tab3:
    section_heading(
        "Global context",
        "World Map",
        "Scan the latest cross-country picture and compare burden, prevention coverage, structural context, and detection capacity.",
    )
    views = ["TB Burden", "BCG Coverage", "GDP per Capita", "Detection Capacity"]
    if "bcg_coverage" in COVARIATES:
        views.append("What-If: All at 90% BCG")
    view = st.radio("Map view", views, horizontal=True)
    map_bcg_target = st.slider("What-if BCG target for map", 70, 99, 90, step=1)
    plot(world_map(view, API_BASE, bcg_target=map_bcg_target))
    st.markdown(
        '<div class="section-copy">Hover any country for the latest available profile.</div>',
        unsafe_allow_html=True,
    )


with tab4:
    section_heading(
        "Method",
        "Model Info",
        "The app exposes its target source, evaluation split, cross-validated random forest settings, and residual diagnostics.",
    )
    info = api_get("/model-info")
    summary_cols = st.columns(3)
    summary_cols[0].markdown(
        metric_tile("Target", "WHO modeled", info.get("target_display", TARGET_DISPLAY)),
        unsafe_allow_html=True,
    )
    summary_cols[1].markdown(
        metric_tile("Training Window", info["training_period"], "Temporal split"),
        unsafe_allow_html=True,
    )
    summary_cols[2].markdown(
        metric_tile("Countries", f'{info["n_countries"]}', "Distinct country profiles"),
        unsafe_allow_html=True,
    )

    m = info["metrics"]
    metrics_df = pd.DataFrame(
        {
            "Metric": ["R²", "MAE (cases/100k)", "RMSE (cases/100k)"],
            "Random Forest": [f"{m['rf']['r2']:.3f}", f"{m['rf']['mae']:.1f}", f"{m['rf']['rmse']:.1f}"],
            "Linear Regression": [f"{m['lr']['r2']:.3f}", f"{m['lr']['mae']:.1f}", f"{m['lr']['rmse']:.1f}"],
            "Gradient Boosting": [f"{m['gbm']['r2']:.3f}", f"{m['gbm']['mae']:.1f}", f"{m['gbm']['rmse']:.1f}"],
        }
    )
    st.dataframe(metrics_df, use_container_width=True, hide_index=True)

    compare_cols = st.columns(2, gap="large")
    with compare_cols[0]:
        plot(model_compare_figure(m))
    with compare_cols[1]:
        plot(importance_figure(info["feature_importance"]))

    st.markdown(
        surface_card(
            "Cross-validation",
            f"Best RF params: {info['metrics']['rf_best_params']}<br>"
            f"Best CV score ({esc(info['metrics']['rf_cv_scoring'])}): {info['metrics']['rf_cv_best_score']:.3f}",
            eyebrow="Tuning",
            soft=True,
        ),
        unsafe_allow_html=True,
    )

    diag_cols = st.columns(2, gap="large")
    with diag_cols[0]:
        plot(residual_diagnostic_figure(info["diagnostics"]["by_region"], "region", "Residual Diagnostic by Region"))
    with diag_cols[1]:
        plot(residual_diagnostic_figure(info["diagnostics"]["by_income"], "income_level", "Residual Diagnostic by Income"))

    plot(predicted_vs_actual_figure(info["diagnostics"]["scatter_sample"]))

    st.markdown(
        surface_card(
            "Model card",
            info["model_card"].replace("\n", "<br>"),
            eyebrow="Documentation",
        ),
        unsafe_allow_html=True,
    )

    st.markdown(
        surface_card(
            "Data sources",
            "The merged dataset uses OWID's WHO estimated TB incidence series, BCG coverage, GDP per capita, population, rapid-diagnostic-site density, and WHO income/region context.",
            eyebrow="Inputs",
        ),
        unsafe_allow_html=True,
    )
    trust_badges()
