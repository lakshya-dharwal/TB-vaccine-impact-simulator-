"""TB Futures FastAPI backend."""

import json
from pathlib import Path

import joblib
import pandas as pd
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from src.model.country_story import generate_country_story
from src.model.predict import prioritize, simulate

BASE_DIR = Path(__file__).resolve().parents[2]
DATA_PATH = BASE_DIR / "data/processed/merged_tb_dataset.csv"
MODELS_DIR = BASE_DIR / "models"
MODEL_CARD_PATH = BASE_DIR / "docs/MODEL_CARD.md"
FRONTEND_DIST = BASE_DIR / "frontend/dist"
TRAINING_PERIOD = "2000-2018"
TEST_PERIOD = "2019-2023"

app = FastAPI(title="TB Futures API", version="3.0.0")
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
    model_card = None


state = State()


def _load():
    if state.df is None:
        state.df = pd.read_csv(DATA_PATH)
    if state.model is None:
        state.model = joblib.load(MODELS_DIR / "rf_model.pkl")
    if state.schema is None:
        with open(MODELS_DIR / "schema.json") as f:
            state.schema = json.load(f)
    if state.metrics is None:
        with open(MODELS_DIR / "model_metrics.json") as f:
            state.metrics = json.load(f)
    if state.feature_importance is None:
        with open(MODELS_DIR / "feature_importance.json") as f:
            state.feature_importance = json.load(f)
    if state.diagnostics is None:
        with open(MODELS_DIR / "diagnostics.json") as f:
            state.diagnostics = json.load(f)
    if state.model_card is None:
        with open(MODEL_CARD_PATH) as f:
            state.model_card = f.read()


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


def _latest_country_rows():
    return state.df.sort_values("year").groupby("country", as_index=False).last()


def _num(value):
    try:
        if value is None or pd.isna(value):
            return None
    except (TypeError, ValueError):
        return None
    return float(value)


class SimulationRequest(BaseModel):
    country: str
    scenario: str
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
    _load()
    return {
        "covariates": state.schema["covariates"],
        "scenarios": state.schema["scenarios"],
        "income_levels": state.schema["income_levels"],
        "regions": state.schema["regions"],
        "use_income": state.schema["use_income"],
        "target_source": state.schema.get("target_source"),
        "target_display": state.schema.get("target_display"),
        "target_transform": state.schema.get("target_transform"),
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
        "tb_target_display": state.schema.get("target_display"),
        "population": _num(row.get("population")),
        "income_level": row.get("income_level") if state.schema["use_income"] else None,
        "region": row.get("region"),
        "country_story": generate_country_story(country_name, row.to_dict()),
        "rapid_dx_sites": _num(row.get("rapid_dx_sites")),
    }
    for cov in ("bcg_coverage", "gdp_per_capita", "hiv_prevalence", "health_expenditure"):
        if cov in row.index:
            out[cov] = _num(row.get(cov))
    return out


@app.post("/simulate", response_model=SimulationResponse)
def run_simulation(req: SimulationRequest):
    _load()
    _latest_row(req.country)

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

    return simulate(req.country, req.scenario, overrides, state.df, state.model, state.schema)


@app.get("/map-data")
def map_data():
    _load()
    latest = _latest_country_rows()
    out = []
    for _, row in latest.iterrows():
        out.append(
            {
                "country": row["country"],
                "iso3": row["iso3"],
                "tb_incidence": _num(row.get("tb_incidence")),
                "bcg_coverage": _num(row.get("bcg_coverage")),
                "gdp_per_capita": _num(row.get("gdp_per_capita")),
                "rapid_dx_sites": _num(row.get("rapid_dx_sites")),
                "population": _num(row.get("population")),
                "region": row.get("region"),
            }
        )
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
            res = simulate(
                name,
                "custom",
                {"bcg_coverage": min(bcg, 99.0)},
                state.df,
                state.model,
                state.schema,
                include_ci=False,
                include_story=False,
            )
        except KeyError:
            continue
        row = _latest_row(name)
        out.append(
            {
                "country": name,
                "iso3": row["iso3"],
                "predicted_tb_incidence": res["predicted_tb_incidence"],
                "current_tb_incidence": res["current_tb_incidence"],
                "bcg_coverage": res["simulated_bcg_coverage"],
                "current_bcg_coverage": res["current_bcg_coverage"],
                "gdp_per_capita": _num(row.get("gdp_per_capita")),
                "rapid_dx_sites": _num(row.get("rapid_dx_sites")),
            }
        )
    return out


@app.get("/prioritize")
def prioritize_view(bcg_target: float = 90.0, top: int = 20):
    _load()
    rows = prioritize(state.df, state.model, state.schema, bcg_target=bcg_target, top=top)
    return {
        "bcg_target": bcg_target,
        "top": max(1, int(top)),
        "target_display": state.schema.get("target_display"),
        "rows": rows,
    }


@app.get("/model-info")
def model_info():
    _load()
    return {
        "metrics": state.metrics,
        "feature_importance": state.feature_importance,
        "diagnostics": state.diagnostics,
        "model_card": state.model_card,
        "schema": state.schema,
        "target_source": state.schema.get("target_source"),
        "target_display": state.schema.get("target_display"),
        "training_period": TRAINING_PERIOD,
        "test_period": TEST_PERIOD,
        "n_countries": int(state.df["country"].nunique()),
    }


if (FRONTEND_DIST / "assets").is_dir():
    app.mount("/assets", StaticFiles(directory=FRONTEND_DIST / "assets"), name="frontend-assets")


def _frontend_response(path: str):
    if not FRONTEND_DIST.is_dir():
        raise HTTPException(status_code=404, detail="Frontend build not found.")

    candidate = (FRONTEND_DIST / path).resolve()
    if candidate.is_file() and FRONTEND_DIST in candidate.parents:
        return FileResponse(candidate)
    return FileResponse(FRONTEND_DIST / "index.html")


@app.get("/")
def frontend_root():
    return _frontend_response("index.html")


@app.get("/{path:path}")
def frontend_app(path: str):
    return _frontend_response(path)
