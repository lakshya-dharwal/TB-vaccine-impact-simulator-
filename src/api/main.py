"""TB Futures FastAPI backend.

Serves country statistics, the choropleth map data, model metadata, and runs
counterfactual simulations against the trained Random Forest.
"""

import json
import os

import joblib
import pandas as pd
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from src.model.country_story import generate_country_story
from src.model.predict import simulate

DATA_PATH = "data/processed/merged_tb_dataset.csv"
MODELS_DIR = "models"

app = FastAPI(title="TB Futures API", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class State:
    df: pd.DataFrame = None
    model = None
    feature_columns = None
    metrics = None
    feature_importance = None


state = State()


def _load():
    if state.df is None:
        state.df = pd.read_csv(DATA_PATH)
    if state.model is None:
        state.model = joblib.load(os.path.join(MODELS_DIR, "rf_model.pkl"))
    if state.feature_columns is None:
        with open(os.path.join(MODELS_DIR, "feature_columns.json")) as f:
            state.feature_columns = json.load(f)
    if state.metrics is None:
        with open(os.path.join(MODELS_DIR, "model_metrics.json")) as f:
            state.metrics = json.load(f)
    if state.feature_importance is None:
        with open(os.path.join(MODELS_DIR, "feature_importance.json")) as f:
            state.feature_importance = json.load(f)


@app.on_event("startup")
def startup():
    try:
        _load()
    except FileNotFoundError:
        # Allow the app to boot even if artifacts aren't built yet; endpoints
        # that need them will raise a clear error.
        pass


def _latest_row(country: str):
    sub = state.df[state.df["country"] == country]
    if sub.empty:
        raise HTTPException(status_code=422, detail=f"Unknown country: {country}")
    return sub.sort_values("year").iloc[-1]


class SimulationRequest(BaseModel):
    country: str
    scenario: str  # baseline, vaccine_push, hiv_control, health_boost, combined, custom
    bcg_override: float | None = None
    hiv_override: float | None = None
    health_override: float | None = None
    gdp_override: float | None = None


class SimulationResponse(BaseModel):
    country: str
    scenario: str
    current_bcg_coverage: float
    simulated_bcg_coverage: float
    current_hiv_prevalence: float
    simulated_hiv_prevalence: float
    current_health_expenditure: float
    simulated_health_expenditure: float
    current_tb_incidence: float
    predicted_tb_incidence: float
    absolute_reduction: float
    relative_reduction_pct: float
    ci_lower: float
    ci_upper: float
    population: float
    cases_prevented_per_year: float
    country_story: str
    scenario_explanation: str
    disclaimer: str


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/countries")
def countries():
    _load()
    return sorted(state.df["country"].unique().tolist())


@app.get("/country/{country_name}")
def country(country_name: str):
    _load()
    row = _latest_row(country_name)
    return {
        "country": country_name,
        "year": int(row["year"]),
        "bcg_coverage": _num(row.get("bcg_coverage")),
        "tb_incidence": _num(row.get("tb_incidence")),
        "hiv_prevalence": _num(row.get("hiv_prevalence")),
        "gdp_per_capita": _num(row.get("gdp_per_capita")),
        "health_expenditure": _num(row.get("health_expenditure")),
        "population": _num(row.get("population")),
        "region": row.get("region"),
        "country_story": generate_country_story(country_name, row.to_dict()),
    }


@app.post("/simulate", response_model=SimulationResponse)
def run_simulation(req: SimulationRequest):
    _load()
    # Validate country up front so unknown countries return 422.
    _latest_row(req.country)

    valid = {"baseline", "vaccine_push", "hiv_control", "health_boost", "combined", "custom"}
    if req.scenario not in valid:
        raise HTTPException(status_code=422, detail=f"Unknown scenario: {req.scenario}")

    overrides = {
        "bcg_coverage": req.bcg_override,
        "hiv_prevalence": req.hiv_override,
        "health_expenditure": req.health_override,
        "gdp_per_capita": req.gdp_override,
    }
    overrides = {k: v for k, v in overrides.items() if v is not None}

    result = simulate(
        req.country, req.scenario, overrides, state.df, state.model, state.feature_columns
    )
    return result


@app.get("/map-data")
def map_data():
    _load()
    latest = (
        state.df.sort_values("year")
        .groupby("country", as_index=False)
        .last()
    )
    out = []
    for _, row in latest.iterrows():
        out.append(
            {
                "country": row["country"],
                "iso3": row["iso3"],
                "tb_incidence": _num(row.get("tb_incidence")),
                "bcg_coverage": _num(row.get("bcg_coverage")),
                "hiv_prevalence": _num(row.get("hiv_prevalence")),
            }
        )
    return out


@app.get("/whatif-map")
def whatif_map(bcg: float = 90.0):
    """Predicted TB burden for every country if BCG coverage were set to `bcg`%."""
    _load()
    countries_list = state.df["country"].unique().tolist()
    out = []
    for name in countries_list:
        try:
            res = simulate(
                name, "custom", {"bcg_coverage": bcg}, state.df, state.model,
                state.feature_columns,
            )
        except KeyError:
            continue
        iso3 = state.df[state.df["country"] == name]["iso3"].iloc[-1]
        out.append(
            {
                "country": name,
                "iso3": iso3,
                "predicted_tb_incidence": res["predicted_tb_incidence"],
                "current_tb_incidence": res["current_tb_incidence"],
                "bcg_coverage": res["simulated_bcg_coverage"],
                "hiv_prevalence": res["current_hiv_prevalence"],
            }
        )
    return out


@app.get("/model-info")
def model_info():
    _load()
    return {
        "metrics": state.metrics,
        "feature_importance": state.feature_importance,
        "training_period": "2000-2017",
        "test_period": "2018-2022",
        "n_countries": int(state.df["country"].nunique()),
    }


def _num(value):
    try:
        if value is None or pd.isna(value):
            return None
    except (TypeError, ValueError):
        return None
    return float(value)
