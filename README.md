# TB Futures

### A Global Health What-If Lab for Tuberculosis Prevention

![Python](https://img.shields.io/badge/Python-3.11+-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-Latest-green)
![scikit-learn](https://img.shields.io/badge/scikit--learn-Latest-orange)
![React](https://img.shields.io/badge/React-Vite-blue)
![License](https://img.shields.io/badge/License-MIT-lightgrey)

> "Pick a country, choose a prevention scenario, and explore how TB burden might
> change — powered by real WHO/OWID data and honest ML."

---

## What It Is

**TB Futures** is an interactive public-health scenario explorer that helps users
understand how vaccination coverage, economic conditions, and regional context shape
tuberculosis risk across countries.

It is **not** a policy-grade vaccine impact model. It is a what-if exploration tool
built on real WHO / OWID / World Bank data with explicit uncertainty communication.

Pick a country, choose a prevention scenario (or fine-tune individual factors), and see
the estimated change in TB burden — with a model-uncertainty interval, a plain-language
explanation, and a **Prioritization** view for ranking countries by estimated opportunity.

---

## Scenarios

| Scenario | What it does |
|----------|--------------|
| **Baseline** | No changes |
| **Vaccine Push** | BCG coverage +30 percentage points (capped at 99%) |
| **Income Level Up** | Bump income band up one tier (L → LM → UM → H) |
| **Combined** | BCG push + income band improvement |
| **Custom** | Override BCG, GDP, and income level individually |

---

## The ML Model

- **Type:** Tuned Random Forest Regressor with Linear Regression and Gradient Boosting comparisons
- **Features:** BCG coverage, log GDP per capita, year, one-hot income level (L/LM/UM/H),
  and one-hot WHO region
- **Target:** WHO estimated TB incidence per 100,000 population from the OWID SDG series
- **Transform:** `log1p(tb_incidence)` at train time, inverted with `expm1(...)` at inference time
- **Split:** Temporal — train 2000–2018, test 2019–2023
- **Tuning:** `RandomizedSearchCV` with `TimeSeriesSplit`
- **Uncertainty:** Bootstrap over the forest's trees (100 resamples), reported back in
  original incidence space

The simulation is a counterfactual: a country's most recent feature vector is taken and
only the chosen factors are modified; all else stays at real-world values.

The current trained model evaluates at roughly **R² = 0.443** on the held-out 2019–2023
window. That is an improvement over the earlier income/region-only build, but still
modest enough that the product should be treated as directional rather than predictive.

---

## Project Structure

```text
TB-Futures/
├── README.md
├── requirements.txt
├── pytest.ini
├── data/
│   ├── *.csv
│   ├── raw/
│   │   └── who_tb_data_merged.csv
│   └── processed/
│       └── merged_tb_dataset.csv
├── docs/
│   ├── DATA.md
│   ├── MODEL_CARD.md
│   └── TB_FUTURES_SOP.md
├── frontend/
│   ├── src/
│   ├── e2e/
│   └── package.json
├── src/
│   ├── data/
│   │   ├── download_data.py
│   │   └── process_data.py
│   ├── model/
│   │   ├── features.py
│   │   ├── train.py
│   │   ├── predict.py
│   │   ├── country_story.py
│   │   └── evaluate.py
│   ├── api/
│   │   └── main.py
│   └── ui/
│       ├── app.py
│       └── charts.py
├── models/
└── tests/
    ├── test_model.py
    ├── test_api.py
    ├── test_data.py
    └── test_predict_utils.py
```

---

## Getting Started

### Prerequisites
- Python 3.11+

### Run order

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Refresh the tracked OWID datasets into data/
python -m src.data.download_data

# 3. Build the processed modelling dataset
python -m src.data.process_data

# 4. Train and tune the models
python -m src.model.train

# 5. Evaluate on the held-out test set
python -m src.model.evaluate

# 6. Start the API
uvicorn src.api.main:app --reload --port 8000

# 7. Start the frontend
cd frontend
cp .env.example .env
npm install
npm run dev

# 8. Run the tests
pytest tests/ -q
```

---

## API Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Liveness check |
| GET | `/countries` | Sorted list of country names |
| GET | `/country/{name}` | Most-recent-year stats + country story |
| POST | `/simulate` | Run a scenario simulation |
| GET | `/map-data` | Per-country TB / BCG / GDP / rapid-dx context |
| GET | `/whatif-map?bcg=90` | Predicted TB burden at a uniform BCG level |
| GET | `/prioritize?bcg_target=90&top=20` | Ranked country opportunity list under a BCG target |
| GET | `/model-info` | Metrics, diagnostics, model card, and feature importance |

**POST /simulate request**

```json
{ "country": "Nigeria", "scenario": "combined" }
```

Optional overrides: `bcg_override`, `gdp_override`, `income_override` (L/LM/UM/H),
used with `"scenario": "custom"`.

---

## Data Sources

- OWID SDG series — WHO estimated incidence of all forms of tuberculosis
- WHO / UNICEF WUENIC via OWID — BCG immunization coverage among 1-year-olds
- World Bank via OWID — GDP per capita
- OWID — population
- OWID / WHO — rapid TB diagnostic sites per million population
- WHO Global Tuberculosis Programme — income level, WHO region, and fallback population context

All data is publicly available.

---

## Limitations and Disclaimer

This tool is built for education and portfolio demonstration. It is **not** for clinical
decisions, policy implementation, or research claims without expert review.

The model captures population-level patterns, not causal effects. It does not represent
transmission dynamics, reporting bias, lagged vaccine effects, or country-specific
confounders outside the feature set. Rapid-diagnostic-site density is shown for context
only and is not used as a model feature. The tool reports estimated **cases prevented**,
not lives saved.

---

## Frontend Note

The primary UI is now the React + Vite frontend in `frontend/`, which talks directly to
the FastAPI API. The older Streamlit app remains in `src/ui/` as a legacy prototype.

---

## Author

**Lakshya Dharwal** — BME Graduate, Arizona State University
Building at the intersection of biomedical engineering and clinical AI.
