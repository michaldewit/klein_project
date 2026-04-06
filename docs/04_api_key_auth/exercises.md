# API 4 — Exercises

Work through these exercises in order. Each one builds your understanding of authentication, authorization, and dependency injection. The source file to edit is `apis/api4_auth/main.py`.

Run the server with:
```bash
uvicorn apis.api4_auth.main:app --reload
```

---

## Exercise 1 — Add a Third Role (Easy)

**Goal:** Practice adding a new key and understanding how roles flow through the dependency chain.

### Task

Add a third entry to `VALID_KEYS`:

```python
"superreader-key-789": "superreader"
```

This role should be able to access `GET /protected/data` (same as `reader`) but should **not** be allowed to access any `/admin/*` routes.

### Steps

1. Add the new key to the `VALID_KEYS` dictionary
2. Update `require_reader` so it also accepts the `"superreader"` role alongside `"reader"` and `"admin"`
3. Confirm `require_admin` is unchanged and still only allows `"admin"`

### What to Test

| Request | Key | Expected |
|---|---|---|
| `GET /protected/data` | `superreader-key-789` | `200` — success |
| `GET /admin/notes` | `superreader-key-789` | `403` — forbidden |
| `GET /protected/data` | `reader-key-123` | `200` — still works |

### Hint

You only need to change one line in `require_reader`. Look at the tuple it checks against.

---

## Exercise 2 — Profile Endpoint (Medium)

**Goal:** Practice creating a new protected route that uses the injected key to return information about the caller.

### Task

Add a new endpoint `GET /protected/profile` that returns the caller's role and a truncated version of their key.

The response should look like this (for the reader key):

```json
{
  "role": "reader",
  "key_prefix": "reader-ke..."
}
```

`key_prefix` should be the **first 10 characters** of the key followed by `"..."`. So `"reader-key-123"` becomes `"reader-ke..."`.

### Steps

1. Add a new route `GET /protected/profile` with `Depends(require_reader)` so both readers and admins can access it
2. Inside the route, look up the role using `VALID_KEYS[api_key]`
3. Build the `key_prefix` by slicing the key string: `api_key[:10] + "..."`
4. Return a dict with `role` and `key_prefix`

### What to Test

- Call with `reader-key-123` → `{"role": "reader", "key_prefix": "reader-ke..."}`
- Call with `admin-key-456` → `{"role": "admin", "key_prefix": "admin-key-"}`  
  *(10 chars of `"admin-key-456"` is `"admin-key-"`)*
- Call with no key → `401`
- Call with `reader-key-123` on `GET /admin/notes` → still `403` (your new route should not break anything)

### Hint

The route function signature will look like:

```python
@app.get("/protected/profile")
def get_profile(api_key: str = Depends(require_reader)):
    ...
```

---

## Exercise 3 — Per-Key Request Counter (Medium)

**Goal:** Practice storing state in a dependency and exposing it through a dedicated admin endpoint.

### Task

Track how many times each API key has been used and expose that data to admins.

### Steps

1. Add a module-level dictionary to store counts:

    ```python
    _request_count: dict[str, int] = {}
    ```

2. Modify `get_api_key` to increment the counter each time a valid key is used:

    ```python
    _request_count[x_api_key] = _request_count.get(x_api_key, 0) + 1
    ```

    Add this line just before `return x_api_key`.

3. Add a new endpoint `GET /admin/stats` (admin only) that returns the counter dictionary:

    ```python
    @app.get("/admin/stats")
    def get_stats(api_key: str = Depends(require_admin)):
        return {"request_counts": _request_count}
    ```

### What to Test

1. Call `GET /protected/data` with `reader-key-123` a few times
2. Call `GET /admin/stats` with `admin-key-456`
3. You should see something like:

    ```json
    {
      "request_counts": {
        "reader-key-123": 3,
        "admin-key-456": 1
      }
    }
    ```

### Things to think about

- The count for `admin-key-456` goes up every time you call `GET /admin/stats` itself. Why?
- What happens to the counts when you restart the server? How would you fix that in a production app?

---

## Exercise 4 — Dynamic Key Generation (Hard)

**Goal:** Practice mutating shared state through a POST endpoint, using the `secrets` module for cryptographically safe random values.

### Task

Add `POST /admin/keys` that generates a brand new reader key and registers it so it works immediately — no server restart needed.

The response should look like:

```json
{
  "key": "a3f9c21d8b4e07165c2f9d30a1b4e872",
  "role": "reader"
}
```

### Steps

1. Import the `secrets` module at the top of the file:

    ```python
    import secrets
    ```

2. Add the endpoint (admin only):

    ```python
    @app.post("/admin/keys", status_code=201)
    def create_key(api_key: str = Depends(require_admin)):
        new_key = secrets.token_hex(16)   # 32-character hex string
        VALID_KEYS[new_key] = "reader"
        return {"key": new_key, "role": "reader"}
    ```

3. Test the full flow:
    - Call `POST /admin/keys` with the admin key → copy the returned `key`
    - Call `GET /protected/data` using the new key as `X-API-Key`
    - It should return `200` immediately, with `"accessed_with_role": "reader"`

### Things to think about

- What happens to dynamically added keys when the server restarts? They are lost, because `VALID_KEYS` lives only in memory. How would you make them permanent?
- `secrets.token_hex(16)` produces 32 hex characters. What does `token_hex(32)` produce?
- Should the response include the full key or only a prefix? What are the security trade-offs?

---

## Checklist

| Exercise | Completed |
|---|---|
| 1 — Add `superreader` role | [ ] |
| 2 — Add `GET /protected/profile` | [ ] |
| 3 — Add per-key request counter + `GET /admin/stats` | [ ] |
| 4 — Add `POST /admin/keys` | [ ] |
