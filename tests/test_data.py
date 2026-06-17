"""Tests for the processed dataset."""

import os

import pandas as pd
import pytest

DATA_PATH = "data/processed/merged_tb_dataset.csv"

pytestmark = pytest.mark.skipif(
    not os.path.exists(DATA_PATH),
    reason="Processed dataset not built. Run download_data.py + process_data.py.",
)

# Columns that are always present (covariate columns are optional/data-adaptive).
CORE_COLUMNS = {"country", "iso3", "year", "tb_incidence", "population",
                "income_level", "region"}


@pytest.fixture(scope="module")
def df():
    return pd.read_csv(DATA_PATH)


def test_has_core_columns(df):
    assert CORE_COLUMNS.issubset(set(df.columns))


def test_year_range(df):
    assert df["year"].min() >= 2000
    assert df["year"].max() <= 2023


def test_tb_positive(df):
    assert (df["tb_incidence"] > 0).all()


def test_no_nulls_in_tb_target(df):
    assert df["tb_incidence"].notna().all()


def test_income_level_valid(df):
    assert set(df["income_level"].unique()).issubset({"L", "LM", "UM", "H"})


def test_bcg_in_range_if_present(df):
    if "bcg_coverage" in df.columns:
        assert df["bcg_coverage"].min() >= 0
        assert df["bcg_coverage"].max() <= 100
        assert df["bcg_coverage"].notna().all()
