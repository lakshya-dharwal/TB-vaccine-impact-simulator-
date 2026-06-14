"""Build the analysis-ready TB Futures dataset from whatever sources are present.

Always required:
  who_tb_data_merged.csv  WHO TB notifications — provides c_newinc,
                          population_size, income_level, g_whoregion. We derive
                          tb_incidence = c_newinc / population_size * 100,000.

Optional OWID grapher CSVs (Entity, Code, Year, <value>) in data/raw/. Each is
merged in only if its file exists, and the corresponding feature is dropped if
it is absent:
  bcg_coverage.csv        -> bcg_coverage
  hiv_prevalence.csv      -> hiv_prevalence
  gdp_per_capita.csv      -> gdp_per_capita
  health_expenditure.csv  -> health_expenditure

Merge is on (iso3, year). Output: data/processed/merged_tb_dataset.csv.
"""

import os

import pandas as pd

RAW_DIR = "data/raw"
PROCESSED_DIR = "data/processed"
OUTPUT_PATH = os.path.join(PROCESSED_DIR, "merged_tb_dataset.csv")

WHO_FILE = "who_tb_data_merged.csv"

# filename -> metric column name
OPTIONAL_SOURCES = {
    "bcg_coverage.csv": "bcg_coverage",
    "hiv_prevalence.csv": "hiv_prevalence",
    "gdp_per_capita.csv": "gdp_per_capita",
    "health_expenditure.csv": "health_expenditure",
}

YEAR_MIN, YEAR_MAX = 2000, 2022
VALID_INCOME = {"L", "LM", "UM", "H"}


def load_owid(filename: str, metric: str) -> pd.DataFrame:
    """Load an OWID grapher CSV (Entity, Code, Year, <value>) -> iso3/year/metric."""
    path = os.path.join(RAW_DIR, filename)
    df = pd.read_csv(path)
    rename = {}
    for col in df.columns:
        low = col.lower()
        if low == "code":
            rename[col] = "iso3"
        elif low == "year":
            rename[col] = "year"
    df = df.rename(columns=rename)
    value_cols = [c for c in df.columns if c not in ("Entity", "iso3", "year")]
    if not value_cols:
        raise ValueError(f"No value column found in {filename}")
    df = df.rename(columns={value_cols[0]: metric})
    return df[["iso3", "year", metric]]


def load_who() -> pd.DataFrame:
    """Load the WHO notifications file and derive the modelling columns."""
    path = os.path.join(RAW_DIR, WHO_FILE)
    if not os.path.exists(path):
        raise FileNotFoundError(
            f"Missing {path}. Pull it from the repo into data/raw/."
        )
    df = pd.read_csv(path, low_memory=False)
    df = df[["country", "iso3", "year", "g_whoregion", "c_newinc",
             "population_size", "income_level"]].copy()
    df["tb_incidence"] = df["c_newinc"] / df["population_size"] * 100000.0
    df = df.rename(columns={"g_whoregion": "region", "population_size": "population"})
    return df.drop(columns=["c_newinc"])


def main():
    os.makedirs(PROCESSED_DIR, exist_ok=True)

    merged = load_who()

    present, absent = [], []
    for filename, metric in OPTIONAL_SOURCES.items():
        if os.path.exists(os.path.join(RAW_DIR, filename)):
            merged = merged.merge(load_owid(filename, metric), on=["iso3", "year"],
                                  how="outer")
            present.append(metric)
        else:
            absent.append(metric)

    # Keep real countries within the modelling window.
    merged = merged.dropna(subset=["iso3"])
    merged = merged[merged["iso3"].astype(str).str.len() == 3]
    merged = merged[(merged["year"] >= YEAR_MIN) & (merged["year"] <= YEAR_MAX)]

    # Core requirements: a usable TB target and a valid income band + region.
    merged = merged[merged["tb_incidence"].notna() & (merged["tb_incidence"] > 0)]
    merged = merged[merged["income_level"].isin(VALID_INCOME)]
    merged = merged.dropna(subset=["region"])
    # Require any optional covariate that IS present (so feature rows are complete).
    if present:
        merged = merged.dropna(subset=present)

    base_cols = ["country", "iso3", "year", "tb_incidence", "population",
                 "income_level", "region"]
    final_cols = base_cols + present
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
    print(f"Covariates present: {present if present else '(none — WHO only)'}")
    if absent:
        print(f"Covariates skipped: {absent} (no file in data/raw/)")
    print(f"\nSaved to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
