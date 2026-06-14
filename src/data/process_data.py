"""Clean, merge, and feature-engineer the raw TB Futures datasets.

Reads the six raw OWID CSVs from data/raw/, harmonises them onto
(country, iso3, year), attaches a WHO region, and writes a single
analysis-ready table to data/processed/merged_tb_dataset.csv.
"""

import os

import pandas as pd

from src.data.who_regions import get_region

RAW_DIR = "data/raw"
PROCESSED_DIR = "data/processed"
OUTPUT_PATH = os.path.join(PROCESSED_DIR, "merged_tb_dataset.csv")

# raw filename -> canonical metric column name
DATASETS = {
    "bcg_coverage.csv": "bcg_coverage",
    "tb_incidence.csv": "tb_incidence",
    "hiv_prevalence.csv": "hiv_prevalence",
    "gdp_per_capita.csv": "gdp_per_capita",
    "health_expenditure.csv": "health_expenditure",
    "population.csv": "population",
}

KEY_COLS = ["country", "iso3", "year"]
# columns that must be present for a row to be usable
REQUIRED_NON_NULL = ["bcg_coverage", "tb_incidence"]
YEAR_MIN, YEAR_MAX = 2000, 2022


def load_one(filename: str, metric: str) -> pd.DataFrame:
    """Load a single OWID grapher CSV and standardise its columns.

    OWID grapher CSVs come as: Entity, Code, Year, <value column>. We map the
    first three to country/iso3/year and the first remaining numeric column to
    the metric name.
    """
    path = os.path.join(RAW_DIR, filename)
    if not os.path.exists(path):
        raise FileNotFoundError(
            f"Missing {path}. Run `python src/data/download_data.py` first."
        )

    df = pd.read_csv(path)

    rename = {}
    for col in df.columns:
        low = col.lower()
        if low == "entity":
            rename[col] = "country"
        elif low == "code":
            rename[col] = "iso3"
        elif low == "year":
            rename[col] = "year"
    df = df.rename(columns=rename)

    value_cols = [c for c in df.columns if c not in ("country", "iso3", "year")]
    if not value_cols:
        raise ValueError(f"No value column found in {filename}")
    # First non-key column holds the metric of interest.
    df = df.rename(columns={value_cols[0]: metric})

    keep = ["country", "iso3", "year", metric]
    df = df[[c for c in keep if c in df.columns]]
    return df


def main():
    os.makedirs(PROCESSED_DIR, exist_ok=True)

    merged = None
    for filename, metric in DATASETS.items():
        df = load_one(filename, metric)
        if merged is None:
            merged = df
        else:
            merged = merged.merge(df, on=KEY_COLS, how="outer")

    # Drop aggregates / rows without an ISO3 code (regions, "World", etc.).
    merged = merged.dropna(subset=["iso3"])
    merged = merged[merged["iso3"].str.len() == 3]

    # Restrict to the modelling window.
    merged = merged[(merged["year"] >= YEAR_MIN) & (merged["year"] <= YEAR_MAX)]

    # Require the core modelling columns.
    merged = merged.dropna(subset=REQUIRED_NON_NULL)

    # Attach WHO region.
    merged["region"] = merged["iso3"].apply(get_region)
    merged = merged[merged["region"] != "OTHER"]

    final_cols = [
        "country", "iso3", "year",
        "bcg_coverage", "tb_incidence", "gdp_per_capita",
        "health_expenditure", "hiv_prevalence", "population", "region",
    ]
    for col in final_cols:
        if col not in merged.columns:
            merged[col] = pd.NA
    merged = merged[final_cols].sort_values(["country", "year"]).reset_index(drop=True)

    merged.to_csv(OUTPUT_PATH, index=False)

    # Summary.
    print("=" * 60)
    print("Processed dataset summary")
    print("=" * 60)
    print(f"Rows:        {len(merged)}")
    print(f"Countries:   {merged['country'].nunique()}")
    print(f"Year range:  {int(merged['year'].min())}-{int(merged['year'].max())}")
    print(f"Regions:     {sorted(merged['region'].unique())}")
    print("\nMissing values per column:")
    print(merged.isna().sum().to_string())
    print(f"\nSaved to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
