# API 5 — Background Tasks + JSON Persistence

## What You Will Learn

- Why some work should not block an HTTP response
- How FastAPI's `BackgroundTasks` runs code **after** the response is sent
- How to track job status by polling (`GET /jobs/{id}`)
- How to write results to a JSON file for simple persistence
- Why `threading.Lock()` is needed when background threads share data

---

## Running the API

```bash
uvicorn apis.api5_background.main:app --reload --port 8005
```

---

## Why Background Tasks?

Imagine a user uploads a large file and asks your API to process it. Processing takes 30 seconds. You have two options:

**Option A (bad):** Make the client wait 30 seconds for the response. The HTTP connection stays open. The browser shows a loading spinner. The user might think it crashed.

**Option B (good):** Accept the request immediately, return a job ID, and do the work in the background. The client checks back later with `GET /jobs/{id}` to see if it is done.

Option B is what `BackgroundTasks` enables.

**Analogy:** Dropping off dry cleaning. You hand over your clothes, get a ticket, and leave. You come back later and show the ticket to pick up your clothes. You don't stand at the counter for an hour.

---

## HTTP 202 Accepted

When you create a background job, the server returns **202 Accepted** — not 201 Created, not 200 OK:

```python
@app.post("/jobs", status_code=202)
def create_job(body: JobCreate, background_tasks: BackgroundTasks):
    ...
    background_tasks.add_task(_run_job, job["id"])
    return job   # returns immediately, job still pending
```

202 means: "I received your request and I am working on it — but the work is not done yet."

---

## The Job Lifecycle

Jobs move through states:

```
pending → running → completed
                 ↘ failed
```

- **pending**: created but background task hasn't started yet
- **running**: `_run_job` is executing
- **completed**: work succeeded, `result` is set
- **failed**: an error occurred, `error` is set

The client polls `GET /jobs/{id}` until the status is `completed` or `failed`.

---

## How `BackgroundTasks` Works

```python
from fastapi import BackgroundTasks

@app.post("/jobs", status_code=202)
def create_job(body: JobCreate, background_tasks: BackgroundTasks):
    job = {...}
    _jobs[job["id"]] = job

    # Add the function to run in the background
    # It will run AFTER this function returns the response
    background_tasks.add_task(_run_job, job["id"])

    return job  # ← response sent here, THEN _run_job runs
```

`add_task(function, *args)` schedules the function. FastAPI sends the HTTP response first, then calls the function.

---

## Thread Safety with `threading.Lock()`

The HTTP request handler and the background job run in **different threads** at the same time. They both access `_jobs` — one to read status, the other to write it.

Without a lock, two threads can corrupt data:

```
Thread A reads _jobs[1]: {"status": "running"}
Thread B reads _jobs[1]: {"status": "running"}  ← same moment!
Thread A writes _jobs[1]["status"] = "completed"
Thread B writes _jobs[1]["status"] = "failed"   ← overwrites A!
```

With a lock, only one thread can write at a time:

```python
_lock = threading.Lock()

with _lock:
    _jobs[job_id]["status"] = JobStatus.running
```

The `with _lock:` block is an exclusive section — no other thread can enter until it exits.

---

## JSON File Persistence

When a job completes, its result is saved to `jobs_results.json`. The pattern is:

```python
def _persist_result(job: dict):
    results_file = _RESULTS_FILE
    existing = []
    if results_file.exists():
        with open(results_file, "r") as f:
            existing = json.load(f)    # read current contents
    existing.append(job)               # add new result
    with open(results_file, "w") as f:
        json.dump(existing, f, indent=2)  # write everything back
```

This is simple but not production-ready — it re-reads and re-writes the whole file on every job. For learning purposes it works fine. In production you would use a database.

---

## Code Walkthrough

### Creating a job — `POST /jobs`

```python
@app.post("/jobs", response_model=Job, status_code=202)
def create_job(body: JobCreate, background_tasks: BackgroundTasks):
    global _job_id
    with _lock:
        job = {
            "id": _job_id,
            "name": body.name,
            "status": JobStatus.pending,    # starts as pending
            "input_value": body.input_value,
            "result": None,
            "error": None,
        }
        _jobs[_job_id] = job
        _job_id += 1
    background_tasks.add_task(_run_job, job["id"])
    return job
```

### The background worker — `_run_job()`

```python
def _run_job(job_id: int):
    with _lock:
        _jobs[job_id]["status"] = JobStatus.running   # mark as running
    try:
        time.sleep(0.05)                              # simulate work
        input_value = _jobs[job_id]["input_value"]
        if input_value < 0:
            raise ValueError("input_value must be non-negative")
        result = input_value * 2                      # actual "work"
        with _lock:
            _jobs[job_id]["status"] = JobStatus.completed
            _jobs[job_id]["result"] = result
        _persist_result(_jobs[job_id])                # save to disk
    except Exception as exc:
        with _lock:
            _jobs[job_id]["status"] = JobStatus.failed
            _jobs[job_id]["error"] = str(exc)
```

---

## Testing in Postman

**Step 1:** `POST /jobs` with body `{"name": "my job", "input_value": 7}` → get back job ID, status = "pending"

**Step 2:** `GET /jobs/1` → status = "running" or "completed" (it's fast, so you might catch it running)

**Step 3:** `GET /jobs/1` again → status = "completed", result = 14

**Step 4:** `GET /results` → the completed job appears here (loaded from `jobs_results.json`)

**Step 5:** `POST /jobs` with `"input_value": -5` → job will fail. Check `GET /jobs/{id}` for the error field.
