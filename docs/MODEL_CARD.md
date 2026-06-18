# TB Futures Model Card

## Intended Use

TB Futures is a country-level educational what-if simulator for tuberculosis prevention and prioritization.
It is appropriate for exploratory portfolio demos and directional screening, not for policy implementation,
clinical use, or causal claims.

## Data

- Target: WHO estimated TB incidence from OWID SDG series (per 100k)
- Time window: 2000-2023
- Features: bcg_coverage, log_gdp, year, income_L, income_LM, income_UM, income_H, region_AFR, region_AMR, region_EMR, region_EUR, region_SEA, region_WPR
- Context-only column: rapid diagnostic sites per million population

## Training Setup

- Target transform: log1p / expm1
- Train period: 2000-2018
- Test period: 2019-2023
- Random Forest tuned with RandomizedSearchCV + TimeSeriesSplit

## Held-out Metrics

- Random Forest: R²=0.443, MAE=63.1, RMSE=115.5
- Linear Regression: R²=0.240, MAE=82.0, RMSE=134.9
- Gradient Boosting: R²=0.315, MAE=76.8, RMSE=128.0

## Key Limitations

- Country-level associations are not causal effects.
- BCG coverage and GDP are incomplete proxies for prevention and system strength.
- Rapid diagnostic site density is shown as context only and is not part of the trained model.
- Error is not uniform across regions and income bands; inspect the diagnostics tables in the app.

## Diagnostics Snapshot

- Region rows: 6
- Income rows: 4
