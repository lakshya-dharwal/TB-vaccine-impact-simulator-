# TB Vaccine Impact Simulator

A counterfactual simulation tool that predicts TB burden reduction under different BCG vaccine coverage scenarios — trained on WHO/UNICEF/World Bank data across 180 countries from 2000 to 2022.

![Python](https://img.shields.io/badge/Python-3.11+-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-Latest-green)
![scikit-learn](https://img.shields.io/badge/scikit--learn-Latest-orange)
![Streamlit](https://img.shields.io/badge/Streamlit-Latest-red)
![License](https://img.shields.io/badge/License-MIT-lightgrey)

---

## What It Does

Select any country. Adjust BCG vaccine coverage with a slider. The model predicts how TB incidence would change — with a 95% confidence interval — in real time.

This is not a drug discovery engine or a clinical decision tool. It is a hypothesis generation and policy prioritization tool that compresses days of manual data analysis into 30 seconds.

**The question it answers:**
> "If BCG coverage in Nigeria increases from 54% to 80%, how much does predicted TB incidence drop — and how many lives does that represent?"

---

## The Biological Problem

Tuberculosis (TB) kills 1.3 million people per year. 87% of cases occur in 30 high-burden countries, almost all of them low and middle income. BCG (Bacillus Calmette-Guérin), developed in 1921, remains the only licensed TB vaccine. It protects children against severe TB with 70-80% efficacy but provides inconsistent protection in adults — which is why next-generation vaccines like M72/AS01E (currently in Phase 3 trials at Gates Medical Research Institute) are critical.

BCG coverage varies enormously. Some countries achieve 99% coverage. Others sit below 50%. But the relationship between coverage and TB burden is not linear — GDP, HIV prevalence, healthcare access, and population density all interact. This tool models those interactions and lets users simulate the impact of coverage changes on TB incidence at a country level.

---

## Demo

> Screenshot / GIF placeholder — add after deployment

**Example output for Nigeria:**

| Metric | Value |
|--------|-------|
| Current BCG Coverage | 54% |
| Simulated BCG Coverage | 80% |
| Current TB Incidence | 219 / 100k |
| Predicted TB Incidence | 172.4 / 100k |
| Absolute Reduction | 46.6 / 100k |
| Relative Reduction | 21.3% |
| Estimated Lives Saved / Year | ~101,000 |
| 95% Confidence Interval | 160.2 — 184.6 / 100k |

---

## Features

- Country selector with live stats panel for all 180 WHO member states
- BCG coverage slider with real-time counterfactual prediction
- 95% confidence intervals via bootstrap resampling (100 models)
- Estimated lives saved per year based on country population
- Interactive Plotly choropleth world map colored by TB burden
- Toggle between actual burden and predicted burden at universal 90% coverage
- Feature importance chart explaining what drives TB predictions
- Model transparency panel with training data size, metrics, and disclaimer
- Downloadable CSV of simulation results
- FastAPI backend with documented REST endpoint

---

## The ML Model

**Type:** Random Forest Regressor (scikit-learn)

**Features:**
- BCG coverage (%)
- GDP per capita (USD, log-transformed)
- Health expenditure (% of GDP)
- HIV prevalence (% of adults 15-49)
- WHO region (one-hot encoded)
- Year

**Target:** TB incidence per 100,000 population per year

**Training data:** 180 countries × 22 years (2000-2021) = ~3,960 rows

**Train/test split:** Temporal — trained on 2000-2017, tested on 2018-2022

**Confidence intervals:** Bootstrap resampling across 100 model instances, reporting 2.5th and 97.5th percentile as 95% CI

**Validation metrics:**

| Metric | Value |
|--------|-------|
| R² (test set) | TBD after training |
| MAE (test set) | TBD after training |
| RMSE (test set) | TBD after training |

**Counterfactual layer:** To simulate a new BCG coverage value, the country's feature vector is taken with only the BCG coverage value replaced. All other features (GDP, HIV, etc.) remain identical to real-world values. The model predicts on this modified vector. This is a standard counterfactual inference approach used in epidemiology and health economics.

---

## Data Sources

| Dataset | Source | Coverage |
|---------|--------|----------|
| BCG immunization coverage | WHO/UNICEF WUENIC estimates | 180 countries, 1980-2023 |
| TB incidence per 100k | WHO Global TB Programme | 180 countries, 2000-2022 |
| GDP per capita | World Bank Open Data | 180 countries, 2000-2022 |
| Health expenditure % GDP | World Bank Open Data | 180 countries, 2000-2022 |
| HIV prevalence % | World Bank / UNAIDS | 180 countries, 2000-2022 |
| Population | World Bank Open Data | 180 countries, 2000-2022 |

All data is publicly available and free to access.

---

## Tech Stack

| Layer | Tool |
|-------|------|
| Backend API | FastAPI + Uvicorn |
| Input validation | Pydantic v2 |
| Machine learning | scikit-learn |
| Data processing | Pandas + NumPy |
| Frontend | Streamlit |
| Visualization | Plotly |
| HTTP client | httpx |
| Testing | pytest |
| Deployment | Render |

---

## Project Structure

```
tb-vaccine-simulator/
├── README.md
├── requirements.txt
├── .env.example
│
├── data/
│   ├── raw/                        ← downloaded source CSVs
│   └── processed/
│       └── merged_tb_dataset.csv   ← final analysis-ready dataset
│
├── src/
│   ├── data/
│   │   ├── download_data.py        ← downloads all 4 datasets
│   │   └── process_data.py         ← cleans, merges, engineers features
│   │
│   ├── model/
│   │   ├── train.py                ← trains Random Forest, saves model
│   │   ├── predict.py              ← inference + bootstrap CI
│   │   └── evaluate.py             ← R², MAE, RMSE on test set
│   │
│   ├── api/
│   │   └── main.py                 ← FastAPI /simulate endpoint
│   │
│   └── ui/
│       └── app.py                  ← Streamlit frontend
│
├── models/
│   └── rf_model.pkl                ← saved trained model
│
└── tests/
    ├── test_model.py
    ├── test_api.py
    └── test_data.py
```

---

## API Reference

### POST /simulate

Runs a counterfactual simulation for a given country and BCG coverage scenario.

**Request:**
```json
{
  "country": "Nigeria",
  "bcg_coverage_pct": 80.0
}
```

**Response:**
```json
{
  "country": "Nigeria",
  "current_bcg_coverage": 54.0,
  "simulated_bcg_coverage": 80.0,
  "current_tb_incidence": 219.0,
  "predicted_tb_incidence": 172.4,
  "absolute_reduction": 46.6,
  "relative_reduction_pct": 21.3,
  "confidence_interval_lower": 160.2,
  "confidence_interval_upper": 184.6,
  "population": 218541000,
  "estimated_lives_saved_per_year": 101834,
  "model_r2": 0.847,
  "disclaimer": "Predictions are estimates based on historical population-level data. Not for clinical use."
}
```

---

## Getting Started

### Prerequisites
- Python 3.11+
- pip

### Installation

```bash
git clone https://github.com/ldharwal-asu/tb-vaccine-simulator
cd tb-vaccine-simulator
pip install -r requirements.txt
```

### Download and Process Data

```bash
python src/data/download_data.py
python src/data/process_data.py
```

### Train the Model

```bash
python src/model/train.py
```

### Run the API

```bash
uvicorn src.api.main:app --reload --port 8000
```

### Run the Frontend

```bash
streamlit run src/ui/app.py
```

### Run Tests

```bash
pytest tests/ -v
```

---

## Limitations and Disclaimer

This tool is built for research and educational purposes. It is not intended for clinical use or policy decisions without expert validation.

Key limitations:

- The model captures population-level historical patterns. It cannot account for country-specific policy changes, conflict, supply chain disruption, or emerging drug resistance trends.
- Counterfactual predictions assume all other factors remain constant when BCG coverage changes. In reality, coverage improvements often co-occur with broader health system strengthening.
- The BCG-TB relationship varies by strain, latitude, and local TB prevalence — effects that are partially captured by the region feature but not fully.
- ADMET and confidence intervals reflect model uncertainty, not uncertainty in the underlying epidemiology.
- MDR-TB dynamics are not modeled separately.

Predictions represent model estimates based on historical trends, not projections endorsed by WHO, UNICEF, or Gates Medical Research Institute.

---

## Why I Built This

I built this after a conversation with a senior scientist working on the M72/AS01E TB vaccine Phase 3 program at Gates Medical Research Institute. The M72 vaccine is designed for LMIC populations where BCG coverage is insufficient and adult TB burden remains high.

Understanding which countries are most underserved — and simulating how much coverage improvements would reduce TB burden — is directly relevant to trial site selection, manufacturing volume planning, and vaccine rollout prioritization.

This tool does not replace that analysis. It makes the first pass faster.

---

## Author

**Lakshya Dharwal**
BME Graduate, Arizona State University (May 2026)
Building at the intersection of biomedical engineering and clinical AI.

[Portfolio](https://lakshyadharwal.vercel.app) · [LinkedIn](https://linkedin.com/in/lakshyadharwal) · [GitHub](https://github.com/ldharwal-asu)
