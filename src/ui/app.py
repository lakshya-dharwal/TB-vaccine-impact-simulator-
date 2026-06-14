"""TB Futures — Streamlit frontend.

Talks to the FastAPI backend over HTTP (httpx). No model code runs here.
"""

import os

import httpx
import streamlit as st

from src.ui.charts import (
    _pct, _val,
    before_after_figure, ci_figure, gauge_figure,
    importance_figure, model_compare_figure, world_map,
)

INCOME_LABELS = {
    "L": "Low income",
    "LM": "Lower-middle income",
    "UM": "Upper-middle income",
    "H": "High income",
}

API_BASE = os.environ.get("TB_API_BASE", "http://localhost:8000")

st.set_page_config(page_title="TB Futures", page_icon="🫁", layout="wide")

CSS = """
<style>
body, .stApp { background-color: #FFFFFF; }
h1 { color: #1F2937; font-weight: 700; }
h2, h3 { color: #1F2937; font-weight: 600; }
p, label { color: #6B7280; }
.card {
    background: #FFFFFF; border: 1px solid #E5E7EB; border-radius: 12px;
    padding: 20px; box-shadow: 0 1px 3px rgba(0,0,0,0.08); margin-bottom: 16px;
}
.card-accent { border-left: 4px solid #F97316; }
.card-warning {
    background: #FFF7ED; border-left: 4px solid #F97316;
    border-radius: 8px; padding: 16px; margin-bottom: 16px;
}
.metric-tile {
    background: #FFFFFF; border: 1px solid #E5E7EB; border-radius: 10px;
    padding: 16px; text-align: center;
}
.metric-value { font-size: 28px; font-weight: 700; color: #1F2937; }
.metric-value-orange { font-size: 28px; font-weight: 700; color: #F97316; }
.metric-value-green { font-size: 28px; font-weight: 700; color: #16A34A; }
.metric-label { font-size: 12px; color: #9CA3AF; text-transform: uppercase; letter-spacing: 0.05em; }
.badge-green { background: #DCFCE7; color: #166534; padding: 4px 10px; border-radius: 999px; font-size: 12px; }
.badge-yellow { background: #FEF9C3; color: #854D0E; padding: 4px 10px; border-radius: 999px; font-size: 12px; }
.badge-red { background: #FEE2E2; color: #991B1B; padding: 4px 10px; border-radius: 999px; font-size: 12px; }
.stButton > button {
    background-color: #F97316; color: white; border: none; border-radius: 8px;
    font-weight: 600; padding: 10px 24px;
}
.stButton > button:hover { background-color: #EA6C0A; color: white; }
.stSlider > div > div > div { background: #F97316 !important; }
.orange-divider { height: 3px; background: #F97316; border: none; border-radius: 2px; margin: 8px 0 20px 0; }
.country-story { color: #6B7280; font-style: italic; margin-top: 8px; }
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)


# ---------------------------------------------------------------- API helpers
@st.cache_data(ttl=300)
def api_get(path: str, params: dict | None = None):
    r = httpx.get(f"{API_BASE}{path}", params=params, timeout=120)
    r.raise_for_status()
    return r.json()


def api_post(path: str, payload: dict):
    r = httpx.post(f"{API_BASE}{path}", json=payload, timeout=120)
    if r.status_code == 422:
        return None
    r.raise_for_status()
    return r.json()


def trust_badges():
    st.markdown(
        '<span class="badge-green">🟢 Good for: Learning TB risk patterns and '
        "exploring what-if scenarios</span>",
        unsafe_allow_html=True,
    )
    st.markdown(
        '<span class="badge-yellow">🟡 Use with caution: Comparing exact outcomes '
        "between countries</span>",
        unsafe_allow_html=True,
    )
    st.markdown(
        '<span class="badge-red">🔴 Not for: Clinical decisions, policy '
        "implementation, or research claims</span>",
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


# ---------------------------------------------------------------- Header
st.markdown("# TB Futures")
st.markdown(
    "Explore how prevention, HIV burden, income, and healthcare access shape "
    "tuberculosis risk"
)
st.markdown('<hr class="orange-divider">', unsafe_allow_html=True)
st.caption(
    "A what-if lab for global TB prevention — built on real WHO/UNICEF/World Bank data"
)

# Session state
if "selected_country" not in st.session_state:
    st.session_state.selected_country = None
if "scenario" not in st.session_state:
    st.session_state.scenario = "baseline"
if "result" not in st.session_state:
    st.session_state.result = None

try:
    COUNTRIES = api_get("/countries")
    API_OK = True
except Exception as exc:  # noqa: BLE001
    COUNTRIES = []
    API_OK = False
    st.error(
        f"Could not reach the TB Futures API at {API_BASE}. "
        f"Start it with `uvicorn src.api.main:app --port 8000`.\n\n{exc}"
    )

tab1, tab2, tab3 = st.tabs(["🔬 Scenario Explorer", "🌍 World Map", "📊 Model Info"])

SCENARIOS = [
    ("baseline", "Baseline"),
    ("vaccine_push", "Vaccine Push (+30% BCG)"),
    ("hiv_control", "HIV Control (-25% HIV)"),
    ("income_up", "Income Level Up (one tier)"),
    ("combined", "Combined (all three)"),
]


# ============================================================ TAB 1
with tab1:
    if not st.session_state.selected_country:
        st.subheader("What if TB prevention improved?")
        c1, c2, c3 = st.columns(3)
        c1.markdown(
            '<div class="card card-accent"><b>1. Pick a country</b><br>'
            "<span style='color:#6B7280'>Choose from ~180 WHO member states.</span></div>",
            unsafe_allow_html=True,
        )
        c2.markdown(
            '<div class="card card-accent"><b>2. Choose a scenario</b><br>'
            "<span style='color:#6B7280'>Vaccination, HIV control, income level, "
            "or all three.</span></div>",
            unsafe_allow_html=True,
        )
        c3.markdown(
            '<div class="card card-accent"><b>3. Understand the result</b><br>'
            "<span style='color:#6B7280'>See estimated burden change with honest "
            "uncertainty.</span></div>",
            unsafe_allow_html=True,
        )

    left, right = st.columns([1, 1.2])

    # ---------------- Inputs
    with left:
        st.markdown("### Country")
        if API_OK and COUNTRIES:
            default_idx = (
                COUNTRIES.index(st.session_state.selected_country)
                if st.session_state.selected_country in COUNTRIES
                else 0
            )
            chosen = st.selectbox("Select a country", COUNTRIES, index=default_idx)
            st.session_state.selected_country = chosen

            stats = api_get(f"/country/{chosen}")
            st.markdown(
                f"""<div class="card card-accent">
                <b>{chosen} at a glance</b><br><br>
                BCG Coverage: &nbsp;<b>{_pct(stats['bcg_coverage'])}</b><br>
                TB Incidence: &nbsp;<b>{_val(stats['tb_incidence'])} / 100k</b><br>
                HIV Burden: &nbsp;<b>{_pct(stats['hiv_prevalence'])}</b><br>
                Income Level: &nbsp;<b>{INCOME_LABELS.get(stats.get('income_level'), '—')}</b><br>
                Population: &nbsp;<b>{fmt_pop(stats['population'])}</b>
                </div>""",
                unsafe_allow_html=True,
            )
            st.markdown(
                f'<p class="country-story">{stats.get("country_story", "")}</p>',
                unsafe_allow_html=True,
            )

            st.markdown("### Choose a scenario")
            cols = st.columns(len(SCENARIOS))
            for i, (key, label) in enumerate(SCENARIOS):
                if cols[i].button(label, key=f"sc_{key}", use_container_width=True):
                    st.session_state.scenario = key
            st.caption(f"Selected scenario: **{dict(SCENARIOS)[st.session_state.scenario]}**")

            with st.expander("⚙️ Adjust individual factors"):
                st.caption("These override the scenario values above")
                use_custom = st.checkbox("Use custom values", value=False)
                bcg_v = st.slider("BCG Coverage (%)", 0.0, 100.0,
                                  float(stats["bcg_coverage"] or 0))
                hiv_v = st.slider("HIV Prevalence (%)", 0.0, 30.0,
                                  float(stats["hiv_prevalence"] or 0))
                income_options = ["L", "LM", "UM", "H"]
                cur_income = stats.get("income_level")
                income_idx = (
                    income_options.index(cur_income)
                    if cur_income in income_options else 0
                )
                income_v = st.selectbox(
                    "Income Level", income_options, index=income_idx,
                    format_func=lambda x: INCOME_LABELS.get(x, x),
                )

            if st.button("Explore Scenario →", key="run"):
                payload = {
                    "country": chosen,
                    "scenario": "custom" if use_custom else st.session_state.scenario,
                }
                if use_custom:
                    payload.update(
                        bcg_override=bcg_v, hiv_override=hiv_v,
                        income_override=income_v,
                    )
                st.session_state.result = api_post("/simulate", payload)

    # ---------------- Outputs
    with right:
        result = st.session_state.result
        if result:
            st.markdown("### Results")
            r1c1, r1c2 = st.columns(2)
            r1c1.markdown(
                f'<div class="metric-tile"><div class="metric-label">Current TB Incidence</div>'
                f'<div class="metric-value">{result["current_tb_incidence"]:.0f}</div>'
                f'<div class="metric-label">/ 100k</div></div>',
                unsafe_allow_html=True,
            )
            r1c2.markdown(
                f'<div class="metric-tile"><div class="metric-label">Predicted TB Incidence</div>'
                f'<div class="metric-value-orange">{result["predicted_tb_incidence"]:.0f}</div>'
                f'<div class="metric-label">/ 100k</div></div>',
                unsafe_allow_html=True,
            )
            st.write("")
            r2c1, r2c2 = st.columns(2)
            prevented = max(result["cases_prevented_per_year"], 0)
            r2c1.markdown(
                f'<div class="metric-tile"><div class="metric-label">Cases Prevented / Year</div>'
                f'<div class="metric-value-green">~{prevented:,.0f}</div></div>',
                unsafe_allow_html=True,
            )
            r2c2.markdown(
                f'<div class="metric-tile"><div class="metric-label">Relative Reduction</div>'
                f'<div class="metric-value-green">{result["relative_reduction_pct"]:.1f}%</div></div>',
                unsafe_allow_html=True,
            )
            st.caption("Estimated cases prevented per year based on country population")

            # CI bar
            st.markdown("#### 95% Model Uncertainty Interval")
            st.plotly_chart(ci_figure(result), use_container_width=True)
            st.caption(
                f'{result["ci_lower"]:.0f} — {result["ci_upper"]:.0f} cases per 100k. '
                "Reflects ML model variance, not epidemiological certainty"
            )

            # Before/after
            st.plotly_chart(before_after_figure(result), use_container_width=True)

            # Gauge
            st.plotly_chart(gauge_figure(result), use_container_width=True)

            # Reality check
            st.markdown(
                """<div class="card-warning">
                <b>⚠️ Reality Check</b><br>
                This estimate does not mean prevention alone caused this change.
                TB is shaped by many interacting factors:<br><br>
                <b>HIV prevalence</b> — HIV increases risk of latent TB becoming active<br>
                <b>Income level</b> — Lower income = higher exposure, delayed care<br>
                <b>BCG coverage</b> — Childhood protection, not full adult prevention<br>
                <b>Region</b> — Captures broader public health patterns
                </div>""",
                unsafe_allow_html=True,
            )

            st.markdown(f"**In plain terms:** {result['scenario_explanation']}")
            st.caption(result["disclaimer"])

            st.markdown("#### How much should you trust this?")
            trust_badges()
        else:
            st.info("Select a country and scenario, then click **Explore Scenario →**.")


# ============================================================ TAB 2
with tab2:
    st.subheader("Global TB Picture")
    if API_OK:
        view = st.radio(
            "Map view",
            ["TB Burden", "BCG Coverage", "HIV Burden", "What-If: All at 90% BCG"],
            horizontal=True,
        )
        with st.spinner("Rendering map…"):
            st.plotly_chart(world_map(view, API_BASE), use_container_width=True)
        st.caption(
            "Hover a country for details. Most recent year available per country."
        )


# ============================================================ TAB 3
with tab3:
    st.subheader("About This Model")
    st.markdown(
        """<div class="card">
        TB Futures uses a <b>Random Forest Regression</b> model trained on real WHO,
        UNICEF, and World Bank data from ~180 countries spanning 2000 to 2022.<br><br>
        <b>Training period:</b> 2000 – 2017<br>
        <b>Test period:</b> 2018 – 2022 (held out, never seen during training)<br>
        <b>Countries:</b> ~180 WHO member states
        </div>""",
        unsafe_allow_html=True,
    )

    if API_OK:
        try:
            info = api_get("/model-info")
            m = info["metrics"]
            st.markdown("### Model Performance")
            st.table(
                {
                    "Metric": ["R²", "MAE (cases/100k)", "RMSE (cases/100k)"],
                    "Random Forest": [
                        f"{m['rf']['r2']:.3f}", f"{m['rf']['mae']:.1f}",
                        f"{m['rf']['rmse']:.1f}",
                    ],
                    "Linear Regression": [
                        f"{m['lr']['r2']:.3f}", f"{m['lr']['mae']:.1f}",
                        f"{m['lr']['rmse']:.1f}",
                    ],
                }
            )
            st.plotly_chart(model_compare_figure(m), use_container_width=True)

            st.markdown("### What drives TB incidence predictions?")
            st.plotly_chart(
                importance_figure(info["feature_importance"]), use_container_width=True
            )
        except Exception as exc:  # noqa: BLE001
            st.warning(f"Model info unavailable (train the model first): {exc}")

    st.markdown("### Data Sources")
    st.markdown(
        "- WHO Global Tuberculosis Programme — notifications, population, income level\n"
        "- WHO/UNICEF WUENIC Immunization Coverage Estimates (BCG)\n"
        "- Our World in Data — BCG coverage and HIV prevalence\n"
        "- World Bank income classification / UNAIDS"
    )

    st.markdown(
        """<div class="card-warning">
        <b>How much should you trust this?</b><br>
        🟢 <b>Good for:</b> Learning how TB risk factors interact and exploring prevention scenarios<br>
        🟡 <b>Use caution for:</b> Drawing specific conclusions about individual countries<br>
        🔴 <b>Not for:</b> Clinical decisions, policy proposals, or scientific research without expert review<br><br>
        This tool is built for education and portfolio demonstration. The Random Forest model
        captures real statistical patterns in the data but cannot account for reporting bias,
        transmission dynamics, time lags between vaccination and disease burden, or
        country-specific confounders not present in the dataset.
        </div>""",
        unsafe_allow_html=True,
    )
