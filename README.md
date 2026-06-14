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
| **Baseline** | No changes |
| **Vaccine Push** | BCG coverage +30 percentage points (capped at 99%) |
| **HIV Control** | HIV prevalence × 0.75 |
| **Health System Boost** | Health expenditure × 1.25 |
| **Combined** | All three of the above together |
| **Custom** | Override BCG, HIV, health spend, and GDP with individual sliders |

---

## The ML Model

- **Type:** Random Forest Regressor (with a Linear Regression baseline for comparison)
- **Features:** BCG coverage, log(GDP per capita), health expenditure, HIV prevalence,
  year, one-hot WHO region
- **Target:** TB incidence per 100,000 population
- **Split:** Temporal — train 2000–2017, test 2018–2022 (held out)
- **Uncertainty:** Bootstrap over the forest's trees (exactly 100 resamples), reporting
  the 2.5th–97.5th percentile as a 95% model-uncertainty interval

The simulation is a counterfactual: a country's most recent feature vector is taken and
only the chosen factors are modified; all else stays at real-world values.

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
│   │   ├── download_data.py        ← downloads the 6 source datasets
│   │   ├── process_data.py         ← cleans, merges, adds WHO region
│   │   └── who_regions.py          ← ISO3 → WHO region mapping
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
- Network access to `ourworldindata.org` (for the data download step)

### Run order

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Download real data (writes to data/raw/)
python src/data/download_data.py

# 3. Process and merge data (writes data/processed/merged_tb_dataset.csv)
python src/data/process_data.py

# 4. Train the models (writes models/*.pkl + metadata)
python src/model/train.py

# 5. Evaluate on the held-out test set
python src/model/evaluate.py

# 6. Start the API (terminal 1)
uvicorn src.api.main:app --reload --port 8000

# 7. Start the frontend (terminal 2)
streamlit run src/ui/app.py

# 8. Run the tests
pytest tests/ -v
```

If the data download fails (for example, behind a network egress allowlist), the script
prints the exact URLs to download manually into `data/raw/`.

---

## API Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Liveness check |
| GET | `/countries` | Sorted list of country names |
| GET | `/country/{name}` | Most-recent-year stats + country story |
| POST | `/simulate` | Run a scenario simulation |
| GET | `/map-data` | Per-country TB / BCG / HIV for the choropleth |
| GET | `/whatif-map?bcg=90` | Predicted TB burden at a uniform BCG level |
| GET | `/model-info` | Model metrics + feature importance |

**POST /simulate request**

```json
{ "country": "Nigeria", "scenario": "combined" }
```

Optional overrides: `bcg_override`, `hiv_override`, `health_override`, `gdp_override`
(used with `"scenario": "custom"`).

---

## Data Sources

- WHO / UNICEF WUENIC Immunization Coverage Estimates (BCG)
- WHO Global Tuberculosis Programme (TB incidence)
- Our World in Data — TB, HIV, GDP per capita, health expenditure, population
- World Bank Development Indicators / UNAIDS

All data is publicly available and free to access.

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
