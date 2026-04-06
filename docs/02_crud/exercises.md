# Exercises — API 2: CRUD Items

Work through these in order. Each one builds on the previous. Try to solve each exercise yourself before reading the answer.

Run the API while working: `uvicorn apis.api2_crud.main:app --reload --port 8002`

---

## Exercise 1 (Easy) — Add a `category` field

**Task:** Add an optional `category` field (a string, default `None`) to items. It should appear in creates, updates, and responses.

**Files to edit:** `apis/api2_crud/main.py`

**Hint:** Add `category: Optional[str] = None` to `ItemCreate`, `ItemUpdate`, `ItemPatch`, and `Item`. Import `Optional` from `typing`.

<details>
<summary>Answer</summary>

```python
from typing import Optional

class ItemCreate(BaseModel):
    name: str = Field(..., min_length=1)
    price: float = Field(..., gt=0)
    stock: int = Field(default=0, ge=0)
    category: Optional[str] = None       # ← add this

class ItemUpdate(BaseModel):
    name: str = Field(..., min_length=1)
    price: float = Field(..., gt=0)
    stock: int = Field(..., ge=0)
    category: Optional[str] = None       # ← add this

class ItemPatch(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1)
    price: Optional[float] = Field(default=None, gt=0)
    stock: Optional[int] = Field(default=None, ge=0)
    category: Optional[str] = None       # ← add this

class Item(BaseModel):
    id: int
    name: str
    price: float
    stock: int
    category: Optional[str] = None       # ← add this
```

No changes needed to the endpoint functions — `model_dump()` automatically includes the new field.

**Test it in Postman:**
```json
POST /items
{"name": "Apple", "price": 1.5, "category": "fruit"}
```

</details>

---

## Exercise 2 (Easy) — Filter items by category

**Task:** Add a `?category=` query parameter to `GET /items` that returns only items in that category. When `category` is not provided, return all items as before.

**Hint:** Add `category: Optional[str] = Query(default=None)` to `list_items`. Filter the list before applying `skip`/`limit`.

<details>
<summary>Answer</summary>

```python
@app.get("/items", response_model=list[Item])
def list_items(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=1000),
    category: Optional[str] = Query(default=None),   # ← add this
):
    items = list(_store.values())
    if category is not None:                          # ← add this block
        items = [i for i in items if i.get("category") == category]
    return items[skip : skip + limit]
```

**Test it in Postman:** `GET /items?category=fruit`

</details>

---

## Exercise 3 (Medium) — Search by name

**Task:** Add `GET /items/search?name=apple` that returns items whose name contains the search string (case-insensitive). Return an empty list if nothing matches — not a 404.

**Important:** This new route must be declared **above** `GET /items/{item_id}` in the file. If you put it below, FastAPI will try to use the word "search" as an item ID.

**Hint:** Use a list comprehension with `.lower()` on both the query and the name.

<details>
<summary>Answer</summary>

```python
# Add this BEFORE the get_item endpoint
@app.get("/items/search", response_model=list[Item], summary="Search items by name")
def search_items(name: str = Query(default="", description="Search term")):
    results = [
        item for item in _store.values()
        if name.lower() in item["name"].lower()
    ]
    return results
```

**Test it in Postman:** `GET /items/search?name=app` — returns "Apple", "Pineapple", etc.

</details>

---

## Exercise 4 (Medium) — Block reserved names

**Task:** Prevent creating items with the name `"test"` (case-insensitive). Raise an HTTP 400 Bad Request with a helpful error message.

**Hint:** Add a check at the start of `create_item` using `HTTPException(status_code=400, ...)`.

<details>
<summary>Answer</summary>

```python
@app.post("/items", response_model=Item, status_code=201)
def create_item(body: ItemCreate):
    if body.name.lower() == "test":                   # ← add this check
        raise HTTPException(
            status_code=400,
            detail="The name 'test' is reserved and cannot be used",
        )
    global _next_id
    item = {"id": _next_id, **body.model_dump()}
    _store[_next_id] = item
    _next_id += 1
    return item
```

**Why 400 and not 422?** — 422 is for structural validation (wrong type, missing field). 400 is for business logic rejections (valid data, but not allowed). FastAPI's `HTTPException` lets you choose.

</details>

---

## Exercise 5 (Hard) — Inventory statistics

**Task:** Add `GET /items/stats` that returns a summary of the current inventory. The response should include:
- `total_items` — how many items are in the store
- `total_value` — sum of `price × stock` across all items
- `out_of_stock` — how many items have `stock == 0`
- `most_expensive` — the name of the item with the highest price (or `null` if no items)

**Hint:** This route must also be declared above `GET /items/{item_id}`.

<details>
<summary>Answer</summary>

```python
# Add this BEFORE the get_item endpoint
@app.get("/items/stats", summary="Inventory statistics")
def get_stats():
    items = list(_store.values())
    if not items:
        return {
            "total_items": 0,
            "total_value": 0.0,
            "out_of_stock": 0,
            "most_expensive": None,
        }
    return {
        "total_items": len(items),
        "total_value": round(sum(i["price"] * i["stock"] for i in items), 2),
        "out_of_stock": sum(1 for i in items if i["stock"] == 0),
        "most_expensive": max(items, key=lambda i: i["price"])["name"],
    }
```

**Test it:** Create a few items with different prices and stock levels, then `GET /items/stats`.

</details>
