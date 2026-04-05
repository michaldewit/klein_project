"""
Tests for API 2 - In-Memory CRUD

Requirements covered:
  - GET  /items           returns empty list initially
  - POST /items           creates item, returns 201 with id
  - GET  /items           lists created items
  - GET  /items/{id}      returns correct item
  - GET  /items/{id}      returns 404 for unknown id
  - PUT  /items/{id}      fully replaces item
  - PUT  /items/{id}      returns 404 for unknown id
  - PATCH /items/{id}     partially updates item
  - PATCH /items/{id}     returns 404 for unknown id
  - DELETE /items/{id}    removes item, returns 204
  - DELETE /items/{id}    returns 404 for unknown id
  - POST /items           validates price > 0
  - POST /items           validates stock >= 0
  - GET  /items?skip&limit pagination works
"""

import pytest
from fastapi.testclient import TestClient
from apis.api2_crud.main import app, _reset

client = TestClient(app)


@pytest.fixture(autouse=True)
def reset_store():
    """Reset in-memory store before each test."""
    _reset()
    yield


# ── GET /items (empty) ───────────────────────────────────────────────────────

def test_list_items_empty():
    response = client.get("/items")
    assert response.status_code == 200
    assert response.json() == []


# ── POST /items ──────────────────────────────────────────────────────────────

def test_create_item_status_201():
    response = client.post("/items", json={"name": "Apple", "price": 1.5, "stock": 10})
    assert response.status_code == 201


def test_create_item_returns_id():
    response = client.post("/items", json={"name": "Apple", "price": 1.5, "stock": 10})
    assert "id" in response.json()


def test_create_item_data_correct():
    response = client.post("/items", json={"name": "Banana", "price": 0.99, "stock": 5})
    data = response.json()
    assert data["name"] == "Banana"
    assert data["price"] == 0.99
    assert data["stock"] == 5


def test_create_item_default_stock_zero():
    response = client.post("/items", json={"name": "Cherry", "price": 2.0})
    assert response.json()["stock"] == 0


def test_create_item_invalid_price_zero():
    response = client.post("/items", json={"name": "Bad", "price": 0, "stock": 1})
    assert response.status_code == 422


def test_create_item_invalid_price_negative():
    response = client.post("/items", json={"name": "Bad", "price": -5.0, "stock": 1})
    assert response.status_code == 422


def test_create_item_invalid_stock_negative():
    response = client.post("/items", json={"name": "Bad", "price": 1.0, "stock": -1})
    assert response.status_code == 422


def test_create_multiple_items_increments_id():
    r1 = client.post("/items", json={"name": "A", "price": 1.0})
    r2 = client.post("/items", json={"name": "B", "price": 2.0})
    assert r1.json()["id"] != r2.json()["id"]


# ── GET /items (after create) ────────────────────────────────────────────────

def test_list_items_after_create():
    client.post("/items", json={"name": "Apple", "price": 1.5})
    client.post("/items", json={"name": "Banana", "price": 0.99})
    response = client.get("/items")
    assert len(response.json()) == 2


def test_list_items_pagination_skip():
    for i in range(5):
        client.post("/items", json={"name": f"Item{i}", "price": float(i + 1)})
    response = client.get("/items?skip=3")
    assert len(response.json()) == 2


def test_list_items_pagination_limit():
    for i in range(5):
        client.post("/items", json={"name": f"Item{i}", "price": float(i + 1)})
    response = client.get("/items?limit=2")
    assert len(response.json()) == 2


# ── GET /items/{id} ──────────────────────────────────────────────────────────

def test_get_item_returns_correct_data():
    created = client.post("/items", json={"name": "Apple", "price": 1.5, "stock": 3}).json()
    response = client.get(f"/items/{created['id']}")
    assert response.status_code == 200
    assert response.json()["name"] == "Apple"


def test_get_item_not_found():
    response = client.get("/items/9999")
    assert response.status_code == 404


# ── PUT /items/{id} ──────────────────────────────────────────────────────────

def test_put_item_updates_all_fields():
    created = client.post("/items", json={"name": "Old", "price": 1.0, "stock": 1}).json()
    response = client.put(f"/items/{created['id']}", json={"name": "New", "price": 9.99, "stock": 50})
    data = response.json()
    assert data["name"] == "New"
    assert data["price"] == 9.99
    assert data["stock"] == 50


def test_put_item_not_found():
    response = client.put("/items/9999", json={"name": "X", "price": 1.0, "stock": 0})
    assert response.status_code == 404


# ── PATCH /items/{id} ────────────────────────────────────────────────────────

def test_patch_item_partial_update():
    created = client.post("/items", json={"name": "Old", "price": 1.0, "stock": 1}).json()
    response = client.patch(f"/items/{created['id']}", json={"price": 5.0})
    data = response.json()
    assert data["price"] == 5.0
    assert data["name"] == "Old"  # unchanged


def test_patch_item_not_found():
    response = client.patch("/items/9999", json={"price": 1.0})
    assert response.status_code == 404


# ── DELETE /items/{id} ───────────────────────────────────────────────────────

def test_delete_item_returns_204():
    created = client.post("/items", json={"name": "Apple", "price": 1.5}).json()
    response = client.delete(f"/items/{created['id']}")
    assert response.status_code == 204


def test_delete_item_removes_from_list():
    created = client.post("/items", json={"name": "Apple", "price": 1.5}).json()
    client.delete(f"/items/{created['id']}")
    response = client.get("/items")
    assert len(response.json()) == 0


def test_delete_item_then_get_returns_404():
    created = client.post("/items", json={"name": "Apple", "price": 1.5}).json()
    client.delete(f"/items/{created['id']}")
    response = client.get(f"/items/{created['id']}")
    assert response.status_code == 404


def test_delete_item_not_found():
    response = client.delete("/items/9999")
    assert response.status_code == 404
