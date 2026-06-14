"""Plotly figures and value formatters for the TB Futures UI.

All charts use a white background and the orange (#F97316) primary accent.
"""

import httpx
import plotly.graph_objects as go

ORANGE = "#F97316"
GRAY = "#E5E7EB"
GREEN = "#16A34A"
DARK = "#1F2937"

FEATURE_LABELS = {
    "bcg_coverage": "BCG Vaccination Coverage",
    "hiv_prevalence": "HIV Burden",
    "year": "Time Trend",
}


# ---------------------------------------------------------------- formatters
def _pct(value):
    return f"{value:.1f}%" if value is not None else "—"


def _val(value):
    return f"{value:.0f}" if value is not None else "—"


def _usd(value):
    return f"${value:,.0f}" if value is not None else "—"


def _clean_layout(fig, height=300, title=None):
    fig.update_layout(
        paper_bgcolor="#FFFFFF",
        plot_bgcolor="#FFFFFF",
        height=height,
        margin=dict(l=10, r=10, t=40 if title else 10, b=10),
        title=dict(text=title, font=dict(color=DARK)) if title else None,
        font=dict(color=DARK),
    )
    fig.update_xaxes(showgrid=False, zeroline=False)
    fig.update_yaxes(showgrid=False, zeroline=False)
    return fig


# ---------------------------------------------------------------- figures
def ci_figure(result):
    lower, upper = result["ci_lower"], result["ci_upper"]
    pred = result["predicted_tb_incidence"]
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=[lower, upper], y=[0, 0], mode="lines",
            line=dict(color=GRAY, width=14), showlegend=False,
            hovertemplate="%{x:.0f} / 100k<extra></extra>",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=[pred], y=[0], mode="markers",
            marker=dict(color=ORANGE, size=18), showlegend=False,
            hovertemplate="Prediction: %{x:.0f} / 100k<extra></extra>",
        )
    )
    _clean_layout(fig, height=140)
    fig.update_yaxes(visible=False, range=[-0.5, 0.5])
    fig.update_xaxes(visible=True, title="Cases per 100,000")
    return fig


def before_after_figure(result):
    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            y=["Current"], x=[result["current_tb_incidence"]], orientation="h",
            marker_color=GRAY, name="Current",
            hovertemplate="Current: %{x:.0f} / 100k<extra></extra>",
        )
    )
    fig.add_trace(
        go.Bar(
            y=["Predicted"], x=[result["predicted_tb_incidence"]], orientation="h",
            marker_color=ORANGE, name="Predicted",
            hovertemplate="Predicted: %{x:.0f} / 100k<extra></extra>",
        )
    )
    _clean_layout(fig, height=240, title="TB Burden: Current vs Simulated")
    fig.update_xaxes(title="TB Incidence per 100,000", visible=True)
    fig.update_layout(showlegend=False)
    return fig


def gauge_figure(result):
    val = max(result["relative_reduction_pct"], 0)
    fig = go.Figure(
        go.Indicator(
            mode="gauge+number",
            value=val,
            number={"suffix": "%"},
            gauge={
                "axis": {"range": [0, 50]},
                "bar": {"color": ORANGE},
                "steps": [
                    {"range": [0, 10], "color": "#F3F4F6"},
                    {"range": [10, 25], "color": "#FED7AA"},
                    {"range": [25, 50], "color": "#FDBA74"},
                ],
            },
        )
    )
    _clean_layout(fig, height=280, title="Estimated Burden Reduction")
    return fig


def importance_figure(importance: dict):
    grouped = {}
    for key, val in importance.items():
        if key.startswith("region_"):
            grouped["Geographic Region"] = grouped.get("Geographic Region", 0) + val
        elif key.startswith("income_"):
            grouped["Income Level"] = grouped.get("Income Level", 0) + val
        else:
            grouped[FEATURE_LABELS.get(key, key)] = val
    items = sorted(grouped.items(), key=lambda x: x[1])
    fig = go.Figure(
        go.Bar(
            x=[v for _, v in items], y=[k for k, _ in items], orientation="h",
            marker_color=ORANGE,
            hovertemplate="%{y}: %{x:.3f}<extra></extra>",
        )
    )
    _clean_layout(fig, height=320, title="Feature Importance")
    fig.update_xaxes(title="Relative importance", visible=True)
    return fig


def model_compare_figure(metrics: dict):
    fig = go.Figure(
        go.Bar(
            x=["Random Forest", "Linear Regression"],
            y=[metrics["rf"]["r2"], metrics["lr"]["r2"]],
            marker_color=[ORANGE, GRAY],
            text=[f"{metrics['rf']['r2']:.3f}", f"{metrics['lr']['r2']:.3f}"],
            textposition="outside",
            hovertemplate="%{x}: R²=%{y:.3f}<extra></extra>",
        )
    )
    _clean_layout(fig, height=300, title="Model Comparison (R²)")
    fig.update_yaxes(title="R²", visible=True)
    return fig


# ---------------------------------------------------------------- world map
def _choropleth(locations, z, text, colorscale, reversescale, title, cbar_title):
    fig = go.Figure(
        go.Choropleth(
            locations=locations,
            z=z,
            text=text,
            colorscale=colorscale,
            reversescale=reversescale,
            marker_line_color="white",
            marker_line_width=0.4,
            colorbar_title=cbar_title,
            hovertemplate="%{text}<extra></extra>",
        )
    )
    fig.update_layout(
        paper_bgcolor="#FFFFFF",
        geo=dict(bgcolor="#FFFFFF", showframe=False, showcoastlines=False,
                 projection_type="natural earth"),
        height=520,
        margin=dict(l=0, r=0, t=40, b=0),
        title=dict(text=title, font=dict(color=DARK)),
    )
    return fig


def world_map(view: str, api_base: str):
    def fetch(path, params=None):
        r = httpx.get(f"{api_base}{path}", params=params, timeout=180)
        r.raise_for_status()
        return r.json()

    if view == "What-If: All at 90% BCG":
        data = fetch("/whatif-map", {"bcg": 90})
        locations = [d["iso3"] for d in data]
        z = [d["predicted_tb_incidence"] for d in data]
        text = [
            f"{d['country']}<br>Predicted TB: {d['predicted_tb_incidence']:.0f} / 100k"
            f"<br>BCG: {d['bcg_coverage']:.0f}%<br>HIV: {d['hiv_prevalence']:.1f}%"
            for d in data
        ]
        scale = [[0, "#FFFFFF"], [0.5, "#FECACA"], [1, "#DC2626"]]
        return _choropleth(locations, z, text, scale, False,
                           "Predicted TB Burden if All Countries Reached 90% BCG",
                           "TB / 100k")

    data = fetch("/map-data")
    locations = [d["iso3"] for d in data]
    text = [
        f"{d['country']}<br>TB: {(d['tb_incidence'] or 0):.0f} / 100k"
        f"<br>BCG: {(d['bcg_coverage'] or 0):.0f}%<br>HIV: {(d['hiv_prevalence'] or 0):.1f}%"
        for d in data
    ]

    if view == "TB Burden":
        z = [d["tb_incidence"] or 0 for d in data]
        scale = [[0, "#FFFFFF"], [0.5, "#FECACA"], [1, "#DC2626"]]
        return _choropleth(locations, z, text, scale, False,
                           "TB Incidence per 100,000", "TB / 100k")
    if view == "BCG Coverage":
        z = [d["bcg_coverage"] or 0 for d in data]
        scale = [[0, "#FFFFFF"], [0.5, "#FED7AA"], [1, "#F97316"]]
        return _choropleth(locations, z, text, scale, False,
                           "BCG Vaccination Coverage (%)", "BCG %")
    # HIV Burden
    z = [d["hiv_prevalence"] or 0 for d in data]
    scale = [[0, "#FFFFFF"], [0.5, "#FECACA"], [1, "#DC2626"]]
    return _choropleth(locations, z, text, scale, False,
                       "HIV Prevalence (%)", "HIV %")
