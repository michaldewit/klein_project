# API 2 — CRUD Items

This API is where things get real. You will build a complete in-memory item store that supports creating, reading, updating, and deleting records. Every major web application — from a to-do list to an e-commerce shop — is built on these same four operations.

---

## What You Will Learn

- What CRUD means and why it maps to specific HTTP methods
- How to keep data alive between requests using a module-level store
- Why you need three separate Pydantic models for Create, Update, and Patch
- The practical difference between PUT and PATCH
- How HTTP status codes communicate the result of an operation to the caller

---

## What is CRUD?

CRUD stands for **Create, Read, Update, Delete**. Think of a shopping list on your phone:

| Letter | Operation | Shopping list analogy | HTTP method | Our endpoint |
|---|---|---|---|---|
| **C** | Create | Add "apples" to the list | `POST` | `POST /items` |
| **R** | Read | Look at what is on the list | `GET` | `GET /items`, `GET /items/{id}` |
| **U** | Update | Change "apples" to "green apples" | `PUT` / `PATCH` | `PUT /items/{id}`, `PATCH /items/{id}` |
| **D** | Delete | Cross "apples" off the list | `DELETE` | `DELETE /items/{id}` |

These four operations, expressed through HTTP methods, are the foundation of **REST APIs** — the style used by the vast majority of APIs you will encounter in the real world.

---

## The In-Memory Store

Our API needs somewhere to keep items between requests. In a production app you would use a database. Here we use a plain Python dictionary so nothing gets in the way of learning the API concepts:

```python
# In-memory store: { id -> item_dict }
_store: dict[int, dict] = {}
_next_id: int = 1
```

- `_store` is a dictionary that maps an integer ID to an item dictionary. For example, after creating two items it might look like: `{1: {"id": 1, "name": "Apple", "price": 0.5, "stock": 100}, 2: {...}}`.
- `_next_id` is a counter that increments each time a new item is created. This is a simple way to generate unique IDs without a database sequence.
- The leading underscore on both names is a Python convention meaning "this is an internal implementation detail, not part of the public interface".

**Important limitation:** Because these variables live in the server process's memory, they are reset every time you restart the server. Stop `uvicorn`, run it again, and the store is empty. This is fine for learning — in production you would use a database that persists to disk.

---

## The Three-Model Pattern

You might wonder: why do we have four Pydantic models (`ItemCreate`, `ItemUpdate`, `ItemPatch`, and `Item`) for what is basically the same thing? Each model has a different job:

```python
class ItemCreate(BaseModel):
    name: str = Field(..., min_length=1, description="Name of the item")
    price: float = Field(..., gt=0, description="Price must be positive")
    stock: int = Field(default=0, ge=0, description="Stock quantity")
```

`ItemCreate` is what the **client sends when creating an item**. Notice:
- `name` and `price` are required (the `...` means "no default — this field is mandatory").
- `stock` has a default of `0` — if the client does not send it, we assume no stock.
- `Field(gt=0)` means "greater than zero" — FastAPI validates this automatically.

```python
class ItemUpdate(BaseModel):
    name: str = Field(..., min_length=1)
    price: float = Field(..., gt=0)
    stock: int = Field(..., ge=0)
```

`ItemUpdate` is for **full replacement (PUT)**. Every field is required. If you only send `name`, FastAPI rejects the request because `price` and `stock` are missing.

```python
class ItemPatch(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1)
    price: Optional[float] = Field(default=None, gt=0)
    stock: Optional[int] = Field(default=None, ge=0)
```

`ItemPatch` is for **partial update (PATCH)**. Every field is optional (`Optional[str]` with `default=None`). The client only sends the fields it wants to change.

```python
class Item(BaseModel):
    id: int
    name: str
    price: float
    stock: int
```

`Item` is the **response model** — the full shape of an item as returned to the client, including the `id` that the server assigned.

> For a deeper dive into Pydantic models and JSON validation, see `json_and_pydantic.md`.

---

## PUT vs PATCH

This is one of the most commonly confused distinctions in REST APIs.

**Scenario:** Your store has this item:

```json
{"id": 1, "name": "Apple", "price": 0.50, "stock": 100}
```

You want to update the price to `0.75` but keep everything else the same.

### Using PUT (full replacement)

You must send **all fields**, even the ones that are not changing:

```
PUT /items/1
{"name": "Apple", "price": 0.75, "stock": 100}
```

If you only send `{"price": 0.75}`, FastAPI returns 422 because `name` and `stock` are required in `ItemUpdate`.

The server replaces the entire stored object:

```python
updated = {"id": item_id, **body.model_dump()}
_store[item_id] = updated
```

### Using PATCH (partial update)

You only send **the fields you want to change**:

```
PATCH /items/1
{"price": 0.75}
```

The server merges the new values on top of the existing ones:

```python
patch_data = body.model_dump(exclude_none=True)  # {"price": 0.75}, skips None fields
existing.update(patch_data)                       # merges into the stored dict
```

`exclude_none=True` is the key detail — it tells Pydantic to skip fields that were not provided (i.e. they are still `None`), so only the fields the client actually sent get merged.

**Rule of thumb:** Use PUT when you always send the complete object. Use PATCH when you want to change one or two fields without touching the rest.

---

## Status Codes in Practice

HTTP status codes are a standardised language between servers and clients. Here is how this API uses them:

| Code | Name | When we use it | Why |
|---|---|---|---|
| `200 OK` | Success | GET requests that return data | The default — everything went fine |
| `201 Created` | Created | POST /items | Signals that a new resource was created, not just a query |
| `204 No Content` | No Content | DELETE /items/{id} | Success, but there is nothing to send back |
| `404 Not Found` | Not Found | GET/PUT/PATCH/DELETE with unknown ID | The item does not exist |
| `422 Unprocessable Entity` | Validation Error | Missing required fields, wrong types | FastAPI sends this automatically when Pydantic validation fails |

The `201` and `204` status codes are set explicitly in the decorators:

```python
@app.post("/items", status_code=201)
def create_item(body: ItemCreate): ...

@app.delete("/items/{item_id}", status_code=204)
def delete_item(item_id: int): ...
```

The `404` is raised with `HTTPException`:

```python
from fastapi import HTTPException

if item_id not in _store:
    raise HTTPException(status_code=404, detail=f"Item {item_id} not found")
```

`HTTPException` immediately stops the function and sends the error response. The `detail` field is included in the JSON response body so the client gets a human-readable message.

---

## Code Walkthrough

```python
# ── In-memory store ───────────────────────────────────────────────────────────

_store: dict[int, dict] = {}   # empty store at startup
_next_id: int = 1              # IDs start at 1


# ── GET /items ────────────────────────────────────────────────────────────────

@app.get("/items", response_model=list[Item], summary="List all items")
def list_items(
    skip: int = Query(default=0, ge=0),          # skip the first N results
    limit: int = Query(default=100, ge=1, le=1000),  # return at most this many
):
    items = list(_store.values())    # convert dict values to a list
    return items[skip : skip + limit]  # Python slice for pagination


# ── GET /items/{item_id} ──────────────────────────────────────────────────────

@app.get("/items/{item_id}", response_model=Item)
def get_item(item_id: int):
    if item_id not in _store:                          # check existence first
        raise HTTPException(status_code=404, detail=f"Item {item_id} not found")
    return _store[item_id]                             # return the dict directly


# ── POST /items ───────────────────────────────────────────────────────────────

@app.post("/items", response_model=Item, status_code=201)
def create_item(body: ItemCreate):
    global _next_id                              # we need to modify the module variable
    item = {"id": _next_id, **body.model_dump()} # combine the auto-generated id with
                                                 # the fields from the request body
    _store[_next_id] = item                      # save it
    _next_id += 1                                # increment for the next item
    return item


# ── PUT /items/{item_id} ──────────────────────────────────────────────────────

@app.put("/items/{item_id}", response_model=Item)
def update_item(item_id: int, body: ItemUpdate):
    if item_id not in _store:
        raise HTTPException(status_code=404, detail=f"Item {item_id} not found")
    updated = {"id": item_id, **body.model_dump()}  # full replacement
    _store[item_id] = updated                       # overwrite the old entry
    return updated


# ── PATCH /items/{item_id} ────────────────────────────────────────────────────

@app.patch("/items/{item_id}", response_model=Item)
def patch_item(item_id: int, body: ItemPatch):
    if item_id not in _store:
        raise HTTPException(status_code=404, detail=f"Item {item_id} not found")
    existing = _store[item_id]
    patch_data = body.model_dump(exclude_none=True)  # only the provided fields
    existing.update(patch_data)                       # merge into the existing dict
    return existing


# ── DELETE /items/{item_id} ───────────────────────────────────────────────────

@app.delete("/items/{item_id}", status_code=204)
def delete_item(item_id: int):
    if item_id not in _store:
        raise HTTPException(status_code=404, detail=f"Item {item_id} not found")
    del _store[item_id]       # remove it from the dict
                              # no return value needed — 204 means "nothing to return"
```

---

## Testing in Postman

Start the server:

```bash
uvicorn main:app --reload
```

Follow these steps in order to create an item, read it back, update it, and then delete it.

### Step 1 — Create an item (POST)

1. Method: **POST**, URL: `http://localhost:8000/items`
2. Body → raw → JSON:
   ```json
   {"name": "Apple", "price": 0.50, "stock": 100}
   ```
3. Click **Send**. You should get a `201 Created` status and:
   ```json
   {"id": 1, "name": "Apple", "price": 0.5, "stock": 100}
   ```

### Step 2 — List all items (GET)

1. Method: **GET**, URL: `http://localhost:8000/items`
2. Click **Send**. You should see a JSON array with your Apple.

### Step 3 — Get a single item (GET)

1. Method: **GET**, URL: `http://localhost:8000/items/1`
2. Click **Send**. You should see just the Apple.
3. Try `http://localhost:8000/items/999` — you should get a `404` response.

### Step 4 — Fully update an item (PUT)

1. Method: **PUT**, URL: `http://localhost:8000/items/1`
2. Body → raw → JSON (all fields required):
   ```json
   {"name": "Green Apple", "price": 0.75, "stock": 80}
   ```
3. Click **Send**. The item is now fully replaced.

### Step 5 — Partially update an item (PATCH)

1. Method: **PATCH**, URL: `http://localhost:8000/items/1`
2. Body → raw → JSON (only the field you want to change):
   ```json
   {"stock": 50}
   ```
3. Click **Send**. Only `stock` changed; `name` and `price` are unchanged.

### Step 6 — Delete the item (DELETE)

1. Method: **DELETE**, URL: `http://localhost:8000/items/1`
2. Click **Send**. You should get a `204 No Content` status with an empty body.
3. Try `GET /items/1` — you should now get a `404`.
