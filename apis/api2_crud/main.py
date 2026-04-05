"""
API 2 - In-Memory CRUD API
Goal: Learn full Create/Read/Update/Delete with Pydantic models and HTTP status codes.

Resource: Item (id, name, price, stock)

Endpoints:
  GET    /items          - list all items (supports ?skip & ?limit)
  GET    /items/{id}     - get single item (404 if not found)
  POST   /items          - create item (201 Created)
  PUT    /items/{id}     - fully update item (404 if not found)
  PATCH  /items/{id}     - partially update item (404 if not found)
  DELETE /items/{id}     - delete item (404 if not found)
"""

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Optional

app = FastAPI(
    title="API 2 - CRUD Items",
    description="Full CRUD operations on an in-memory store of Items.",
    version="1.0.0",
)

# In-memory store: { id -> item_dict }
_store: dict[int, dict] = {}
_next_id: int = 1


def _reset():
    """Utility to reset state (used in tests)."""
    global _store, _next_id
    _store = {}
    _next_id = 1


class ItemCreate(BaseModel):
    name: str = Field(..., min_length=1, description="Name of the item")
    price: float = Field(..., gt=0, description="Price must be positive")
    stock: int = Field(default=0, ge=0, description="Stock quantity")


class ItemUpdate(BaseModel):
    name: str = Field(..., min_length=1)
    price: float = Field(..., gt=0)
    stock: int = Field(..., ge=0)


class ItemPatch(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1)
    price: Optional[float] = Field(default=None, gt=0)
    stock: Optional[int] = Field(default=None, ge=0)


class Item(BaseModel):
    id: int
    name: str
    price: float
    stock: int


@app.get("/items", response_model=list[Item], summary="List all items")
def list_items(
    skip: int = Query(default=0, ge=0, description="Number of items to skip"),
    limit: int = Query(default=100, ge=1, le=1000, description="Max items to return"),
):
    items = list(_store.values())
    return items[skip : skip + limit]


@app.get("/items/{item_id}", response_model=Item, summary="Get a single item")
def get_item(item_id: int):
    if item_id not in _store:
        raise HTTPException(status_code=404, detail=f"Item {item_id} not found")
    return _store[item_id]


@app.post("/items", response_model=Item, status_code=201, summary="Create an item")
def create_item(body: ItemCreate):
    global _next_id
    item = {"id": _next_id, **body.model_dump()}
    _store[_next_id] = item
    _next_id += 1
    return item


@app.put("/items/{item_id}", response_model=Item, summary="Fully update an item")
def update_item(item_id: int, body: ItemUpdate):
    if item_id not in _store:
        raise HTTPException(status_code=404, detail=f"Item {item_id} not found")
    updated = {"id": item_id, **body.model_dump()}
    _store[item_id] = updated
    return updated


@app.patch("/items/{item_id}", response_model=Item, summary="Partially update an item")
def patch_item(item_id: int, body: ItemPatch):
    if item_id not in _store:
        raise HTTPException(status_code=404, detail=f"Item {item_id} not found")
    existing = _store[item_id]
    patch_data = body.model_dump(exclude_none=True)
    existing.update(patch_data)
    return existing


@app.delete("/items/{item_id}", status_code=204, summary="Delete an item")
def delete_item(item_id: int):
    if item_id not in _store:
        raise HTTPException(status_code=404, detail=f"Item {item_id} not found")
    del _store[item_id]
