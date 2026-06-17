# TB Futures

### A Global Health What-If Lab for Tuberculosis Prevention

![Python](https://img.shields.io/badge/Python-3.11+-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-Latest-green)
![scikit-learn](https://img.shields.io/badge/scikit--learn-Latest-orange)
![Streamlit](https://img.shields.io/badge/Streamlit-Latest-red)
![License](https://img.shields.io/badge/License-MIT-lightgrey)

> "Pick a country, choose a prevention scenario, and explore how TB burden might
> change — powered by real WHO data and honest ML."

---

## What It Is

**TB Futures** is an interactive public-health scenario explorer that helps users
understand how vaccination coverage, HIV burden, healthcare investment, and economic
conditions shape tuberculosis risk across ~180 countries.

It is **not** a policy-grade vaccine impact model. It is a what-if exploration tool
built on real WHO / UNICEF / World Bank data with honest uncertainty communication.

Pick a country, choose a prevention scenario (or fine-tune individual factors), and see
the estimated change in TB burden — with a model-uncertainty interval and a clear
"reality check" about what the estimate does and does not mean.

---

## Scenarios

| Scenario | What it does |
|----------|--------------|
| **Baseline** | No changes (anchored to the country's observed incidence) |
| **Vaccine Push** | BCG coverage +30 percentage points (capped at 99%) |
| **Economic Development** | GDP per capita × 1.25 |
| **Combined** | Both of the above together |
| **Custom** | Override BCG coverage and GDP individually |

Income level and WHO region are model **features/context**, not intervention levers
(a one-tier income jump is not a credible, graded what-if).

The **Prioritization** view ranks countries by estimated TB cases prevented per year if
BCG coverage were raised to a target — burden × population × the coverage gap — as a guide
to where vaccination investment could matter most.

---

## The ML Model

- **Type:** tuned Random Forest Regressor, with Linear Regression and Gradient Boosting
  baselines.
- **Features:** BCG coverage, log(GDP per capita), year, one-hot income level (L/LM/UM/H),
  one-hot WHO region.
- **Target:** **WHO estimated TB incidence per 100,000** (OWID SDG series), modelled in
  log space (`log1p`/`expm1`) because the target is right-skewed.
- **Tuning:** randomized search over forest hyperparameters with 5-fold year-grouped
  cross-validation. **Split:** temporal — train 2000–2017, test 2018–2023 (held out).
- **Counterfactual:** the model estimates the *change* between a country's baseline and
  the intervention (both predicted by the model, so baseline error cancels), and applies
  that change to the real observed incidence.
- **Uncertainty:** bootstrap over the forest's trees (exactly 100 resamples), 2.5th–97.5th
  percentile, in original units.

See [`docs/MODEL_CARD.md`](docs/MODEL_CARD.md) for metrics and limitations, and
[`docs/DATA.md`](docs/DATA.md) for the data dictionary.

---

## Project Structure

```
TB-Futures/
├── README.md
├── requirements.txt
├── .gitignore
├── pytest.ini
│
├── data/
│   ├── raw/                        ← downloaded source CSVs
│   └── processed/
│       └── merged_tb_dataset.csv   ← final analysis-ready dataset
│
├── src/
│   ├── data/
│   │   ├── download_data.py        ← downloads BCG + HIV from OWID
│   │   └── process_data.py         ← merges WHO + BCG + HIV, derives TB incidence
│   ├── model/
│   │   ├── features.py             ← shared feature engineering
│   │   ├── train.py                ← trains RF + LR, saves artifacts
│   │   ├── predict.py              ← simulation + bootstrap CI
│   │   ├── country_story.py        ← plain-English narratives
│   │   └── evaluate.py             ← test-set metrics
│   ├── api/
│   │   └── main.py                 ← FastAPI endpoints
│   └── ui/
│       ├── app.py                  ← Streamlit frontend
│       └── charts.py               ← Plotly figures + formatters
│
├── models/                         ← saved model + metadata (pkl gitignored)
└── tests/
    ├── test_model.py
    ├── test_api.py
    └── test_data.py
```

---

## Getting Started

### Prerequisites
- Python 3.11+
- The source data is already committed (`data/` and `who_tb_data_merged.csv`), so no
  download is needed.

### Run order

```bash
# 1. Install dependencies
pip install -r requirements.txt

# Run scripts from the repo root. The `python -m` form is canonical; the plain
# `python src/...` form also works.

# 2. Process and merge the committed sources -> data/processed/merged_tb_dataset.csv
python -m src.data.process_data

# 3. Train the models (writes models/*.pkl + metadata + docs/MODEL_CARD.md)
python -m src.model.train

# 4. Evaluate on the held-out test set
python -m src.model.evaluate

# 5. Start the API (terminal 1)
uvicorn src.api.main:app --reload --port 8000

# 7. Start the frontend (terminal 2)
streamlit run src/ui/app.py

# 8. Run the tests
pytest tests/ -v
```

If the data download fails (for example, behind a network egress allowlist), the script
prints the exact URLs to download manually into `data/raw/`.

A `Makefile` wraps the common tasks: `make install`, `make pipeline` (data + train +
evaluate), `make test`, `make api`, `make ui`, `make docker-up`.

---

## Run with Docker

The image builds the dataset and trains the model at build time, so the container starts
ready to serve. Run the full stack (API + UI) locally with one command:

```bash
docker compose up --build
# UI  -> http://localhost:8501
# API -> http://localhost:8000
```

## Deploy to Render

`render.yaml` is a Render Blueprint that deploys two Docker web services — the API and
the Streamlit UI. Push to GitHub, create a new Blueprint on Render pointing at this repo,
and it provisions both. The UI's `TB_API_BASE` is wired to the API service automatically
(the app prepends `https://` when the host has no scheme).

Continuous integration runs on GitHub Actions (`.github/workflows/ci.yml`): it builds the
dataset, trains the model, runs the test suite, and builds the Docker image on every push.

---

## API Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Liveness check |
| GET | `/config` | Data-adaptive covariates + available scenarios |
| GET | `/countries` | Sorted list of country names |
| GET | `/country/{name}` | Most-recent-year stats + country story |
| POST | `/simulate` | Run a scenario simulation |
| GET | `/map-data` | Per-country TB / BCG / GDP / detection for the choropleth |
| GET | `/whatif-map?bcg=90` | Predicted TB burden at a uniform BCG level |
| GET | `/prioritize?bcg_target=90&top=25` | Countries ranked by cases prevented |
| GET | `/model-info` | Model metrics, feature importance, diagnostics |

**POST /simulate request**

```json
{ "country": "Nigeria", "scenario": "combined" }
```

Optional overrides: `bcg_override`, `gdp_override`, used with `"scenario": "custom"`.

---

## Data Sources

- **TB incidence (target)** — WHO estimate via Our World in Data
  (`incidence-of-tuberculosis-sdgs`)
- **BCG coverage** — WHO/UNICEF via OWID
- **GDP per capita** — World Bank via OWID
- **Population** — OWID
- **Income band + WHO region** — WHO Global TB Programme (`who_tb_data_merged.csv`)
- **Rapid TB diagnostic sites** — WHO (context layer only; sparse 2020–2023)

All data is publicly available and free to access. See [`docs/DATA.md`](docs/DATA.md).

---

## Limitations and Disclaimer

This tool is built for education and portfolio demonstration. It is **not** for clinical
decisions, policy implementation, or research claims without expert review.

The Random Forest model captures real statistical patterns in the data but cannot account
for reporting bias, transmission dynamics, time lags between vaccination and disease
burden, or country-specific confounders not present in the dataset. The uncertainty
interval reflects ML model variance, not epidemiological certainty. The tool reports
estimated **cases prevented**, not lives saved.

---

## Author

**Lakshya Dharwal** — BME Graduate, Arizona State University
Building at the intersection of biomedical engineering and clinical AI.
