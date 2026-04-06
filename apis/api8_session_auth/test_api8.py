"""
Tests for API 8 - Session Auth: Shopping Cart API

Requirements covered:
  - GET /       returns 200 without session
  - POST /login returns 200 for valid credentials
  - POST /login returns 401 for wrong password
  - POST /login returns 401 for unknown user
  - POST /logout returns 200 when logged in
  - POST /logout returns 401 when not logged in
  - GET /cart   returns 401 without session
  - GET /cart   returns empty cart after login
  - POST /cart/items returns 401 without session
  - POST /cart/items adds item to cart
  - POST /cart/items calculates line_total and total
  - POST /cart/items adds to quantity if item already exists
  - DELETE /cart/items/{name} removes item from cart
  - DELETE /cart/items/{name} returns 404 if item not in cart
  - PUT /cart/items/{name} updates quantity
  - PUT /cart/items/{name} returns 404 if item not in cart
  - Cart is per-user (Alice's cart != Bob's cart)
  - After logout session is cleared (401 on subsequent requests)
"""

import pytest
from fastapi.testclient import TestClient
from apis.api8_session_auth.main import app, _reset

# TestClient with raise_server_exceptions=False so we see 5xx as responses
client = TestClient(app, raise_server_exceptions=False)


@pytest.fixture(autouse=True)
def reset_state():
    _reset()
    yield


def login(username: str, password: str) -> TestClient:
    """Login and return a new client with the session cookie set."""
    response = client.post(
        "/login",
        data={"username": username, "password": password},
    )
    assert response.status_code == 200, f"Login failed: {response.json()}"
    # Extract session cookie and create a client with it set
    cookies = dict(response.cookies)
    return TestClient(app, cookies=cookies, raise_server_exceptions=False)


# ── GET / (public) ────────────────────────────────────────────────────────────

def test_root_no_session_returns_200():
    assert client.get("/").status_code == 200


def test_root_has_message():
    assert "message" in client.get("/").json()


# ── POST /login ───────────────────────────────────────────────────────────────

def test_login_valid_returns_200():
    response = client.post("/login", data={"username": "alice", "password": "alicepass"})
    assert response.status_code == 200


def test_login_returns_username():
    response = client.post("/login", data={"username": "alice", "password": "alicepass"})
    assert response.json()["username"] == "alice"


def test_login_wrong_password_returns_401():
    response = client.post("/login", data={"username": "alice", "password": "wrong"})
    assert response.status_code == 401


def test_login_unknown_user_returns_401():
    response = client.post("/login", data={"username": "nobody", "password": "pass"})
    assert response.status_code == 401


def test_login_sets_session_cookie():
    response = client.post("/login", data={"username": "alice", "password": "alicepass"})
    assert "session" in response.cookies


# ── POST /logout ──────────────────────────────────────────────────────────────

def test_logout_when_logged_in_returns_200():
    authed = login("alice", "alicepass")
    assert authed.post("/logout").status_code == 200


def test_logout_when_not_logged_in_returns_401():
    assert client.post("/logout").status_code == 401


def test_after_logout_cart_returns_401():
    authed = login("alice", "alicepass")
    authed.post("/logout")
    # The session should be invalidated — reusing same cookie should fail
    assert authed.get("/cart").status_code == 401


# ── GET /cart ─────────────────────────────────────────────────────────────────

def test_cart_no_session_returns_401():
    assert client.get("/cart").status_code == 401


def test_cart_initially_empty():
    authed = login("alice", "alicepass")
    data = authed.get("/cart").json()
    assert data["items"] == []
    assert data["total"] == 0.0


def test_cart_has_username():
    authed = login("alice", "alicepass")
    data = authed.get("/cart").json()
    assert data["username"] == "alice"


# ── POST /cart/items ──────────────────────────────────────────────────────────

def test_add_item_no_session_returns_401():
    response = client.post("/cart/items", json={"product_name": "Apple", "quantity": 2, "price": 1.5})
    assert response.status_code == 401


def test_add_item_returns_cart_with_item():
    authed = login("alice", "alicepass")
    cart = authed.post(
        "/cart/items",
        json={"product_name": "Apple", "quantity": 2, "price": 1.5},
    ).json()
    assert len(cart["items"]) == 1
    assert cart["items"][0]["product_name"] == "Apple"


def test_add_item_calculates_line_total():
    authed = login("alice", "alicepass")
    cart = authed.post(
        "/cart/items",
        json={"product_name": "Apple", "quantity": 3, "price": 2.0},
    ).json()
    assert cart["items"][0]["line_total"] == 6.0


def test_add_item_calculates_cart_total():
    authed = login("alice", "alicepass")
    authed.post("/cart/items", json={"product_name": "Apple", "quantity": 2, "price": 1.5})
    cart = authed.post(
        "/cart/items",
        json={"product_name": "Banana", "quantity": 1, "price": 0.5},
    ).json()
    assert cart["total"] == pytest.approx(3.5)


def test_add_same_item_increases_quantity():
    authed = login("alice", "alicepass")
    authed.post("/cart/items", json={"product_name": "Apple", "quantity": 2, "price": 1.5})
    cart = authed.post(
        "/cart/items",
        json={"product_name": "Apple", "quantity": 3, "price": 1.5},
    ).json()
    assert len(cart["items"]) == 1
    assert cart["items"][0]["quantity"] == 5


# ── PUT /cart/items/{name} ────────────────────────────────────────────────────

def test_update_quantity():
    authed = login("alice", "alicepass")
    authed.post("/cart/items", json={"product_name": "Apple", "quantity": 2, "price": 1.5})
    cart = authed.put("/cart/items/Apple", json={"quantity": 10}).json()
    assert cart["items"][0]["quantity"] == 10


def test_update_unknown_item_returns_404():
    authed = login("alice", "alicepass")
    response = authed.put("/cart/items/Unknown", json={"quantity": 1})
    assert response.status_code == 404


# ── DELETE /cart/items/{name} ─────────────────────────────────────────────────

def test_remove_item_from_cart():
    authed = login("alice", "alicepass")
    authed.post("/cart/items", json={"product_name": "Apple", "quantity": 2, "price": 1.5})
    cart = authed.delete("/cart/items/Apple").json()
    assert cart["items"] == []


def test_remove_unknown_item_returns_404():
    authed = login("alice", "alicepass")
    assert authed.delete("/cart/items/NotHere").status_code == 404


# ── Per-user isolation ────────────────────────────────────────────────────────

def test_carts_are_isolated_between_users():
    alice = login("alice", "alicepass")
    bob = login("bob", "bobpass")

    alice.post("/cart/items", json={"product_name": "Apple", "quantity": 1, "price": 1.0})

    bob_cart = bob.get("/cart").json()
    assert bob_cart["items"] == []


def test_alice_and_bob_have_separate_carts():
    alice = login("alice", "alicepass")
    bob = login("bob", "bobpass")

    alice.post("/cart/items", json={"product_name": "Apple", "quantity": 1, "price": 1.0})
    bob.post("/cart/items", json={"product_name": "Banana", "quantity": 5, "price": 0.3})

    alice_cart = alice.get("/cart").json()
    bob_cart = bob.get("/cart").json()

    assert alice_cart["items"][0]["product_name"] == "Apple"
    assert bob_cart["items"][0]["product_name"] == "Banana"
    assert len(alice_cart["items"]) == 1
    assert len(bob_cart["items"]) == 1
