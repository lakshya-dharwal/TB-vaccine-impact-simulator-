"""Build the analysis-ready TB Futures dataset from tracked OWID + WHO files.

Required tracked files in `data/`:
  incidence-of-tuberculosis-sdgs.csv
  bcg-immunization-coverage-for-tb-among-1-year-olds.csv
  gdp-per-capita-worldbank.csv
  population.csv
  sites-providing-rapid-tuberculosis-diagnostics-per-million-people.csv

Required WHO context file in `data/raw/`:
  who_tb_data_merged.csv  -> country, region, income_level, fallback population

Output: data/processed/merged_tb_dataset.csv
"""

import os

import pandas as pd

DATA_DIR = "data"
RAW_DIR = os.path.join(DATA_DIR, "raw")
PROCESSED_DIR = os.path.join(DATA_DIR, "processed")
OUTPUT_PATH = os.path.join(PROCESSED_DIR, "merged_tb_dataset.csv")

WHO_FILE = os.path.join(RAW_DIR, "who_tb_data_merged.csv")

YEAR_MIN, YEAR_MAX = 2000, 2023
VALID_INCOME = {"L", "LM", "UM", "H"}

OWID_FILES = {
    "target": (
        "incidence-of-tuberculosis-sdgs.csv",
        "Estimated incidence of all forms of tuberculosis",
        "tb_incidence",
    ),
    "bcg": (
        "bcg-immunization-coverage-for-tb-among-1-year-olds.csv",
        "Tuberculosis vaccine (BCG)",
        "bcg_coverage",
    ),
    "gdp": (
        "gdp-per-capita-worldbank.csv",
        "GDP per capita",
        "gdp_per_capita",
    ),
    "population": (
        "population.csv",
        "Population",
        "population_owid",
    ),
    "rapid_dx": (
        "sites-providing-rapid-tuberculosis-diagnostics-per-million-people.csv",
        "Sites providing TB diagnostic services using molecular WHO-recommended rapid diagnostics per million population",
        "rapid_dx_sites",
    ),
}


def load_owid(filename: str, value_column: str, metric: str) -> pd.DataFrame:
    """Load an OWID CSV into (iso3, year, metric)."""
    path = os.path.join(DATA_DIR, filename)
    if not os.path.exists(path):
        raise FileNotFoundError(f"Missing required tracked data file: {path}")
    df = pd.read_csv(path)
    rename = {"Code": "iso3", "Year": "year", value_column: metric}
    df = df.rename(columns=rename)
    keep = ["iso3", "year", metric]
    return df[keep].copy()


def load_who_context() -> pd.DataFrame:
    """Load WHO region/income context and fallback population."""
    if not os.path.exists(WHO_FILE):
        raise FileNotFoundError(f"Missing required WHO context file: {WHO_FILE}")
    df = pd.read_csv(WHO_FILE, low_memory=False)
    df = df[["country", "iso3", "year", "g_whoregion", "population_size", "income_level"]].copy()
    df = df.rename(
        columns={
            "g_whoregion": "region",
            "population_size": "population_who",
        }
    )
    return df


def main():
    os.makedirs(PROCESSED_DIR, exist_ok=True)

    target = load_owid(*OWID_FILES["target"])
    bcg = load_owid(*OWID_FILES["bcg"])
    gdp = load_owid(*OWID_FILES["gdp"])
    population = load_owid(*OWID_FILES["population"])
    rapid_dx = load_owid(*OWID_FILES["rapid_dx"])
    who = load_who_context()

    merged = target.merge(bcg, on=["iso3", "year"], how="inner")
    merged = merged.merge(gdp, on=["iso3", "year"], how="inner")
    merged = merged.merge(population, on=["iso3", "year"], how="left")
    merged = merged.merge(rapid_dx, on=["iso3", "year"], how="left")
    merged = merged.merge(who, on=["iso3", "year"], how="inner")

    merged = merged.dropna(subset=["iso3"])
    merged = merged[merged["iso3"].astype(str).str.len() == 3]
    merged = merged[(merged["year"] >= YEAR_MIN) & (merged["year"] <= YEAR_MAX)]

    merged["population"] = merged["population_owid"].fillna(merged["population_who"])
    merged["tb_target_source"] = "owid_who_estimated_incidence"
    merged["tb_target_display"] = "WHO estimated TB incidence from OWID SDG series (per 100k)"

    required = ["tb_incidence", "bcg_coverage", "gdp_per_capita", "income_level", "region", "population"]
    merged = merged.dropna(subset=required)
    merged = merged[merged["income_level"].isin(VALID_INCOME)]
    merged = merged[(merged["tb_incidence"] > 0) & (merged["bcg_coverage"] >= 0) & (merged["bcg_coverage"] <= 100)]
    merged = merged[merged["gdp_per_capita"] > 0]
    merged = merged[merged["population"] > 0]

    final_cols = [
        "country",
        "iso3",
        "year",
        "tb_incidence",
        "tb_target_source",
        "tb_target_display",
        "bcg_coverage",
        "gdp_per_capita",
        "population",
        "income_level",
        "region",
        "rapid_dx_sites",
    ]
    merged = merged[final_cols].sort_values(["country", "year"]).reset_index(drop=True)
    merged.to_csv(OUTPUT_PATH, index=False)

    print("=" * 60)
    print("Processed dataset summary")
    print("=" * 60)
    print(f"Rows:               {len(merged)}")
    print(f"Countries:          {merged['country'].nunique()}")
    print(f"Year range:         {int(merged['year'].min())}-{int(merged['year'].max())}")
    print(f"Regions:            {sorted(merged['region'].dropna().unique())}")
    print(f"Income bands:       {sorted(merged['income_level'].dropna().unique())}")
    print(f"TB target source:   {merged['tb_target_display'].iloc[0]}")
    print(f"Rapid Dx coverage:  {int(merged['rapid_dx_sites'].notna().sum())} rows")
    print(f"\nSaved to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
