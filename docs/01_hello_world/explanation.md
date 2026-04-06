# API 1 — Hello World

Welcome to your first FastAPI endpoint! This API is deliberately small so you can focus on the core building blocks every API uses: routes, parameters, and JSON bodies. By the end of this page you will understand exactly how a browser (or Postman) talks to your server and how FastAPI turns a plain Python function into a working web endpoint.

---

## What You Will Learn

- How FastAPI maps a URL like `/hello/Alice` to a Python function using **decorators**
- The difference between **path parameters** (`/hello/{name}`) and **query parameters** (`?lang=nl`)
- How to accept a **JSON request body** using a Pydantic model and why that is safer than reading raw text

---

## Routes: How FastAPI Maps URLs to Functions

Every time someone visits a URL on your server, FastAPI needs to know which Python function should handle that request. You tell FastAPI by placing a **decorator** directly above your function.

```python
@app.get("/")
def root():
    return {"message": "Welcome to API 1 - Hello World!"}
```

Break this down piece by piece:

| Part | Meaning |
|---|---|
| `app` | The FastAPI application object you created with `app = FastAPI(...)` |
| `.get` | The **HTTP method** — GET means "please give me some data" |
| `"/"` | The **path** — the part of the URL after the domain name |

When someone sends a GET request to `http://localhost:8000/`, FastAPI runs `root()` and sends back whatever the function returns as JSON.

> **Tip — The free interactive docs:** FastAPI automatically builds a web UI from your decorators. Start your server and open `http://localhost:8000/docs` in a browser. You can call every endpoint from there without writing a single line of client code. This is one of FastAPI's biggest advantages for learning.

---

## Path Parameters

A **path parameter** is a variable embedded directly inside the URL. You mark it with curly braces in the route string, and FastAPI passes the value as a function argument.

```python
@app.get("/hello/{name}")
def hello(name: str, ...):
    ...
```

If someone requests `/hello/Alice`, FastAPI extracts `"Alice"` from the URL and passes it to `hello()` as `name="Alice"`. The type annotation `str` is not just documentation — FastAPI uses it to validate the value before your function is called. If you wrote `name: int` and the URL contained `/hello/Alice`, FastAPI would return a 422 error automatically, with no code from you.

**Example request and response:**

```
GET /hello/Alice
```

```json
{
  "message": "Hello, Alice!",
  "name": "Alice",
  "lang": "en"
}
```

---

## Query Parameters

A **query parameter** is the part of the URL that comes after a `?`. You can have multiple ones, separated by `&`.

```
GET /hello/Alice?lang=nl
GET /hello/Alice?lang=nl&someOtherParam=123
```

In FastAPI you declare query parameters in the function signature, but you import `Query` to add extra rules like a default value or a description:

```python
from fastapi import Query

@app.get("/hello/{name}")
def hello(
    name: str,
    lang: str = Query(default="en", description="Language: 'en' or 'nl'"),
):
    ...
```

Key points:

- `default="en"` means the parameter is **optional** — if the caller does not include `?lang=...`, FastAPI uses `"en"` automatically.
- If you want a query parameter to be **required**, either remove the `default` entirely, or use `Query(...)` where `...` is Python's way of saying "no default, this is mandatory".
- The `description` shows up in `/docs`, making your API self-documenting.

Inside the function, the greetings dictionary does the language lookup:

```python
greetings = {
    "en": f"Hello, {name}!",
    "nl": f"Hallo, {name}!",
}
message = greetings.get(lang, greetings["en"])  # fall back to English
```

If an unknown language is passed (e.g. `?lang=zz`), `.get(lang, greetings["en"])` silently falls back to English. This is a deliberate design choice — you could also raise an HTTP error instead (you will practice that in later APIs).

---

## POST with a JSON Body

GET requests carry data in the URL. POST requests carry data in the **request body** — a chunk of JSON sent alongside the request. This is the standard approach when you are creating or submitting something.

FastAPI uses **Pydantic models** to describe the shape of the expected body:

```python
from pydantic import BaseModel
from typing import Any

class EchoBody(BaseModel):
    data: dict[str, Any]
```

`BaseModel` is the base class from the Pydantic library. Any class that inherits from it automatically:

1. **Parses** the incoming JSON into Python objects
2. **Validates** the data (wrong types → 422 Unprocessable Entity, automatically)
3. **Documents** the expected shape in `/docs`

Your function just declares `body: EchoBody` as a parameter and FastAPI does the rest:

```python
@app.post("/echo")
def echo(body: EchoBody):
    return {
        "echoed": body.data,
        "keys_received": list(body.data.keys()),
        "count": len(body.data),
    }
```

You never write JSON parsing code. If the client sends `{"data": {"city": "Amsterdam", "pop": 900000}}`, then `body.data` is already a Python dict `{"city": "Amsterdam", "pop": 900000}`.

---

## Code Walkthrough

Here is the complete `main.py` with explanations for every line:

```python
"""
API 1 - Hello World REST API
Goal: Learn routes, HTTP methods, path/query params, request body, JSON responses.
"""

# FastAPI is the web framework. Query lets us add rules to query parameters.
from fastapi import FastAPI, Query
# BaseModel is the base class for all request/response body schemas.
from pydantic import BaseModel
# Any means "any Python type is acceptable here".
from typing import Any

# Create the application. title and description appear in /docs.
app = FastAPI(
    title="API 1 - Hello World",
    description="Learn the basics of REST: routes, methods, params, and JSON bodies.",
    version="1.0.0",
)


# ── Request body schema ───────────────────────────────────────────────────────

class EchoBody(BaseModel):
    # 'data' must be a JSON object (Python dict). Values can be any type.
    data: dict[str, Any]


# ── Endpoint 1: GET / ─────────────────────────────────────────────────────────

@app.get("/", summary="Welcome message")   # summary shows up in /docs
def root():
    """Returns a welcome message."""
    # Returning a plain dict → FastAPI serialises it to JSON automatically.
    return {"message": "Welcome to API 1 - Hello World!"}


# ── Endpoint 2: GET /hello/{name} ─────────────────────────────────────────────

@app.get("/hello/{name}", summary="Personalized greeting")
def hello(
    name: str,                                           # path parameter
    lang: str = Query(default="en",                      # query parameter, optional
                      description="Language: 'en' or 'nl'"),
):
    greetings = {
        "en": f"Hello, {name}!",
        "nl": f"Hallo, {name}!",
    }
    # .get(key, default) returns the default when key is not in the dict.
    message = greetings.get(lang, greetings["en"])
    # Return multiple fields — FastAPI wraps them in a JSON object.
    return {"message": message, "name": name, "lang": lang}


# ── Endpoint 3: POST /echo ────────────────────────────────────────────────────

@app.post("/echo", summary="Echo JSON body", status_code=200)
def echo(body: EchoBody):
    """Receives a JSON body and echoes it back with some metadata."""
    return {
        "echoed": body.data,                      # the original dict
        "keys_received": list(body.data.keys()),  # just the key names
        "count": len(body.data),                  # how many keys
    }
```

---

## Testing in Postman

The steps below assume your server is running. Start it with:

```bash
uvicorn main:app --reload
```

### Test 1 — GET /

1. Open Postman and create a new request.
2. Set the method to **GET**.
3. Enter the URL: `http://localhost:8000/`
4. Click **Send**.
5. You should see:
   ```json
   {"message": "Welcome to API 1 - Hello World!"}
   ```

### Test 2 — GET /hello/Alice?lang=nl

1. Set the method to **GET**.
2. Enter the URL: `http://localhost:8000/hello/Alice`
3. Open the **Params** tab and add a key `lang` with value `nl`.
   Postman will build the URL `http://localhost:8000/hello/Alice?lang=nl` for you.
4. Click **Send**.
5. You should see:
   ```json
   {"message": "Hallo, Alice!", "name": "Alice", "lang": "nl"}
   ```

### Test 3 — POST /echo

1. Set the method to **POST**.
2. Enter the URL: `http://localhost:8000/echo`
3. Open the **Body** tab, select **raw**, and choose **JSON** from the dropdown on the right.
4. Paste this body:
   ```json
   {
     "data": {
       "city": "Amsterdam",
       "population": 900000,
       "country": "Netherlands"
     }
   }
   ```
5. Click **Send**.
6. You should see:
   ```json
   {
     "echoed": {"city": "Amsterdam", "population": 900000, "country": "Netherlands"},
     "keys_received": ["city", "population", "country"],
     "count": 3
   }
   ```

> **What happens if you send bad data?** Try removing the `"data"` key and sending `{"city": "Amsterdam"}` directly. FastAPI will return a **422 Unprocessable Entity** response with a clear explanation of what was wrong — you did not write a single line of validation code.
