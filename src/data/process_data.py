"""Build the analysis-ready TB Futures dataset from three source files.

Sources (all in data/raw/):
  who_tb_data_merged.csv  WHO TB notifications — provides c_newinc,
                          population_size, income_level, g_whoregion. We derive
                          tb_incidence = c_newinc / population_size * 100,000.
  bcg_coverage.csv        OWID BCG immunization coverage (Entity, Code, Year, value).
  hiv_prevalence.csv      OWID share of population with HIV (Entity, Code, Year, value).

Merge is on (iso3, year). Output: data/processed/merged_tb_dataset.csv with columns
country, iso3, year, bcg_coverage, tb_incidence, hiv_prevalence, population,
income_level, region.
"""

import os

import pandas as pd

RAW_DIR = "data/raw"
PROCESSED_DIR = "data/processed"
OUTPUT_PATH = os.path.join(PROCESSED_DIR, "merged_tb_dataset.csv")

WHO_FILE = "who_tb_data_merged.csv"
BCG_FILE = "bcg_coverage.csv"
HIV_FILE = "hiv_prevalence.csv"

YEAR_MIN, YEAR_MAX = 2000, 2022
VALID_INCOME = {"L", "LM", "UM", "H"}


def load_owid(filename: str, metric: str) -> pd.DataFrame:
    """Load an OWID grapher CSV (Entity, Code, Year, <value>) -> iso3/year/metric."""
    path = os.path.join(RAW_DIR, filename)
    if not os.path.exists(path):
        raise FileNotFoundError(
            f"Missing {path}. Download it from OWID and place it in data/raw/."
        )
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
    df = df.drop(columns=["c_newinc"])
    return df


def main():
    os.makedirs(PROCESSED_DIR, exist_ok=True)

    who = load_who()
    bcg = load_owid(BCG_FILE, "bcg_coverage")
    hiv = load_owid(HIV_FILE, "hiv_prevalence")

    merged = who.merge(bcg, on=["iso3", "year"], how="outer")
    merged = merged.merge(hiv, on=["iso3", "year"], how="outer")

    # Keep real countries within the modelling window.
    merged = merged.dropna(subset=["iso3"])
    merged = merged[merged["iso3"].astype(str).str.len() == 3]
    merged = merged[(merged["year"] >= YEAR_MIN) & (merged["year"] <= YEAR_MAX)]

    # Require the core modelling columns.
    merged = merged.dropna(subset=["bcg_coverage", "tb_incidence", "income_level"])
    merged = merged[merged["income_level"].isin(VALID_INCOME)]
    merged = merged[merged["tb_incidence"] > 0]

    final_cols = [
        "country", "iso3", "year",
        "bcg_coverage", "tb_incidence", "hiv_prevalence",
        "population", "income_level", "region",
    ]
    for col in final_cols:
        if col not in merged.columns:
            merged[col] = pd.NA
    merged = merged[final_cols].sort_values(["country", "year"]).reset_index(drop=True)

    merged.to_csv(OUTPUT_PATH, index=False)

    print("=" * 60)
    print("Processed dataset summary")
    print("=" * 60)
    print(f"Rows:         {len(merged)}")
    print(f"Countries:    {merged['country'].nunique()}")
    print(f"Year range:   {int(merged['year'].min())}-{int(merged['year'].max())}")
    print(f"Regions:      {sorted(merged['region'].dropna().unique())}")
    print(f"Income bands: {sorted(merged['income_level'].dropna().unique())}")
    print("\nMissing values per column:")
    print(merged.isna().sum().to_string())
    print(f"\nSaved to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
