"""Tests for the FastAPI backend."""

import os

import pytest
from fastapi.testclient import TestClient

DATA_PATH = "data/processed/merged_tb_dataset.csv"
MODEL_PATH = "models/rf_model.pkl"

pytestmark = pytest.mark.skipif(
    not (os.path.exists(DATA_PATH) and os.path.exists(MODEL_PATH)),
    reason="Model/data artifacts not built. Run the data + train pipeline first.",
)

SCENARIOS = ["baseline", "vaccine_push", "hiv_control", "health_boost", "combined"]


@pytest.fixture(scope="module")
def client():
    from src.api.main import app

    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="module")
def a_country(client):
    return client.get("/countries").json()[0]


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_countries_non_empty(client):
    r = client.get("/countries")
    assert r.status_code == 200
    assert isinstance(r.json(), list)
    assert len(r.json()) > 0


def test_map_data_has_iso3(client):
    r = client.get("/map-data")
    assert r.status_code == 200
    data = r.json()
    assert len(data) > 0
    assert "iso3" in data[0]


def test_simulate_valid(client, a_country):
    r = client.post("/simulate", json={"country": a_country, "scenario": "vaccine_push"})
    assert r.status_code == 200
    assert "predicted_tb_incidence" in r.json()


def test_simulate_all_scenarios(client, a_country):
    for scenario in SCENARIOS:
        r = client.post("/simulate", json={"country": a_country, "scenario": scenario})
        assert r.status_code == 200


def test_simulate_unknown_country(client):
    r = client.post(
        "/simulate", json={"country": "Atlantis", "scenario": "baseline"}
    )
    assert r.status_code == 422
