"""
API 5 - Background Tasks + JSON Persistence
Goal: Learn async background tasks, job tracking, and saving data to disk as JSON.

How it works:
  - POST /jobs        starts a background job (simulates processing)
  - GET  /jobs        lists all jobs and their statuses
  - GET  /jobs/{id}   polls the status of a single job
  - GET  /results     lists all completed job results loaded from jobs.json
  - DELETE /jobs/{id} cancels/removes a pending or failed job

Job lifecycle: pending -> running -> completed | failed

Persistence: completed job results are appended to jobs_results.json on disk.
"""

import json
import time
import threading
from pathlib import Path
from typing import Optional
from enum import Enum

from fastapi import FastAPI, BackgroundTasks, HTTPException
from pydantic import BaseModel, Field

app = FastAPI(
    title="API 5 - Background Tasks",
    description="Learn async background jobs, status polling, and JSON file persistence.",
    version="1.0.0",
)

# ── Config ─────────────────────────────────────────────────────────────────────

_RESULTS_FILE = Path(__file__).parent / "jobs_results.json"

# In-memory job store
_jobs: dict[int, dict] = {}
_job_id: int = 1
_lock = threading.Lock()


def _reset(results_file: Optional[Path] = None):
    """Reset state (used in tests)."""
    global _jobs, _job_id
    _jobs = {}
    _job_id = 1
    path = results_file or _RESULTS_FILE
    if path.exists():
        path.unlink()


# ── Models ────────────────────────────────────────────────────────────────────

class JobStatus(str, Enum):
    pending = "pending"
    running = "running"
    completed = "completed"
    failed = "failed"


class JobCreate(BaseModel):
    name: str = Field(..., min_length=1, description="A label for this job")
    input_value: int = Field(..., description="An integer to process (will be doubled)")


class Job(BaseModel):
    id: int
    name: str
    status: JobStatus
    input_value: int
    result: Optional[int] = None
    error: Optional[str] = None


# ── Background worker ─────────────────────────────────────────────────────────

def _run_job(job_id: int):
    """Simulate work: double the input value. Saves result to JSON on completion."""
    with _lock:
        if job_id not in _jobs:
            return
        _jobs[job_id]["status"] = JobStatus.running

    try:
        # Simulate processing time
        time.sleep(0.05)
        input_value = _jobs[job_id]["input_value"]

        if input_value < 0:
            raise ValueError("input_value must be non-negative")

        result = input_value * 2

        with _lock:
            _jobs[job_id]["status"] = JobStatus.completed
            _jobs[job_id]["result"] = result

        # Persist result to JSON file (reads _RESULTS_FILE at call time)
        _persist_result(_jobs[job_id])

    except Exception as exc:
        with _lock:
            _jobs[job_id]["status"] = JobStatus.failed
            _jobs[job_id]["error"] = str(exc)


def _persist_result(job: dict):
    """Append job result to the JSON results file (uses module-level _RESULTS_FILE)."""
    import apis.api5_background.main as _self
    results_file = _self._RESULTS_FILE
    existing: list = []
    if results_file.exists():
        with open(results_file, "r") as f:
            existing = json.load(f)
    existing.append(job)
    with open(results_file, "w") as f:
        json.dump(existing, f, indent=2)


# ── Endpoints ─────────────────────────────────────────────────────────────────

@app.post("/jobs", response_model=Job, status_code=202, summary="Start a background job")
def create_job(body: JobCreate, background_tasks: BackgroundTasks):
    global _job_id
    with _lock:
        job = {
            "id": _job_id,
            "name": body.name,
            "status": JobStatus.pending,
            "input_value": body.input_value,
            "result": None,
            "error": None,
        }
        _jobs[_job_id] = job
        _job_id += 1

    background_tasks.add_task(_run_job, job["id"])
    return job


@app.get("/jobs", response_model=list[Job], summary="List all jobs")
def list_jobs():
    return list(_jobs.values())


@app.get("/jobs/{job_id}", response_model=Job, summary="Get job status")
def get_job(job_id: int):
    if job_id not in _jobs:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
    return _jobs[job_id]


@app.delete("/jobs/{job_id}", status_code=204, summary="Remove a job")
def delete_job(job_id: int):
    if job_id not in _jobs:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
    if _jobs[job_id]["status"] == JobStatus.running:
        raise HTTPException(status_code=409, detail="Cannot delete a running job")
    del _jobs[job_id]


@app.get("/results", summary="List completed results from disk")
def list_results():
    import apis.api5_background.main as _self
    results_file = _self._RESULTS_FILE
    if not results_file.exists():
        return {"results": []}
    with open(results_file, "r") as f:
        data = json.load(f)
    return {"results": data}
