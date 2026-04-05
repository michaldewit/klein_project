"""
Tests for API 5 - Background Tasks + JSON Persistence

Requirements covered:
  - POST /jobs          returns 202 with job id and pending status
  - POST /jobs          validates name is not empty
  - GET  /jobs          returns empty list initially
  - GET  /jobs          lists created jobs
  - GET  /jobs/{id}     returns correct job
  - GET  /jobs/{id}     returns 404 for unknown id
  - Background task     job transitions from pending -> completed
  - Background task     completed job result = input * 2
  - Background task     negative input causes failed status
  - DELETE /jobs/{id}   returns 204 for pending/completed job
  - DELETE /jobs/{id}   returns 404 for unknown id
  - GET  /results       returns empty list when no file exists
  - GET  /results       returns completed results after jobs finish
  - Persistence         results are written to JSON file on disk
"""

import time
import json
import pytest
from pathlib import Path
from fastapi.testclient import TestClient
from apis.api5_background.main import app, _reset, _RESULTS_FILE, JobStatus

# Use a separate test results file so we don't pollute the real one
_TEST_RESULTS_FILE = Path(__file__).parent / "test_jobs_results.json"

client = TestClient(app)


@pytest.fixture(autouse=True)
def reset_state(monkeypatch):
    """Reset job store and use a temp results file for each test."""
    import apis.api5_background.main as m
    monkeypatch.setattr(m, "_RESULTS_FILE", _TEST_RESULTS_FILE)
    _reset(results_file=_TEST_RESULTS_FILE)
    yield
    _reset(results_file=_TEST_RESULTS_FILE)


def wait_for_job(job_id: int, timeout: float = 2.0) -> dict:
    """Poll until job reaches a terminal state."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        data = client.get(f"/jobs/{job_id}").json()
        if data["status"] in (JobStatus.completed, JobStatus.failed):
            return data
        time.sleep(0.05)
    return client.get(f"/jobs/{job_id}").json()


# ── POST /jobs ────────────────────────────────────────────────────────────────

def test_create_job_returns_202():
    response = client.post("/jobs", json={"name": "test", "input_value": 5})
    assert response.status_code == 202


def test_create_job_returns_id():
    response = client.post("/jobs", json={"name": "test", "input_value": 5})
    assert "id" in response.json()


def test_create_job_initial_status_pending():
    response = client.post("/jobs", json={"name": "test", "input_value": 5})
    assert response.json()["status"] in ("pending", "running")


def test_create_job_empty_name_returns_422():
    response = client.post("/jobs", json={"name": "", "input_value": 5})
    assert response.status_code == 422


def test_create_job_missing_input_returns_422():
    response = client.post("/jobs", json={"name": "test"})
    assert response.status_code == 422


# ── GET /jobs ─────────────────────────────────────────────────────────────────

def test_list_jobs_initially_empty():
    assert client.get("/jobs").json() == []


def test_list_jobs_after_create():
    client.post("/jobs", json={"name": "j1", "input_value": 1})
    client.post("/jobs", json={"name": "j2", "input_value": 2})
    assert len(client.get("/jobs").json()) == 2


# ── GET /jobs/{id} ────────────────────────────────────────────────────────────

def test_get_job_returns_correct_data():
    job = client.post("/jobs", json={"name": "myjob", "input_value": 10}).json()
    response = client.get(f"/jobs/{job['id']}")
    assert response.status_code == 200
    assert response.json()["name"] == "myjob"


def test_get_job_not_found_returns_404():
    assert client.get("/jobs/9999").status_code == 404


# ── Background task completion ────────────────────────────────────────────────

def test_job_completes_successfully():
    job = client.post("/jobs", json={"name": "double", "input_value": 7}).json()
    completed = wait_for_job(job["id"])
    assert completed["status"] == "completed"


def test_job_result_doubles_input():
    job = client.post("/jobs", json={"name": "double", "input_value": 6}).json()
    completed = wait_for_job(job["id"])
    assert completed["result"] == 12


def test_job_with_zero_input():
    job = client.post("/jobs", json={"name": "zero", "input_value": 0}).json()
    completed = wait_for_job(job["id"])
    assert completed["result"] == 0


def test_job_negative_input_fails():
    job = client.post("/jobs", json={"name": "bad", "input_value": -1}).json()
    completed = wait_for_job(job["id"])
    assert completed["status"] == "failed"
    assert completed["error"] is not None


# ── DELETE /jobs/{id} ─────────────────────────────────────────────────────────

def test_delete_job_returns_204():
    job = client.post("/jobs", json={"name": "del", "input_value": 1}).json()
    completed = wait_for_job(job["id"])
    response = client.delete(f"/jobs/{completed['id']}")
    assert response.status_code == 204


def test_delete_job_removes_from_list():
    job = client.post("/jobs", json={"name": "del", "input_value": 1}).json()
    completed = wait_for_job(job["id"])
    client.delete(f"/jobs/{completed['id']}")
    assert client.get("/jobs").json() == []


def test_delete_job_not_found_returns_404():
    assert client.delete("/jobs/9999").status_code == 404


# ── GET /results ──────────────────────────────────────────────────────────────

def test_results_empty_when_no_file():
    data = client.get("/results").json()
    assert data["results"] == []


def test_results_populated_after_job_completes():
    import apis.api5_background.main as m
    job = client.post("/jobs", json={"name": "persist", "input_value": 4}).json()
    wait_for_job(job["id"])
    # Read directly from the test file
    assert _TEST_RESULTS_FILE.exists()
    with open(_TEST_RESULTS_FILE) as f:
        saved = json.load(f)
    assert len(saved) >= 1
    assert saved[0]["result"] == 8


def test_results_multiple_jobs_all_saved():
    job1 = client.post("/jobs", json={"name": "j1", "input_value": 2}).json()
    job2 = client.post("/jobs", json={"name": "j2", "input_value": 3}).json()
    wait_for_job(job1["id"])
    wait_for_job(job2["id"])
    with open(_TEST_RESULTS_FILE) as f:
        saved = json.load(f)
    assert len(saved) == 2
