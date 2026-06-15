"""Plotly figures and value formatters for the TB Futures UI."""

import httpx
import plotly.graph_objects as go

ACCENT = "#F26B3A"
ACCENT_PALE = "#FBE2D6"
TEXT = "#1A1A1A"
MUTED = "#6B7280"
BORDER = "#F0EDE8"
SURFACE = "#FFFFFF"
DISPLAY_FONT = "Fraunces, serif"
BODY_FONT = "Inter, sans-serif"
REGION_COLORS = {
    "AFR": "#F26B3A",
    "AMR": "#C9773B",
    "EMR": "#9E744B",
    "EUR": "#7C7964",
    "SEA": "#5F7F77",
    "WPR": "#4F7E8D",
}

FEATURE_LABELS = {
    "bcg_coverage": "BCG Vaccination Coverage",
    "log_gdp": "Economic Resources (GDP)",
    "year": "Time Trend",
}


def _pct(value):
    return f"{value:.1f}%" if value is not None else "—"


def _val(value):
    return f"{value:.0f}" if value is not None else "—"


def _usd(value):
    return f"${value:,.0f}" if value is not None else "—"


def _clean_layout(fig, height=300, title=None):
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        height=height,
        margin=dict(l=14, r=14, t=56 if title else 14, b=18),
        title=(
            dict(
                text=title,
                x=0.02,
                xanchor="left",
                font=dict(color=TEXT, size=20, family=DISPLAY_FONT),
            )
            if title else None
        ),
        font=dict(color=MUTED, family=BODY_FONT, size=13),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0.02),
    )
    fig.update_xaxes(showgrid=False, zeroline=False, linecolor=BORDER, tickfont=dict(color=MUTED))
    fig.update_yaxes(showgrid=False, zeroline=False, linecolor=BORDER, tickfont=dict(color=MUTED))
    return fig


def ci_figure(result):
    lower, upper = result["ci_lower"], result["ci_upper"]
    pred = result["predicted_tb_incidence"]
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=[lower, upper],
            y=[0, 0],
            mode="lines",
            line=dict(color=ACCENT_PALE, width=18),
            showlegend=False,
            hovertemplate="%{x:.0f} / 100k<extra></extra>",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=[pred],
            y=[0],
            mode="markers",
            marker=dict(color=ACCENT, size=18, line=dict(color=SURFACE, width=2)),
            showlegend=False,
            hovertemplate="Prediction: %{x:.0f} / 100k<extra></extra>",
        )
    )
    _clean_layout(fig, height=150, title="Model Uncertainty")
    fig.update_yaxes(visible=False, range=[-0.5, 0.5])
    fig.update_xaxes(visible=True, title="Cases per 100,000")
    return fig


def before_after_figure(result):
    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            y=["Current"],
            x=[result["current_tb_incidence"]],
            orientation="h",
            marker=dict(color="#E9DED6", line=dict(color="#E9DED6", width=0)),
            hovertemplate="Current: %{x:.0f} / 100k<extra></extra>",
        )
    )
    fig.add_trace(
        go.Bar(
            y=["Simulated"],
            x=[result["predicted_tb_incidence"]],
            orientation="h",
            marker=dict(color=ACCENT, line=dict(color=ACCENT, width=0)),
            hovertemplate="Simulated: %{x:.0f} / 100k<extra></extra>",
        )
    )
    _clean_layout(fig, height=260, title="Current vs Simulated TB Burden")
    fig.update_xaxes(title="TB incidence per 100,000", visible=True)
    fig.update_layout(showlegend=False, bargap=0.45)
    return fig


def gauge_figure(result):
    val = max(result["relative_reduction_pct"], 0)
    fig = go.Figure(
        go.Indicator(
            mode="gauge+number",
            value=val,
            number={"suffix": "%", "font": {"family": DISPLAY_FONT, "size": 34, "color": TEXT}},
            gauge={
                "axis": {"range": [0, 50], "tickcolor": BORDER, "tickfont": {"color": MUTED, "family": BODY_FONT}},
                "bar": {"color": ACCENT, "thickness": 0.34},
                "bgcolor": "rgba(0,0,0,0)",
                "borderwidth": 0,
                "steps": [
                    {"range": [0, 10], "color": "#FBF1EB"},
                    {"range": [10, 25], "color": "#F9E1D5"},
                    {"range": [25, 50], "color": "#F7C7B2"},
                ],
            },
        )
    )
    _clean_layout(fig, height=280, title="Estimated Reduction")
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
            x=[v for _, v in items],
            y=[k for k, _ in items],
            orientation="h",
            marker=dict(color=ACCENT, line=dict(color=ACCENT, width=0)),
            hovertemplate="%{y}: %{x:.3f}<extra></extra>",
        )
    )
    _clean_layout(fig, height=340, title="Feature Importance")
    fig.update_xaxes(title="Relative importance", visible=True)
    return fig


def model_compare_figure(metrics: dict):
    names = ["Random Forest", "Linear Regression", "Gradient Boosting"]
    values = [metrics["rf"]["r2"], metrics["lr"]["r2"], metrics["gbm"]["r2"]]
    fig = go.Figure(
        go.Bar(
            x=names,
            y=values,
            marker_color=[ACCENT, "#D9C7BB", "#9E744B"],
            text=[f"{v:.3f}" for v in values],
            textposition="outside",
            hovertemplate="%{x}: R²=%{y:.3f}<extra></extra>",
        )
    )
    _clean_layout(fig, height=320, title="Model Comparison")
    fig.update_yaxes(title="R²", visible=True)
    return fig


def residual_diagnostic_figure(rows, key_name, title):
    labels = [row[key_name] for row in rows]
    mae = [row["mae"] for row in rows]
    bias = [row["bias"] for row in rows]
    fig = go.Figure()
    fig.add_trace(go.Bar(x=labels, y=mae, name="MAE", marker_color=ACCENT))
    fig.add_trace(go.Bar(x=labels, y=bias, name="Bias", marker_color="#D9C7BB"))
    _clean_layout(fig, height=340, title=title)
    fig.update_yaxes(title="Cases per 100,000", visible=True)
    return fig


def predicted_vs_actual_figure(rows):
    if not rows:
        return _clean_layout(go.Figure(), height=360, title="Predicted vs Actual")
    fig = go.Figure(
        go.Scatter(
            x=[row["actual"] for row in rows],
            y=[row["predicted"] for row in rows],
            mode="markers",
            marker=dict(
                size=9,
                color=[REGION_COLORS.get(row["region"], ACCENT) for row in rows],
                opacity=0.72,
                line=dict(color=SURFACE, width=0.8),
            ),
            customdata=[[row["country"], row["year"], row["region"]] for row in rows],
            hovertemplate="%{customdata[0]} (%{customdata[1]})<br>Region: %{customdata[2]}"
            "<br>Actual: %{x:.0f} / 100k<br>Predicted: %{y:.0f} / 100k<extra></extra>",
        )
    )
    max_val = max(max(row["actual"], row["predicted"]) for row in rows)
    fig.add_trace(
        go.Scatter(
            x=[0, max_val],
            y=[0, max_val],
            mode="lines",
            line=dict(color="#D9C7BB", dash="dash"),
            hoverinfo="skip",
            showlegend=False,
        )
    )
    _clean_layout(fig, height=360, title="Predicted vs Actual")
    fig.update_xaxes(title="Actual TB incidence per 100,000", visible=True)
    fig.update_yaxes(title="Predicted TB incidence per 100,000", visible=True)
    return fig


def prioritization_bar_figure(rows, bcg_target):
    top = list(reversed(rows[:12]))
    fig = go.Figure(
        go.Bar(
            x=[row["cases_prevented_per_year"] for row in top],
            y=[row["country"] for row in top],
            orientation="h",
            marker=dict(
                color=[row["current_bcg_coverage"] for row in top],
                colorscale=[[0, "#FBE7DE"], [1, ACCENT]],
                cmin=0,
                cmax=max(bcg_target, 100),
                line=dict(color="rgba(0,0,0,0)", width=0),
            ),
            hovertemplate=(
                "%{y}<br>Cases prevented/year: %{x:,.0f}"
                "<br>Current BCG: %{marker.color:.0f}%<extra></extra>"
            ),
            showlegend=False,
        )
    )
    _clean_layout(fig, height=420, title=f"Top Countries at {bcg_target:.0f}% BCG")
    fig.update_xaxes(title="Estimated cases prevented per year", visible=True)
    return fig


def prioritization_scatter_figure(rows):
    if not rows:
        return _clean_layout(go.Figure(), height=420, title="Prioritization Landscape")

    max_pop = max(row["population"] for row in rows) or 1
    sizes = [14 + 32 * (row["population"] / max_pop) for row in rows]
    fig = go.Figure()
    for region in sorted({row["region"] for row in rows}):
        subset = [row for row in rows if row["region"] == region]
        fig.add_trace(
            go.Scatter(
                x=[row["current_bcg_coverage"] for row in subset],
                y=[row["current_tb_incidence"] for row in subset],
                mode="markers+text",
                text=[row["country"] for row in subset[:4]] + [""] * max(len(subset) - 4, 0),
                textposition="top center",
                marker=dict(
                    size=[sizes[rows.index(row)] for row in subset],
                    color=REGION_COLORS.get(region, ACCENT),
                    opacity=0.82,
                    line=dict(color=SURFACE, width=1.3),
                ),
                name=region,
                customdata=[[row["country"], row["cases_prevented_per_year"]] for row in subset],
                hovertemplate="%{customdata[0]}<br>BCG: %{x:.0f}%<br>Current TB: %{y:.0f} / 100k"
                "<br>Cases prevented/year: %{customdata[1]:,.0f}<extra></extra>",
            )
        )
    _clean_layout(fig, height=420, title="Prioritization Landscape")
    fig.update_xaxes(title="Current BCG coverage (%)", visible=True)
    fig.update_yaxes(title="Current TB incidence per 100,000", visible=True)
    return fig


def _choropleth(locations, z, text, colorscale, title, cbar_title):
    fig = go.Figure(
        go.Choropleth(
            locations=locations,
            z=z,
            text=text,
            colorscale=colorscale,
            marker_line_color=SURFACE,
            marker_line_width=0.5,
            colorbar_title=cbar_title,
            hovertemplate="%{text}<extra></extra>",
        )
    )
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        geo=dict(
            bgcolor="rgba(0,0,0,0)",
            showframe=False,
            showcoastlines=False,
            projection_type="natural earth",
            lataxis_range=[-58, 85],
        ),
        height=620,
        autosize=True,
        margin=dict(l=0, r=0, t=56, b=0),
        title=dict(text=title, font=dict(color=TEXT, size=20, family=DISPLAY_FONT), x=0.01),
        font=dict(color=MUTED, family=BODY_FONT),
    )
    return fig


def world_map(view: str, api_base: str, bcg_target: float = 90.0):
    def fetch(path, params=None):
        r = httpx.get(f"{api_base}{path}", params=params, timeout=180)
        r.raise_for_status()
        return r.json()

    if view == "What-If: All at 90% BCG":
        data = fetch("/whatif-map", {"bcg": bcg_target})
        locations = [d["iso3"] for d in data]
        z = [d["predicted_tb_incidence"] for d in data]
        text = [
            f"{d['country']}<br>Predicted TB: {d['predicted_tb_incidence']:.0f} / 100k"
            f"<br>Current BCG: {d['current_bcg_coverage']:.0f}%<br>GDP: {_usd(d['gdp_per_capita'])}"
            for d in data
        ]
        scale = [[0, "#FFF7F3"], [0.5, "#F7BCA5"], [1, ACCENT]]
        return _choropleth(
            locations,
            z,
            text,
            scale,
            f"Predicted TB Burden if All Countries Reached {bcg_target:.0f}% BCG",
            "TB / 100k",
        )

    data = fetch("/map-data")
    locations = [d["iso3"] for d in data]
    if view == "TB Burden":
        z = [d["tb_incidence"] or 0 for d in data]
        text = [
            f"{d['country']}<br>TB: {(d['tb_incidence'] or 0):.0f} / 100k"
            f"<br>BCG: {(d['bcg_coverage'] or 0):.0f}%<br>GDP: {_usd(d['gdp_per_capita'])}"
            for d in data
        ]
        scale = [[0, "#FFF7F3"], [0.5, "#F7BCA5"], [1, ACCENT]]
        return _choropleth(locations, z, text, scale, "TB Incidence per 100,000", "TB / 100k")
    if view == "BCG Coverage":
        z = [d["bcg_coverage"] or 0 for d in data]
        text = [
            f"{d['country']}<br>BCG: {(d['bcg_coverage'] or 0):.0f}%"
            f"<br>TB: {(d['tb_incidence'] or 0):.0f} / 100k"
            for d in data
        ]
        scale = [[0, "#FFF7F3"], [0.5, "#F8CBB7"], [1, ACCENT]]
        return _choropleth(locations, z, text, scale, "BCG Vaccination Coverage (%)", "BCG %")
    if view == "GDP per Capita":
        z = [d["gdp_per_capita"] or 0 for d in data]
        text = [
            f"{d['country']}<br>GDP: {_usd(d['gdp_per_capita'])}"
            f"<br>TB: {(d['tb_incidence'] or 0):.0f} / 100k"
            for d in data
        ]
        scale = [[0, "#FFF7F3"], [0.5, "#E7D7CC"], [1, "#7C7964"]]
        return _choropleth(locations, z, text, scale, "GDP per Capita", "USD")

    z = [d["rapid_dx_sites"] or 0 for d in data]
    text = [
        f"{d['country']}<br>Rapid Dx sites: {(d['rapid_dx_sites'] or 0):.2f} / million"
        f"<br>TB: {(d['tb_incidence'] or 0):.0f} / 100k"
        for d in data
    ]
    scale = [[0, "#FFF7F3"], [0.5, "#D7E6E1"], [1, "#4F7E8D"]]
    return _choropleth(locations, z, text, scale, "Detection Capacity (Rapid Dx Sites per Million)", "Sites / million")
