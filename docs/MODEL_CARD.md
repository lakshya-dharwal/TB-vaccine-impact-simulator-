# TB Futures — Model Card

## Intended use
Educational / portfolio what-if exploration of how vaccination coverage, income,
and economic conditions relate to national tuberculosis burden, and prioritisation
of where BCG scale-up could avert the most cases. **Not** for clinical, policy, or
research decisions without expert review.

## Model
- Algorithm: Random Forest Regressor (tuned), with Linear Regression and Gradient
  Boosting as comparison baselines.
- Target: WHO modeled TB incidence per 100,000 (OWID SDG series), modelled in
  log space (`log1p`/`expm1`).
- Features: bcg_coverage, log_gdp, year, income_L, income_LM, income_UM, income_H, region_AFR, region_AMR, region_EMR, region_EUR, region_SEA, region_WPR.
- Tuning: randomized search over forest hyperparameters with 5-fold year-grouped
  cross-validation. Best params: {'n_estimators': 200, 'min_samples_leaf': 1, 'max_features': 'sqrt', 'max_depth': 16}.

## Data
- 154 countries, 2000–2023.
- Train rows (2000–2017): 2652. Test rows (2018–2023, held out): 875.
- Sources: WHO Global TB Programme (incidence, income band, region),
  WHO/UNICEF (BCG), World Bank/OWID (GDP, population). Rapid-diagnostics-sites is
  shown as context only (too sparse to model).

## Performance (held-out test set, original scale)
| Metric | Random Forest | Linear Regression | Gradient Boosting |
|---|---|---|---|
| R² | 0.394 | 0.220 | 0.266 |
| MAE (/100k) | 66.1 | 83.5 | 79.9 |
| RMSE (/100k) | 126.2 | 143.2 | 138.9 |

## Limitations
The model captures population-level statistical associations, not causation.
BCG is a childhood vaccine with limited adult efficacy, so its modelled effect is
partly a proxy for broader health-system strength. HIV prevalence and health
expenditure — both important TB drivers — are absent from the current data.
Counterfactual scenarios hold all other factors fixed, which rarely holds in
reality. Uncertainty intervals reflect model variance, not epidemiological certainty.
