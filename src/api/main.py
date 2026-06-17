"""TB Futures FastAPI backend.

Serves country statistics, the choropleth map data, model metadata, and runs
counterfactual simulations against the trained Random Forest. The set of
covariates and scenarios is data-adaptive and read from the saved schema.
"""

import json
import os

import joblib
import pandas as pd
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from src.model.country_story import generate_country_story
from src.model.predict import prioritize, simulate

DATA_PATH = "data/processed/merged_tb_dataset.csv"
MODELS_DIR = "models"

app = FastAPI(title="TB Futures API", version="2.0.0")
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
    schema = None
    metrics = None
    feature_importance = None
    diagnostics = None


state = State()


def _load_json(name):
    with open(os.path.join(MODELS_DIR, name)) as f:
        return json.load(f)


def _load():
    if state.df is None:
        state.df = pd.read_csv(DATA_PATH)
    if state.model is None:
        state.model = joblib.load(os.path.join(MODELS_DIR, "rf_model.pkl"))
    if state.schema is None:
        state.schema = _load_json("schema.json")
    if state.metrics is None:
        state.metrics = _load_json("model_metrics.json")
    if state.feature_importance is None:
        state.feature_importance = _load_json("feature_importance.json")
    if state.diagnostics is None:
        try:
            state.diagnostics = _load_json("diagnostics.json")
        except FileNotFoundError:
            state.diagnostics = {}


@app.on_event("startup")
def startup():
    try:
        _load()
    except FileNotFoundError:
        pass


def _latest_row(country: str):
    sub = state.df[state.df["country"] == country]
    if sub.empty:
        raise HTTPException(status_code=422, detail=f"Unknown country: {country}")
    return sub.sort_values("year").iloc[-1]


def _num(value):
    try:
        if value is None or pd.isna(value):
            return None
    except (TypeError, ValueError):
        return None
    return float(value)


class SimulationRequest(BaseModel):
    country: str
    scenario: str  # baseline, vaccine_push, hiv_control, health_boost, income_up, combined, custom
    bcg_override: float | None = None
    hiv_override: float | None = None
    gdp_override: float | None = None
    health_override: float | None = None
    income_override: str | None = None


class SimulationResponse(BaseModel):
    country: str
    scenario: str
    current_bcg_coverage: float | None = None
    simulated_bcg_coverage: float | None = None
    current_hiv_prevalence: float | None = None
    simulated_hiv_prevalence: float | None = None
    current_gdp_per_capita: float | None = None
    simulated_gdp_per_capita: float | None = None
    current_health_expenditure: float | None = None
    simulated_health_expenditure: float | None = None
    current_income_level: str | None = None
    simulated_income_level: str | None = None
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


@app.get("/config")
def config():
    """Data-adaptive layout: which covariates and scenarios are available."""
    _load()
    return {
        "covariates": state.schema["covariates"],
        "scenarios": state.schema["scenarios"],
        "income_levels": state.schema["income_levels"],
        "regions": state.schema["regions"],
        "use_income": state.schema["use_income"],
    }


@app.get("/countries")
def countries():
    _load()
    return sorted(state.df["country"].unique().tolist())


@app.get("/country/{country_name}")
def country(country_name: str):
    _load()
    row = _latest_row(country_name)
    out = {
        "country": country_name,
        "year": int(row["year"]),
        "tb_incidence": _num(row.get("tb_incidence")),
        "population": _num(row.get("population")),
        "income_level": row.get("income_level") if state.schema["use_income"] else None,
        "region": row.get("region"),
        "country_story": generate_country_story(country_name, row.to_dict()),
    }
    for cov in ("bcg_coverage", "hiv_prevalence", "gdp_per_capita",
                "health_expenditure", "rapid_dx_sites"):
        if cov in row.index:
            out[cov] = _num(row.get(cov))
    return out


@app.post("/simulate", response_model=SimulationResponse)
def run_simulation(req: SimulationRequest):
    _load()
    _latest_row(req.country)  # 422 on unknown country

    valid = set(state.schema["scenarios"]) | {"custom"}
    if req.scenario not in valid:
        raise HTTPException(status_code=422, detail=f"Unknown scenario: {req.scenario}")

    overrides = {
        "bcg_coverage": req.bcg_override,
        "hiv_prevalence": req.hiv_override,
        "gdp_per_capita": req.gdp_override,
        "health_expenditure": req.health_override,
        "income_level": req.income_override,
    }
    overrides = {k: v for k, v in overrides.items() if v is not None}

    return simulate(req.country, req.scenario, overrides, state.df, state.model,
                    state.schema)


@app.get("/map-data")
def map_data():
    _load()
    latest = state.df.sort_values("year").groupby("country", as_index=False).last()
    out = []
    for _, row in latest.iterrows():
        out.append({
            "country": row["country"],
            "iso3": row["iso3"],
            "tb_incidence": _num(row.get("tb_incidence")),
            "bcg_coverage": _num(row.get("bcg_coverage")),
            "hiv_prevalence": _num(row.get("hiv_prevalence")),
            "gdp_per_capita": _num(row.get("gdp_per_capita")),
            "rapid_dx_sites": _num(row.get("rapid_dx_sites")),
        })
    return out


@app.get("/whatif-map")
def whatif_map(bcg: float = 90.0):
    """Predicted TB burden for every country if BCG coverage were set to `bcg`%."""
    _load()
    if "bcg_coverage" not in state.schema["numeric"]:
        raise HTTPException(status_code=404, detail="BCG coverage is not in this model.")
    out = []
    for name in state.df["country"].unique().tolist():
        try:
            res = simulate(name, "custom", {"bcg_coverage": bcg}, state.df,
                           state.model, state.schema)
        except KeyError:
            continue
        iso3 = state.df[state.df["country"] == name]["iso3"].iloc[-1]
        out.append({
            "country": name,
            "iso3": iso3,
            "predicted_tb_incidence": res["predicted_tb_incidence"],
            "current_tb_incidence": res["current_tb_incidence"],
            "bcg_coverage": res["simulated_bcg_coverage"],
            "hiv_prevalence": res["current_hiv_prevalence"],
        })
    return out


@app.get("/prioritize")
def prioritize_countries(bcg_target: float = 90.0, top: int = 25):
    """Rank countries by estimated TB cases prevented per year under a BCG target."""
    _load()
    if "bcg_coverage" not in state.schema["numeric"]:
        raise HTTPException(status_code=404, detail="BCG coverage is not in this model.")
    ranked = prioritize(state.df, state.model, state.schema, bcg_target=bcg_target,
                        top=top)
    return {"bcg_target": bcg_target, "countries": ranked}


@app.get("/model-info")
def model_info():
    _load()
    return {
        "metrics": state.metrics,
        "feature_importance": state.feature_importance,
        "diagnostics": state.diagnostics,
        "schema": state.schema,
        "training_period": "2000-2017",
        "test_period": "2018-2023",
        "n_countries": int(state.df["country"].nunique()),
    }
