# API 4 — API Key Authentication

---

## 1. What You Will Learn

By the end of this guide you will understand:

- What authentication and authorization mean, and why every real API needs them
- How an API key travels inside an HTTP header
- How FastAPI's `Depends()` system chains together reusable security checks
- The difference between a **reader** and an **admin** role
- When to return **401 Unauthorized** versus **403 Forbidden**
- The difference between public and protected routes

---

## 2. Why Authentication?

Imagine a large office building. The lobby is open to anyone — delivery drivers, visitors, and employees can all walk in. But the server room? That needs a keycard. And the executive floor? Only certain employees' keycards open that door.

An API works exactly the same way:

- **Authentication** answers: *Who are you?* — Does this keycard exist?
- **Authorization** answers: *What are you allowed to do?* — Does this keycard open *this* door?

Without any authentication, your API is an unlocked building. Anyone on the internet could read your data, modify records, or delete everything. API keys are one of the simplest ways to add a lock.

---

## 3. API Keys: A Shared Secret in a Header

An API key is just a long, hard-to-guess string that the server and the client both know. The client sends it with every request inside an **HTTP header**.

This API uses the header `X-API-Key`. Here is what a real request looks like:

```
GET /protected/data HTTP/1.1
Host: localhost:8000
X-API-Key: reader-key-123
```

The `X-` prefix is a convention for custom headers. The server reads that header value, looks it up in its list of known keys, and decides what to do next.

**Why not use a query parameter like `/data?api_key=reader-key-123`?**

Query parameters show up in browser history, server logs, and URLs that get copy-pasted. Headers are not shown in URLs, so they are harder to accidentally leak.

**Why not suitable for browsers?**

Standard browser JavaScript (via `fetch` or `XMLHttpRequest`) can send headers, but it cannot do so from a plain `<a>` link or `<form>` tag. API keys work best for server-to-server communication, command-line tools, and Postman. If you are building a browser app for regular users, you would typically use session cookies or OAuth instead — those are covered in later APIs.

---

## 4. FastAPI's `Depends()` System

FastAPI has a feature called **dependency injection**. It lets you declare that one function depends on the result of another function. FastAPI calls those dependencies for you automatically, before calling your route handler.

In plain English: instead of copy-pasting the same "check the API key" code into every single route, you write it once as a dependency and declare that your routes need it.

Here is how the chain looks in this API:

```
Incoming request
       │
       ▼
  get_api_key()
  ─ Reads the X-API-Key header
  ─ Returns 401 if missing or unknown
  ─ Returns the key string if valid
       │
       ▼
  require_reader()  ─ or ─  require_admin()
  ─ Calls get_api_key() first (via Depends)
  ─ Looks up the role in VALID_KEYS
  ─ Returns 403 if role is wrong
  ─ Returns the key string if role is OK
       │
       ▼
  Your route function (e.g. protected_data)
  ─ Receives the validated key as a parameter
  ─ Does the actual work and returns a response
```

Here is how this looks in code:

```python
def get_api_key(x_api_key: Annotated[Optional[str], Header()] = None) -> str:
    if not x_api_key:
        raise HTTPException(status_code=401, detail="Missing X-API-Key header")
    if x_api_key not in VALID_KEYS:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return x_api_key


def require_reader(x_api_key: str = Depends(get_api_key)) -> str:
    role = VALID_KEYS[x_api_key]
    if role not in ("reader", "admin"):
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    return x_api_key


@app.get("/protected/data")
def protected_data(api_key: str = Depends(require_reader)):
    ...
```

When a request hits `GET /protected/data`, FastAPI sees `Depends(require_reader)`. Before it even calls `protected_data`, it calls `require_reader`. And `require_reader` itself has `Depends(get_api_key)`, so FastAPI calls *that* first. The chain runs from the inside out — `get_api_key` → `require_reader` → `protected_data`.

`Depends()` is a powerful pattern. You will see it used for authentication, database sessions, rate limiting, and much more in real FastAPI applications.

---

## 5. Roles: Reader vs Admin

This API stores its keys and roles in a simple Python dictionary:

```python
VALID_KEYS: dict[str, str] = {
    "reader-key-123": "reader",
    "admin-key-456": "admin",
}
```

The dictionary maps each key string to a role name. When a request comes in, the flow is:

1. `get_api_key` checks that the key exists in `VALID_KEYS`
2. `require_reader` or `require_admin` looks up the role: `role = VALID_KEYS[x_api_key]`
3. The role is compared against what the route requires

| Key | Role | Can access `/protected/data`? | Can access `/admin/*`? |
|---|---|---|---|
| `reader-key-123` | `reader` | Yes | No |
| `admin-key-456` | `admin` | Yes | Yes |
| *(no key)* | *(none)* | No | No |

In a real application you would never hard-code keys like this. You would store them (hashed) in a database and load them from environment variables or a secrets manager. But for learning, a dictionary is perfectly clear.

---

## 6. 401 vs 403 — When to Use Which

These two status codes are easy to confuse. Here is the clearest way to remember them:

**401 Unauthorized — "I don't know who you are"**

The request is missing an API key, or the key provided is not recognized. The server cannot identify the caller at all.

```
GET /protected/data
(no X-API-Key header)

→ 401 {"detail": "Missing X-API-Key header"}
```

```
GET /protected/data
X-API-Key: made-up-nonsense

→ 401 {"detail": "Invalid API key"}
```

**403 Forbidden — "I know who you are, but no"**

The key is valid and recognized, but the role attached to it is not allowed to use this particular route.

```
GET /admin/notes
X-API-Key: reader-key-123   ← valid key, but role is "reader"

→ 403 {"detail": "Admin access required"}
```

A useful memory trick: **401 means "prove yourself first"**, **403 means "I know you, and the answer is still no"**.

---

## 7. Public vs Protected Routes

Not every route needs a key. In this API, some routes are intentionally open to everyone:

```python
# No Depends — anyone can call this
@app.get("/public")
def public():
    return {"message": "This is public. Anyone can read this."}
```

Compare that to a protected route:

```python
# Depends(require_reader) — caller must provide a valid reader or admin key
@app.get("/protected/data")
def protected_data(api_key: str = Depends(require_reader)):
    role = VALID_KEYS[api_key]
    return {"secret": "Here is your protected data!", "accessed_with_role": role}
```

The only difference is the presence of `Depends(...)` in the function signature. There is no global setting — you opt routes in to protection one by one. This means you can freely mix public and private routes in the same application, which is very common.

---

## 8. Code Walkthrough

Let's trace through two complete request/response cycles.

**Request 1: Reader accesses protected data**

1. `GET /protected/data` arrives with header `X-API-Key: reader-key-123`
2. FastAPI sees `Depends(require_reader)` on `protected_data`
3. FastAPI calls `require_reader`, which has `Depends(get_api_key)`
4. FastAPI calls `get_api_key`:
   - `x_api_key` is `"reader-key-123"` (parsed from the header)
   - It is not empty, and it exists in `VALID_KEYS`
   - Returns `"reader-key-123"`
5. Back in `require_reader`:
   - `role = VALID_KEYS["reader-key-123"]` → `"reader"`
   - `"reader"` is in `("reader", "admin")` — passes
   - Returns `"reader-key-123"`
6. `protected_data` runs, looks up the role, returns `{"secret": "...", "accessed_with_role": "reader"}`

**Request 2: Reader tries to access an admin route**

1. `POST /admin/notes` arrives with header `X-API-Key: reader-key-123`
2. FastAPI sees `Depends(require_admin)` on `create_note`
3. `get_api_key` runs — key is valid, returns the key string
4. `require_admin` runs:
   - `role = VALID_KEYS["reader-key-123"]` → `"reader"`
   - `"reader" != "admin"` — raises `HTTPException(status_code=403, ...)`
5. FastAPI catches the exception and returns `403 {"detail": "Admin access required"}`
6. `create_note` is **never called**

The admin notes routes also include a `GET /admin/notes` that lists all notes, and `DELETE /admin/notes/{note_id}` that removes a specific note by ID (returning 404 if it does not exist).

---

## 9. Testing in Postman

**Step 1: Test the public route**

- Method: `GET`
- URL: `http://localhost:8000/public`
- No headers needed
- Expected: `200 {"message": "This is public. Anyone can read this."}`

**Step 2: Test with no key (expect 401)**

- Method: `GET`
- URL: `http://localhost:8000/protected/data`
- No headers
- Expected: `401 {"detail": "Missing X-API-Key header"}`

**Step 3: Test with a reader key**

- Method: `GET`
- URL: `http://localhost:8000/protected/data`
- Headers tab → add key `X-API-Key`, value `reader-key-123`
- Expected: `200 {"secret": "...", "accessed_with_role": "reader"}`

**Step 4: Test reader trying to reach an admin route (expect 403)**

- Method: `GET`
- URL: `http://localhost:8000/admin/notes`
- Headers tab → `X-API-Key: reader-key-123`
- Expected: `403 {"detail": "Admin access required"}`

**Step 5: Test with an admin key**

- Method: `GET`
- URL: `http://localhost:8000/admin/notes`
- Headers tab → `X-API-Key: admin-key-456`
- Expected: `200 []` (empty list at first)

**Step 6: Create a note as admin**

- Method: `POST`
- URL: `http://localhost:8000/admin/notes`
- Headers tab → `X-API-Key: admin-key-456` and `Content-Type: application/json`
- Body (raw JSON): `{"title": "My First Note", "body": "Hello, admin world!"}`
- Expected: `201 {"id": 1, "title": "My First Note", "body": "Hello, admin world!"}`
