# TB Futures Data Dictionary

## Processed Dataset

`data/processed/merged_tb_dataset.csv`

- `country`: WHO country name from the context file.
- `iso3`: ISO3 country code.
- `year`: Calendar year.
- `tb_incidence`: WHO estimated incidence of all forms of tuberculosis per 100,000 population, sourced from the OWID SDG series.
- `tb_target_source`: Stable machine-readable identifier for the target source.
- `tb_target_display`: Human-readable description of the target source.
- `bcg_coverage`: BCG immunization coverage among 1-year-olds (%).
- `gdp_per_capita`: GDP per capita (World Bank series via OWID).
- `population`: Population used for cases-prevented calculations. Prefers OWID population, falls back to WHO population.
- `income_level`: WHO income band (`L`, `LM`, `UM`, `H`).
- `region`: WHO region code.
- `rapid_dx_sites`: Sites providing molecular WHO-recommended rapid TB diagnostics per million population. Context-only column, not a model feature.

## Raw Sources

- `data/incidence-of-tuberculosis-sdgs.csv`
- `data/bcg-immunization-coverage-for-tb-among-1-year-olds.csv`
- `data/gdp-per-capita-worldbank.csv`
- `data/population.csv`
- `data/sites-providing-rapid-tuberculosis-diagnostics-per-million-people.csv`
- `data/raw/who_tb_data_merged.csv`
