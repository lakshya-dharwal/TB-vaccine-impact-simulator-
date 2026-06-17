# TB Futures — Data Dictionary

## Source files (`data/`, committed)

| File | Provides | Notes |
|---|---|---|
| `incidence-of-tuberculosis-sdgs.csv` | TB incidence (target) | WHO modeled estimate, per 100k, 2000–2024, 215 countries |
| `bcg-immunization-coverage-for-tb-among-1-year-olds.csv` | `bcg_coverage` | % of 1-year-olds, 163 countries |
| `gdp-per-capita-worldbank.csv` | `gdp_per_capita` | constant USD; also carries an OWID world-region column (unused) |
| `population.csv` | `population` | used for cases-prevented math |
| `sites-...rapid-tuberculosis-diagnostics-per-million-people.csv` | `rapid_dx_sites` | **context only**, sparse (2020–2023) |
| `who_tb_data_merged.csv` (root / `data/raw/`) | `income_level`, `region` | WHO Global TB Programme notifications file |

OWID grapher CSVs share the layout `Entity, Code, Year, <value>`; `Code` is the ISO3.

## Processed dataset (`data/processed/merged_tb_dataset.csv`)

Built by `src/data/process_data.py`, merged on `(iso3, year)`, filtered to 2000–2023, and
kept only where the target, BCG, GDP, income band, and region are all present.

| Column | Type | Description |
|---|---|---|
| `country`, `iso3`, `year` | str/int | identity |
| `tb_incidence` | float | **target** — WHO estimated TB incidence / 100k |
| `bcg_coverage` | float | BCG coverage % (feature) |
| `gdp_per_capita` | float | GDP per capita; modelled as `log_gdp` (feature) |
| `population` | float | dedicated OWID series, WHO `population_size` fallback |
| `income_level` | str | World Bank band L / LM / UM / H (one-hot feature, context) |
| `region` | str | WHO region AFR/AMR/EMR/EUR/SEA/WPR (one-hot feature) |
| `rapid_dx_sites` | float | rapid molecular dx sites / million — **context only, not a feature** |

Typical result: **~3,500 rows, ~154 countries, 2000–2023**.

## Model features
`bcg_coverage`, `log_gdp`, `year`, one-hot `income_*`, one-hot `region_*`. Detected
adaptively by `src/model/features.py:detect_schema` and saved to `models/schema.json`.
