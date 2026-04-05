"""
Tests for API 3 - Election Data API

Requirements covered:
  - GET /elections               returns list of records with pagination
  - GET /elections/parties       returns list of party names
  - GET /elections/regions       returns sorted list of region names
  - GET /elections/results       returns all results without filters
  - GET /elections/results?region=... filters by region
  - GET /elections/results?party=...  filters by party
  - GET /elections/results       returns 404 for unknown region
  - GET /elections/results       returns 404 for unknown party
  - GET /elections/summary       returns totals per party
  - GET /elections/zero-votes    returns parties/regions with zero votes
  - GET /elections/region/{name} returns full breakdown for known region
  - GET /elections/region/{name} returns 404 for unknown region
  - Pagination skip/limit works correctly
"""

import pytest
from fastapi.testclient import TestClient
from apis.api3_elections.main import app, load_data, _META_COLS

client = TestClient(app)


# ── GET /elections ────────────────────────────────────────────────────────────

def test_list_elections_status_200():
    response = client.get("/elections")
    assert response.status_code == 200


def test_list_elections_returns_list():
    response = client.get("/elections")
    assert isinstance(response.json(), list)


def test_list_elections_default_limit_50():
    response = client.get("/elections")
    assert len(response.json()) <= 50


def test_list_elections_has_region_name():
    response = client.get("/elections")
    assert "RegioNaam" in response.json()[0]


def test_list_elections_pagination_limit():
    response = client.get("/elections?limit=5")
    assert len(response.json()) == 5


def test_list_elections_pagination_skip():
    all_items = client.get("/elections?limit=355").json()
    skipped = client.get("/elections?skip=10&limit=355").json()
    assert all_items[10]["RegioNaam"] == skipped[0]["RegioNaam"]


# ── GET /elections/parties ────────────────────────────────────────────────────

def test_parties_status_200():
    response = client.get("/elections/parties")
    assert response.status_code == 200


def test_parties_returns_list():
    data = client.get("/elections/parties").json()
    assert "parties" in data
    assert isinstance(data["parties"], list)


def test_parties_contains_vvd():
    data = client.get("/elections/parties").json()
    assert "VVD" in data["parties"]


def test_parties_contains_d66():
    data = client.get("/elections/parties").json()
    assert "D66" in data["parties"]


def test_parties_does_not_contain_meta_columns():
    data = client.get("/elections/parties").json()
    for meta in _META_COLS:
        assert meta not in data["parties"]


# ── GET /elections/regions ────────────────────────────────────────────────────

def test_regions_status_200():
    response = client.get("/elections/regions")
    assert response.status_code == 200


def test_regions_returns_list():
    data = client.get("/elections/regions").json()
    assert "regions" in data
    assert isinstance(data["regions"], list)


def test_regions_is_sorted():
    data = client.get("/elections/regions").json()
    regions = data["regions"]
    assert regions == sorted(regions)


def test_regions_total_count():
    data = client.get("/elections/regions").json()
    assert len(data["regions"]) == 355


# ── GET /elections/results ────────────────────────────────────────────────────

def test_results_no_filter_status_200():
    response = client.get("/elections/results")
    assert response.status_code == 200


def test_results_filter_by_known_region():
    response = client.get("/elections/results?region=Aalsmeer")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["RegioNaam"] == "Aalsmeer"


def test_results_filter_by_region_case_insensitive():
    response = client.get("/elections/results?region=aalsmeer")
    assert response.status_code == 200
    assert len(response.json()) == 1


def test_results_filter_by_unknown_region_returns_404():
    response = client.get("/elections/results?region=MadeUpCity")
    assert response.status_code == 404


def test_results_filter_by_party_vvd():
    response = client.get("/elections/results?party=VVD")
    assert response.status_code == 200
    data = response.json()
    assert "VVD" in data[0]


def test_results_filter_by_unknown_party_returns_404():
    response = client.get("/elections/results?party=FakeParty")
    assert response.status_code == 404


def test_results_filter_region_and_party():
    response = client.get("/elections/results?region=Aalsmeer&party=VVD")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert "VVD" in data[0]


# ── GET /elections/summary ────────────────────────────────────────────────────

def test_summary_status_200():
    response = client.get("/elections/summary")
    assert response.status_code == 200


def test_summary_contains_totals():
    data = client.get("/elections/summary").json()
    assert "totals" in data


def test_summary_vvd_is_positive():
    data = client.get("/elections/summary").json()
    assert data["totals"]["VVD"] > 0


def test_summary_totals_are_ints():
    data = client.get("/elections/summary").json()
    for v in data["totals"].values():
        assert isinstance(v, int)


# ── GET /elections/zero-votes ─────────────────────────────────────────────────

def test_zero_votes_status_200():
    response = client.get("/elections/zero-votes")
    assert response.status_code == 200


def test_zero_votes_has_count_and_data():
    data = client.get("/elections/zero-votes").json()
    assert "count" in data
    assert "data" in data


def test_zero_votes_count_matches_data_length():
    data = client.get("/elections/zero-votes").json()
    assert data["count"] == len(data["data"])


def test_zero_votes_each_entry_has_party_and_regions():
    data = client.get("/elections/zero-votes").json()
    for entry in data["data"]:
        assert "party" in entry
        assert "regions_with_zero_votes" in entry


# ── GET /elections/region/{region_name} ───────────────────────────────────────

def test_region_detail_status_200():
    response = client.get("/elections/region/Aalsmeer")
    assert response.status_code == 200


def test_region_detail_contains_vvd():
    data = client.get("/elections/region/Aalsmeer").json()
    assert "VVD" in data


def test_region_detail_region_name_correct():
    data = client.get("/elections/region/Aalsmeer").json()
    assert data["RegioNaam"] == "Aalsmeer"


def test_region_detail_case_insensitive():
    response = client.get("/elections/region/aalsmeer")
    assert response.status_code == 200


def test_region_detail_unknown_returns_404():
    response = client.get("/elections/region/NonExistentCity")
    assert response.status_code == 404
