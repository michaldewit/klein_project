# Exercises — API 5: Background Tasks

Run the API while working: `uvicorn apis.api5_background.main:app --reload --port 8005`

---

## Exercise 1 (Easy) — Add a `label` field

**Task:** Add an optional `label: str = ""` field to `JobCreate`. This label should be stored in the job and appear in the response. It is just a user-friendly name for the job.

**Files to edit:** `apis/api5_background/main.py`

**Hint:** Add `label` to `JobCreate`, and include it in the job dict inside `create_job`.

<details>
<summary>Answer</summary>

```python
class JobCreate(BaseModel):
    name: str = Field(..., min_length=1)
    input_value: int
    label: str = ""                  # ← add this

class Job(BaseModel):
    id: int
    name: str
    status: JobStatus
    input_value: int
    result: Optional[int] = None
    error: Optional[str] = None
    label: str = ""                  # ← add this

# In create_job:
job = {
    "id": _job_id,
    "name": body.name,
    "status": JobStatus.pending,
    "input_value": body.input_value,
    "label": body.label,             # ← add this
    "result": None,
    "error": None,
}
```

**Test it:** `POST /jobs` with `{"name": "test", "input_value": 5, "label": "my first job"}` and check the response.

</details>

---

## Exercise 2 (Medium) — Filter jobs by status

**Task:** Add a `?status=` query parameter to `GET /jobs` that filters results. For example, `GET /jobs?status=completed` returns only completed jobs.

**Hint:** Add `status: Optional[str] = Query(default=None)` and filter `_jobs.values()` before returning.

<details>
<summary>Answer</summary>

```python
@app.get("/jobs", response_model=list[Job], summary="List all jobs")
def list_jobs(status: Optional[str] = Query(default=None)):
    jobs = list(_jobs.values())
    if status is not None:
        jobs = [j for j in jobs if j["status"] == status]
    return jobs
```

**Test it:**
- `GET /jobs?status=pending` — shows jobs not yet started
- `GET /jobs?status=completed` — shows finished jobs
- `GET /jobs?status=failed` — shows failed jobs

</details>

---

## Exercise 3 (Medium) — Retry on failure

**Task:** Add a `retry: bool = True` field to `JobCreate`. When a job fails AND `retry=True`, the job should automatically try once more before marking as `failed`.

**Hint:** Wrap the main logic in `_run_job` in a loop that runs at most twice. Track attempt count. Only set status to `failed` after all attempts are exhausted.

<details>
<summary>Answer</summary>

```python
class JobCreate(BaseModel):
    name: str = Field(..., min_length=1)
    input_value: int
    retry: bool = True               # ← add this

# In create_job, store retry in the job dict:
job = {
    ...
    "retry": body.retry,
}

# Update _run_job:
def _run_job(job_id: int):
    with _lock:
        if job_id not in _jobs:
            return
        _jobs[job_id]["status"] = JobStatus.running

    max_attempts = 2 if _jobs[job_id].get("retry", True) else 1
    last_error = None

    for attempt in range(max_attempts):
        try:
            time.sleep(0.05)
            input_value = _jobs[job_id]["input_value"]
            if input_value < 0:
                raise ValueError("input_value must be non-negative")
            result = input_value * 2
            with _lock:
                _jobs[job_id]["status"] = JobStatus.completed
                _jobs[job_id]["result"] = result
            _persist_result(_jobs[job_id])
            return   # success — stop retrying
        except Exception as exc:
            last_error = str(exc)

    with _lock:
        _jobs[job_id]["status"] = JobStatus.failed
        _jobs[job_id]["error"] = last_error
```

**Note:** In this specific job, every negative input will always fail — the retry just runs the same failing logic twice. This exercise teaches the pattern; in real jobs, transient failures (network timeouts, etc.) are worth retrying.

</details>

---

## Exercise 4 (Hard) — Bulk delete non-running jobs

**Task:** Add `DELETE /jobs` (no ID) that removes all jobs whose status is `pending`, `completed`, or `failed` — but NOT `running` jobs (you can't cancel work in progress). Return the count of deleted jobs.

Expected response: `{"deleted": 3}`

**Hint:** Iterate over `_jobs`, collect IDs to delete, then delete them. Use the lock.

<details>
<summary>Answer</summary>

```python
@app.delete("/jobs", summary="Remove all non-running jobs")
def bulk_delete_jobs():
    with _lock:
        to_delete = [
            job_id
            for job_id, job in _jobs.items()
            if job["status"] != JobStatus.running
        ]
        for job_id in to_delete:
            del _jobs[job_id]
    return {"deleted": len(to_delete)}
```

**Test it:**
1. Create 3 jobs and wait for them to complete
2. `DELETE /jobs` → `{"deleted": 3}`
3. `GET /jobs` → empty list
4. Create a job and call `DELETE /jobs` while it is running → that job should NOT be deleted

</details>
