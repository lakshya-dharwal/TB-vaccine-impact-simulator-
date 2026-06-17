"""TB Futures — Streamlit frontend.

Talks to the FastAPI backend over HTTP (httpx). No model code runs here. All
visible text uses explicit inline colors on a forced white background (see also
.streamlit/config.toml) so the UI renders correctly regardless of the user's
system light/dark setting.
"""

import os

import httpx
import streamlit as st

from src.ui.charts import (
    _pct, _usd, _val,
    before_after_figure, ci_figure, gauge_figure,
    importance_figure, model_compare_figure, residual_figure,
    prioritization_bar, prioritization_scatter, world_map,
)

API_BASE = os.environ.get("TB_API_BASE", "http://localhost:8000")
# Render's fromService host has no scheme; default to https when one is missing.
if not API_BASE.startswith(("http://", "https://")):
    API_BASE = "https://" + API_BASE

st.set_page_config(page_title="TB Futures", page_icon="🫁", layout="wide")

# Palette
INK = "#1F2937"       # headings
BODY = "#374151"      # body text
MUTED = "#6B7280"     # secondary text
ORANGE = "#F97316"
GREEN = "#16A34A"

SCENARIO_LABELS = {
    "baseline": "Baseline",
    "vaccine_push": "Vaccine Push (+30% BCG)",
    "hiv_control": "HIV Control (-25% HIV)",
    "health_boost": "Health System Boost (+25% spending)",
    "econ_dev": "Economic Development (+25% GDP)",
    "combined": "Combined",
}

INCOME_LABELS = {
    "L": "Low income", "LM": "Lower-middle income",
    "UM": "Upper-middle income", "H": "High income",
}

# covariate -> (stat label, formatter, reality-check explanation)
COVARIATE_INFO = {
    "bcg_coverage": ("BCG Coverage", lambda v: _pct(v),
                     "Childhood protection, not full adult prevention"),
    "hiv_prevalence": ("HIV Burden", lambda v: _pct(v),
                       "HIV increases risk of latent TB becoming active"),
    "gdp_per_capita": ("GDP per capita", lambda v: _usd(v),
                       "Lower income = higher exposure, delayed care"),
    "health_expenditure": ("Healthcare Spend", lambda v: f"{_pct(v)} of GDP",
                           "Better systems detect and treat TB earlier"),
    "income_level": ("Income Level", lambda v: INCOME_LABELS.get(v, "—"),
                     "Lower income = higher exposure, delayed care"),
}

# Minimal CSS — only for things inline styles cannot reach (app background,
# Streamlit's own button/slider widgets). Everything else is styled inline.
CSS = """
<style>
.stApp, [data-testid="stAppViewContainer"], [data-testid="stHeader"],
.main, .block-container { background-color: #FFFFFF !important; }
section[data-testid="stSidebar"] { background-color: #F9FAFB !important; }
.stButton > button {
    background-color: #F97316 !important; color: #FFFFFF !important; border: none;
    border-radius: 8px; font-weight: 600; padding: 10px 22px;
}
.stButton > button:hover { background-color: #EA6C0A !important; color: #FFFFFF !important; }
.stButton > button p { color: #FFFFFF !important; }
[data-baseweb="slider"] div[role="slider"] { background: #F97316 !important; }
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)


# ---------------------------------------------------------------- inline helpers
def heading(text, size=22, weight=700, mt=14, mb=8):
    st.markdown(
        f'<div style="color:{INK};font-size:{size}px;font-weight:{weight};'
        f'margin:{mt}px 0 {mb}px 0;">{text}</div>', unsafe_allow_html=True)


def small(text, color=MUTED):
    st.markdown(
        f'<div style="color:{color};font-size:13px;margin:2px 0 10px 0;">{text}</div>',
        unsafe_allow_html=True)


def tile(label, value, value_color=INK, sub=None):
    sub_html = (f'<div style="color:#9CA3AF;font-size:12px;text-transform:uppercase;'
                f'letter-spacing:0.05em;">{sub}</div>') if sub else ""
    return (
        f'<div style="background:#FFFFFF;border:1px solid #E5E7EB;border-radius:10px;'
        f'padding:16px;text-align:center;">'
        f'<div style="color:#9CA3AF;font-size:12px;text-transform:uppercase;'
        f'letter-spacing:0.05em;">{label}</div>'
        f'<div style="color:{value_color};font-size:28px;font-weight:700;">{value}</div>'
        f'{sub_html}</div>')


# ---------------------------------------------------------------- API helpers
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


def trust_badges():
    badges = [
        ("#DCFCE7", "#166534", "🟢 Good for: Learning TB risk patterns and exploring what-if scenarios"),
        ("#FEF9C3", "#854D0E", "🟡 Use with caution: Comparing exact outcomes between countries"),
        ("#FEE2E2", "#991B1B", "🔴 Not for: Clinical decisions, policy implementation, or research claims"),
    ]
    for bg, fg, text in badges:
        st.markdown(
            f'<div style="background:{bg};color:{fg};padding:6px 12px;border-radius:8px;'
            f'font-size:13px;margin:4px 0;">{text}</div>', unsafe_allow_html=True)


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


# ---------------------------------------------------------------- Header
st.markdown(
    f'<div style="color:{INK};font-size:42px;font-weight:800;margin-bottom:2px;">'
    "TB Futures</div>", unsafe_allow_html=True)
st.markdown(
    f'<div style="color:{BODY};font-size:17px;margin-bottom:10px;">Explore how prevention, '
    "HIV burden, income, and healthcare access shape tuberculosis risk</div>",
    unsafe_allow_html=True)
st.markdown('<hr style="height:3px;background:#F97316;border:none;border-radius:2px;'
            'margin:6px 0 14px 0;">', unsafe_allow_html=True)
small("A what-if lab for global TB prevention — built on real WHO/UNICEF/World Bank data")

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
    st.error(f"Could not reach the TB Futures API at {API_BASE}. "
             f"Start it with `uvicorn src.api.main:app --port 8000`.\n\n{exc}")

COVARIATES = CONFIG.get("covariates", [])
SCENARIOS = CONFIG.get("scenarios", ["baseline"])

tab1, tab4, tab2, tab3 = st.tabs(
    ["🔬 Scenario Explorer", "🎯 Prioritization", "🌍 World Map", "📊 Model Info"])


# ============================================================ TAB 1
with tab1:
    if not st.session_state.selected_country:
        heading("What if TB prevention improved?", size=24)
        c1, c2, c3 = st.columns(3)
        for col, (n, body) in zip([c1, c2, c3], [
            ("1. Pick a country", "Choose from the WHO member states in the dataset."),
            ("2. Choose a scenario", "Vaccination, HIV control, income, or a mix."),
            ("3. Understand the result", "See estimated burden change with honest uncertainty."),
        ]):
            col.markdown(
                f'<div style="background:#FFFFFF;border:1px solid #E5E7EB;'
                f'border-left:4px solid {ORANGE};border-radius:12px;padding:18px;'
                f'box-shadow:0 1px 3px rgba(0,0,0,0.08);min-height:96px;">'
                f'<div style="color:{INK};font-weight:700;font-size:16px;">{n}</div>'
                f'<div style="color:{BODY};font-size:14px;margin-top:6px;">{body}</div></div>',
                unsafe_allow_html=True)

    left, right = st.columns([1, 1.2])

    # ---------------- Inputs
    with left:
        heading("Country", size=20)
        if API_OK and COUNTRIES:
            default_idx = (COUNTRIES.index(st.session_state.selected_country)
                           if st.session_state.selected_country in COUNTRIES else 0)
            chosen = st.selectbox("Select a country", COUNTRIES, index=default_idx)
            st.session_state.selected_country = chosen

            stats = api_get(f"/country/{chosen}")

            lines = [f'TB Incidence: <b style="color:{INK};">{_val(stats["tb_incidence"])} / 100k</b>']
            for cov in COVARIATES:
                label, fmt, _ = COVARIATE_INFO[cov]
                lines.append(f'{label}: <b style="color:{INK};">{fmt(stats.get(cov))}</b>')
            lines.append(f'Population: <b style="color:{INK};">{fmt_pop(stats["population"])}</b>')
            body_html = "<br>".join(
                f'<span style="color:{BODY};">{ln}</span>' for ln in lines)
            st.markdown(
                f'<div style="background:#FFFFFF;border:1px solid #E5E7EB;'
                f'border-left:4px solid {ORANGE};border-radius:12px;padding:18px;'
                f'box-shadow:0 1px 3px rgba(0,0,0,0.08);">'
                f'<div style="color:{INK};font-weight:700;font-size:16px;margin-bottom:10px;">'
                f'{chosen} at a glance</div>{body_html}</div>', unsafe_allow_html=True)
            st.markdown(
                f'<p style="color:{MUTED};font-style:italic;margin-top:10px;">'
                f'{stats.get("country_story", "")}</p>', unsafe_allow_html=True)

            heading("Choose a scenario", size=20)
            cols = st.columns(len(SCENARIOS))
            for i, key in enumerate(SCENARIOS):
                if cols[i].button(SCENARIO_LABELS.get(key, key), key=f"sc_{key}",
                                  use_container_width=True):
                    st.session_state.scenario = key
            if st.session_state.scenario not in SCENARIOS:
                st.session_state.scenario = "baseline"
            small(f'Selected scenario: <b style="color:{INK};">'
                  f'{SCENARIO_LABELS.get(st.session_state.scenario)}</b>', color=BODY)

            overrides = {}
            with st.expander("⚙️ Adjust individual factors"):
                small("These override the scenario values above")
                use_custom = st.checkbox("Use custom values", value=False)
                if "bcg_coverage" in COVARIATES:
                    overrides["bcg_override"] = st.slider(
                        "BCG Coverage (%)", 0.0, 100.0, float(stats.get("bcg_coverage") or 0))
                if "hiv_prevalence" in COVARIATES:
                    overrides["hiv_override"] = st.slider(
                        "HIV Prevalence (%)", 0.0, 30.0, float(stats.get("hiv_prevalence") or 0))
                if "gdp_per_capita" in COVARIATES:
                    overrides["gdp_override"] = st.slider(
                        "GDP per capita ($)", 0.0, 100000.0, float(stats.get("gdp_per_capita") or 0))
                if "health_expenditure" in COVARIATES:
                    overrides["health_override"] = st.slider(
                        "Health Expenditure (% GDP)", 0.0, 20.0,
                        float(stats.get("health_expenditure") or 0))
                # Income level is a model feature/context, not an intervention lever.

            if st.button("Explore Scenario →", key="run"):
                payload = {"country": chosen,
                           "scenario": "custom" if use_custom else st.session_state.scenario}
                if use_custom:
                    payload.update(overrides)
                st.session_state.result = api_post("/simulate", payload)

    # ---------------- Outputs
    with right:
        result = st.session_state.result
        if result:
            heading("Results", size=20)
            r1c1, r1c2 = st.columns(2)
            r1c1.markdown(tile("Current TB Incidence",
                               f'{result["current_tb_incidence"]:.0f}', INK, "/ 100k"),
                          unsafe_allow_html=True)
            r1c2.markdown(tile("Predicted TB Incidence",
                               f'{result["predicted_tb_incidence"]:.0f}', ORANGE, "/ 100k"),
                          unsafe_allow_html=True)
            st.write("")
            r2c1, r2c2 = st.columns(2)
            prevented = max(result["cases_prevented_per_year"], 0)
            r2c1.markdown(tile("Cases Prevented / Year", f"~{prevented:,.0f}", GREEN),
                          unsafe_allow_html=True)
            r2c2.markdown(tile("Relative Reduction",
                               f'{result["relative_reduction_pct"]:.1f}%', GREEN),
                          unsafe_allow_html=True)
            small("Estimated cases prevented per year based on country population")

            heading("95% Model Uncertainty Interval", size=16)
            st.plotly_chart(ci_figure(result), use_container_width=True)
            small(f'{result["ci_lower"]:.0f} — {result["ci_upper"]:.0f} cases per 100k. '
                  "Reflects ML model variance, not epidemiological certainty")

            st.plotly_chart(before_after_figure(result), use_container_width=True)
            st.plotly_chart(gauge_figure(result), use_container_width=True)

            factors = "".join(
                f'<div style="color:{BODY};margin:3px 0;"><b style="color:{INK};">'
                f"{COVARIATE_INFO[c][0]}</b> — {COVARIATE_INFO[c][2]}</div>"
                for c in COVARIATES)
            st.markdown(
                f'<div style="background:#FFF7ED;border-left:4px solid {ORANGE};'
                f'border-radius:8px;padding:16px;margin:8px 0 12px 0;">'
                f'<div style="color:{INK};font-weight:700;margin-bottom:8px;">⚠️ Reality Check</div>'
                f'<div style="color:{BODY};margin-bottom:8px;">This estimate does not mean '
                "prevention alone caused this change. TB is shaped by many interacting "
                f'factors:</div>{factors}'
                f'<div style="color:{BODY};margin:3px 0;"><b style="color:{INK};">Region</b> '
                "— Captures broader public health patterns</div></div>",
                unsafe_allow_html=True)

            st.markdown(f'<div style="color:{BODY};margin:6px 0;"><b style="color:{INK};">'
                        f'In plain terms:</b> {result["scenario_explanation"]}</div>',
                        unsafe_allow_html=True)
            small(result["disclaimer"])
            heading("How much should you trust this?", size=16)
            trust_badges()
        else:
            st.info("Select a country and scenario, then click **Explore Scenario →**.")


# ============================================================ PRIORITIZATION
with tab4:
    heading("Where would scaling up BCG avert the most TB?", size=22)
    small("Ranks countries by estimated TB cases prevented per year if BCG coverage "
          "were raised to a target — burden × population × the coverage gap. A guide "
          "to where vaccination investment could matter most, not a policy recommendation.")
    if API_OK and "bcg_coverage" in COVARIATES:
        target = st.slider("Target BCG coverage (%)", 50, 99, 90, step=1)
        with st.spinner("Ranking countries…"):
            pr = api_get("/prioritize", {"bcg_target": float(target), "top": 200})
        countries = pr["countries"]
        pcol1, pcol2 = st.columns([1, 1])
        with pcol1:
            st.plotly_chart(prioritization_bar(countries), use_container_width=True,
                            config={"displayModeBar": False})
        with pcol2:
            st.plotly_chart(prioritization_scatter(countries), use_container_width=True,
                            config={"displayModeBar": False})
        heading("Top countries by estimated cases prevented / year", size=16)
        table = {
            "Country": [c["country"] for c in countries[:15]],
            "TB /100k": [f"{c['current_tb_incidence']:.0f}" for c in countries[:15]],
            "BCG now→target": [f"{c['current_bcg_coverage']:.0f}→{c['target_bcg_coverage']:.0f}%"
                               for c in countries[:15]],
            "Reduction": [f"{c['relative_reduction_pct']:.0f}%" for c in countries[:15]],
            "Cases prevented/yr": [f"~{c['cases_prevented_per_year']:,.0f}" for c in countries[:15]],
        }
        st.table(table)
        small("Estimates assume the modelled BCG–TB association is causal, which it is "
              "only partly — treat as a prioritisation heuristic, not a forecast.")
    elif API_OK:
        st.info("Prioritization needs BCG coverage in the dataset.")


# ============================================================ TAB 2
with tab2:
    heading("Global TB Picture", size=22)
    if API_OK:
        views = ["TB Burden", "BCG Coverage", "GDP per capita", "Detection capacity"]
        if "bcg_coverage" in COVARIATES:
            views.append("What-If: All at 90% BCG")
        view = st.radio("Map view", views, horizontal=True)
        with st.spinner("Rendering map…"):
            st.plotly_chart(world_map(view, API_BASE), use_container_width=True,
                            config={"displayModeBar": False})
        small("Hover a country for details. Most recent year available per country.")


# ============================================================ TAB 3
with tab3:
    heading("About This Model", size=22)
    st.markdown(
        f'<div style="background:#FFFFFF;border:1px solid #E5E7EB;border-radius:12px;'
        f'padding:18px;box-shadow:0 1px 3px rgba(0,0,0,0.08);color:{BODY};">'
        'TB Futures tunes a <b style="color:#1F2937;">Random Forest Regression</b> model '
        "(with Linear Regression and Gradient Boosting baselines) on real WHO and World "
        "Bank data spanning 2000 to 2023.<br><br>"
        '<b style="color:#1F2937;">Training period:</b> 2000 – 2017<br>'
        '<b style="color:#1F2937;">Test period:</b> 2018 – 2023 (held out, never seen during training)<br>'
        '<b style="color:#1F2937;">Target:</b> WHO estimated TB incidence per 100k (log-modelled)'
        "</div>", unsafe_allow_html=True)

    if API_OK:
        try:
            info = api_get("/model-info")
            m = info["metrics"]
            heading("Model Performance (held-out test set)", size=20)

            def col(key):
                return [f"{m[key]['r2']:.3f}", f"{m[key].get('r2_log', float('nan')):.3f}",
                        f"{m[key]['mae']:.1f}", f"{m[key]['rmse']:.1f}"]
            st.table({
                "Metric": ["R²", "R² (log scale)", "MAE /100k", "RMSE /100k"],
                "Random Forest": col("rf"),
                "Gradient Boosting": col("gbm") if "gbm" in m else ["—"] * 4,
                "Linear Regression": col("lr"),
            })
            small(f"Year-grouped CV R² (log): {m.get('rf_cv_r2_log', float('nan')):.3f}. "
                  "Absolute R² is modest because predicting 2018–2023 incidence across 150+ "
                  "heterogeneous countries is hard; log-scale fit is stronger.")
            st.plotly_chart(model_compare_figure(m), use_container_width=True)
            if info.get("diagnostics", {}).get("y_true"):
                st.plotly_chart(residual_figure(info["diagnostics"]),
                                use_container_width=True)
            heading("What drives TB incidence predictions?", size=20)
            st.plotly_chart(importance_figure(info["feature_importance"]),
                            use_container_width=True)
        except Exception as exc:  # noqa: BLE001
            st.warning(f"Model info unavailable (train the model first): {exc}")

    heading("Data Sources", size=20)
    st.markdown(
        f'<div style="color:{BODY};">'
        "• WHO Global Tuberculosis Programme — notifications, population, income level<br>"
        "• WHO/UNICEF WUENIC Immunization Coverage Estimates (BCG)<br>"
        "• Our World in Data — BCG coverage, HIV, GDP, health expenditure (as available)<br>"
        "• World Bank income classification / UNAIDS</div>", unsafe_allow_html=True)

    st.markdown(
        f'<div style="background:#FFF7ED;border-left:4px solid {ORANGE};border-radius:8px;'
        f'padding:16px;margin-top:14px;color:{BODY};">'
        f'<div style="color:{INK};font-weight:700;margin-bottom:8px;">How much should you trust this?</div>'
        "🟢 <b>Good for:</b> Learning how TB risk factors interact and exploring prevention scenarios<br>"
        "🟡 <b>Use caution for:</b> Drawing specific conclusions about individual countries<br>"
        "🔴 <b>Not for:</b> Clinical decisions, policy proposals, or scientific research without expert review<br><br>"
        "This tool is built for education and portfolio demonstration. The Random Forest model "
        "captures real statistical patterns in the data but cannot account for reporting bias, "
        "transmission dynamics, time lags between vaccination and disease burden, or "
        "country-specific confounders not present in the dataset.</div>", unsafe_allow_html=True)
