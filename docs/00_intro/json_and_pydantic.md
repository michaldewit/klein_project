# JSON and Pydantic

## What is JSON?

**JSON** (JavaScript Object Notation) is the most common format for sending data between a client and a server. It looks like Python dictionaries and lists, but it is plain text.

### JSON Data Types

```json
{
  "name": "Alice",           ← string (text in double quotes)
  "age": 30,                 ← number (integer)
  "price": 19.99,            ← number (decimal)
  "is_active": true,         ← boolean (true or false, lowercase)
  "nickname": null,          ← null (Python's None)
  "tags": ["api", "python"], ← array (Python list)
  "address": {               ← object (Python dict, can be nested)
    "city": "Amsterdam",
    "zip": "1234AB"
  }
}
```

### JSON Rules

- Keys must be **strings in double quotes** — `"name"`, not `name` or `'name'`
- Strings use **double quotes** — `"hello"`, not `'hello'`
- No trailing commas — `{"a": 1, "b": 2}` not `{"a": 1, "b": 2,}`
- `true` / `false` / `null` are lowercase

---

## What is Pydantic?

**Pydantic** is a Python library that validates data automatically. You define a model (a Python class) and Pydantic checks that any incoming JSON matches that model.

FastAPI uses Pydantic to validate request bodies before your code runs. If the data is invalid, FastAPI automatically returns a **422 Unprocessable Entity** response with a helpful error message — you never even see the bad data.

### Defining a Model

```python
from pydantic import BaseModel, Field
from typing import Optional

class ItemCreate(BaseModel):
    name: str                               # required, must be a string
    price: float = Field(..., gt=0)         # required, must be > 0
    stock: int = Field(default=0, ge=0)     # optional, default 0, must be >= 0
    category: Optional[str] = None          # optional, can be None
```

### What `Field(...)` Does

`Field` lets you add extra validation rules:

| Argument | Meaning |
|----------|---------|
| `...` | Required (no default) |
| `default=0` | Optional with this default value |
| `gt=0` | Greater than 0 |
| `ge=0` | Greater than or equal to 0 |
| `lt=100` | Less than 100 |
| `le=100` | Less than or equal to 100 |
| `min_length=1` | String must have at least 1 character |
| `max_length=50` | String cannot exceed 50 characters |

### Valid Request Body

```json
{"name": "Apple", "price": 1.5, "stock": 10}
```

### Invalid Request Bodies (FastAPI rejects automatically)

```json
{"price": 1.5}           ← missing required field "name" → 422
{"name": "", "price": 0} ← name too short, price not > 0 → 422
{"name": "X", "price": "cheap"} ← price must be a number → 422
```

---

## The Three-Model Pattern (CRUD APIs)

In CRUD APIs you often see three versions of a model:

```python
class ItemCreate(BaseModel):
    """What the client sends when creating an item."""
    name: str = Field(..., min_length=1)
    price: float = Field(..., gt=0)
    stock: int = Field(default=0, ge=0)

class ItemUpdate(BaseModel):
    """What the client sends for a full update (PUT) — all fields required."""
    name: str = Field(..., min_length=1)
    price: float = Field(..., gt=0)
    stock: int = Field(..., ge=0)

class Item(BaseModel):
    """What the server sends back — includes the auto-generated id."""
    id: int
    name: str
    price: float
    stock: int
```

For partial updates (PATCH), fields are `Optional` with `None` defaults:

```python
class ItemPatch(BaseModel):
    """What the client sends for a partial update — all fields optional."""
    name: Optional[str] = Field(default=None, min_length=1)
    price: Optional[float] = Field(default=None, gt=0)
    stock: Optional[int] = Field(default=None, ge=0)
```

---

## model_dump() and exclude_none=True

`model_dump()` converts a Pydantic model to a plain Python dictionary:

```python
patch = ItemPatch(price=5.0)   # name and stock are None
patch.model_dump()
# → {"name": None, "price": 5.0, "stock": None}

patch.model_dump(exclude_none=True)
# → {"price": 5.0}   ← only the fields the client actually sent
```

This is how PATCH works — only fields explicitly provided by the client are updated:

```python
@app.patch("/items/{id}")
def patch_item(id: int, body: ItemPatch):
    existing = _store[id]
    updates = body.model_dump(exclude_none=True)  # e.g. {"price": 5.0}
    existing.update(updates)                       # only price changes
    return existing
```

---

## Response Models

FastAPI can automatically filter the response through a Pydantic model using `response_model`:

```python
@app.get("/items/{id}", response_model=Item)  # only Item fields are returned
def get_item(id: int):
    return _store[id]   # can be a dict or any object — FastAPI serialises it
```

This means even if `_store[id]` contains extra internal fields (like a password hash), they will not leak into the response if they are not in `Item`.
