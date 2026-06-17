"""Build the analysis-ready TB Futures dataset.

Target and features come from the real OWID/WHO data in data/:

  incidence-of-tuberculosis-sdgs.csv ............. tb_incidence (WHO modeled
                                                   estimate per 100k) — TARGET
  bcg-immunization-coverage-for-tb-among-1-year-olds.csv  bcg_coverage
  gdp-per-capita-worldbank.csv ................... gdp_per_capita
  population.csv ................................. population
  sites-...rapid-tuberculosis-diagnostics...csv .. rapid_dx_sites (CONTEXT only;
                                                   sparse 2020-23, not a feature)
  who_tb_data_merged.csv (data/raw or repo root) . income_level, region

Merge is on (iso3, year). A row is kept for modelling only if it has the target,
BCG, GDP, income level, and region. Output: data/processed/merged_tb_dataset.csv.
"""

import os

import pandas as pd

DATA_DIR = "data"
RAW_DIR = "data/raw"
PROCESSED_DIR = "data/processed"
OUTPUT_PATH = os.path.join(PROCESSED_DIR, "merged_tb_dataset.csv")

# OWID grapher file -> canonical column name
OWID_SOURCES = {
    "incidence-of-tuberculosis-sdgs.csv": "tb_incidence",
    "bcg-immunization-coverage-for-tb-among-1-year-olds.csv": "bcg_coverage",
    "gdp-per-capita-worldbank.csv": "gdp_per_capita",
    "population.csv": "population",
    "sites-providing-rapid-tuberculosis-diagnostics-per-million-people.csv": "rapid_dx_sites",
}

WHO_CANDIDATES = [
    os.path.join(RAW_DIR, "who_tb_data_merged.csv"),
    "who_tb_data_merged.csv",
]

YEAR_MIN, YEAR_MAX = 2000, 2023
VALID_INCOME = {"L", "LM", "UM", "H"}
REQUIRED = ["tb_incidence", "bcg_coverage", "gdp_per_capita", "income_level", "region"]


def load_owid(filename: str, metric: str) -> pd.DataFrame:
    """Load an OWID grapher CSV (Entity, Code, Year, <value>[, extra]) -> iso3/year/metric."""
    df = pd.read_csv(os.path.join(DATA_DIR, filename))
    rename = {}
    for col in df.columns:
        low = col.lower()
        if low == "code":
            rename[col] = "iso3"
        elif low == "year":
            rename[col] = "year"
    df = df.rename(columns=rename)
    value_cols = [c for c in df.columns if c not in ("Entity", "iso3", "year")]
    df = df.rename(columns={value_cols[0]: metric})
    out = df[["iso3", "year", metric]].dropna(subset=["iso3"])
    return out[out["iso3"].astype(str).str.len() == 3]


def load_who():
    """WHO notifications file -> (country, iso3, year, income_level, region, who_pop)."""
    path = next((p for p in WHO_CANDIDATES if os.path.exists(p)), None)
    if path is None:
        raise FileNotFoundError(
            "who_tb_data_merged.csv not found in data/raw/ or repo root."
        )
    df = pd.read_csv(path, low_memory=False)
    df = df[["country", "iso3", "year", "g_whoregion", "income_level",
             "population_size"]].copy()
    return df.rename(columns={"g_whoregion": "region", "population_size": "who_pop"})


def main():
    os.makedirs(PROCESSED_DIR, exist_ok=True)

    who = load_who()
    merged = who
    for filename, metric in OWID_SOURCES.items():
        merged = merged.merge(load_owid(filename, metric), on=["iso3", "year"], how="outer")

    merged = merged.dropna(subset=["iso3"])
    merged = merged[merged["iso3"].astype(str).str.len() == 3]
    merged = merged[(merged["year"] >= YEAR_MIN) & (merged["year"] <= YEAR_MAX)]

    # Population: prefer the dedicated OWID series, fall back to the WHO figure.
    merged["population"] = merged["population"].fillna(merged["who_pop"])

    # Valid income band + positive target.
    merged = merged[merged["income_level"].isin(VALID_INCOME)]
    merged = merged[merged["tb_incidence"] > 0]
    merged = merged.dropna(subset=REQUIRED)

    final_cols = ["country", "iso3", "year", "tb_incidence", "bcg_coverage",
                  "gdp_per_capita", "population", "income_level", "region",
                  "rapid_dx_sites"]
    merged = merged[final_cols].sort_values(["country", "year"]).reset_index(drop=True)
    merged.to_csv(OUTPUT_PATH, index=False)

    print("=" * 60)
    print("Processed dataset summary")
    print("=" * 60)
    print(f"Rows:          {len(merged)}")
    print(f"Countries:     {merged['country'].nunique()}")
    print(f"Year range:    {int(merged['year'].min())}-{int(merged['year'].max())}")
    print(f"Regions:       {sorted(merged['region'].dropna().unique())}")
    print(f"Income bands:  {sorted(merged['income_level'].dropna().unique())}")
    print(f"TB incidence:  {merged['tb_incidence'].min():.0f}-{merged['tb_incidence'].max():.0f} /100k")
    print(f"rapid_dx_sites present (context): {merged['rapid_dx_sites'].notna().sum()} rows")
    print(f"\nSaved to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
