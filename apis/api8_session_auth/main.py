"""
API 8 - Session-Based Authentication with Cookies: Shopping Cart API
Goal: Learn how sessions and cookies work — the traditional web authentication model.

How it works:
  1. Client sends username + password to POST /login (form data)
  2. Server validates credentials, creates a session ID, stores it server-side
  3. Server sends back a cookie: Set-Cookie: session=<session_id>
  4. Browser automatically includes this cookie in ALL future requests
  5. Server looks up the session ID to know who is logged in
  6. POST /logout deletes the session server-side (immediate revocation!)

Key differences from JWT:
  - Session data lives ON THE SERVER (stateful) — JWT data lives IN THE TOKEN (stateless)
  - You can log out immediately by deleting the session
  - Browser handles cookies automatically — no JavaScript needed

The shopping cart:
  - Each user has their own cart (stored server-side, keyed by username)
  - The cart persists across multiple requests as long as the session is valid
  - Alice's cart is completely separate from Bob's cart

Users:
  alice / alicepass
  bob   / bobpass

Endpoints:
  GET  /                          - public welcome page
  POST /login                     - authenticate, set session cookie
  POST /logout                    - clear session
  GET  /cart                      - view your cart (requires session)
  POST /cart/items                - add item to cart (requires session)
  PUT  /cart/items/{product_name} - update item quantity (requires session)
  DELETE /cart/items/{product_name} - remove item from cart (requires session)
"""

import secrets
from typing import Annotated

from fastapi import Depends, FastAPI, Form, HTTPException, Request
from pydantic import BaseModel, Field, computed_field
from starlette.middleware.sessions import SessionMiddleware

app = FastAPI(
    title="API 8 - Session Auth",
    description="Shopping Cart API secured with session cookies.",
    version="1.0.0",
)

# SessionMiddleware stores a signed cookie containing the session ID.
# secret_key is used to sign the cookie — change this in production!
app.add_middleware(SessionMiddleware, secret_key="dev-session-secret-change-me")

# ── User store ────────────────────────────────────────────────────────────────

USERS: dict[str, str] = {
    "alice": "alicepass",
    "bob":   "bobpass",
}

# ── Session and cart stores ───────────────────────────────────────────────────

_sessions: dict[str, str] = {}   # session_id -> username
_carts: dict[str, list] = {}     # username -> list of {product_name, quantity, price}


def _reset():
    """Reset state (used in tests)."""
    global _sessions, _carts
    _sessions = {}
    _carts = {}


# ── Models ────────────────────────────────────────────────────────────────────

class CartItem(BaseModel):
    product_name: str = Field(..., min_length=1)
    quantity: int = Field(..., ge=1)
    price: float = Field(..., gt=0)


class CartItemResponse(BaseModel):
    product_name: str
    quantity: int
    price: float

    @computed_field
    @property
    def line_total(self) -> float:
        return round(self.quantity * self.price, 2)


class CartResponse(BaseModel):
    username: str
    items: list[CartItemResponse]

    @computed_field
    @property
    def total(self) -> float:
        return round(sum(i.quantity * i.price for i in self.items), 2)


class QuantityUpdate(BaseModel):
    quantity: int = Field(..., ge=1)


# ── Dependency ────────────────────────────────────────────────────────────────

def get_session_user(request: Request) -> str:
    """
    Read the session cookie and look up the session ID in _sessions.
    Returns the username. Raises 401 if not logged in.
    """
    session_id = request.session.get("session_id")
    if not session_id or session_id not in _sessions:
        raise HTTPException(status_code=401, detail="Not authenticated — please log in first")
    return _sessions[session_id]


# ── Public routes ─────────────────────────────────────────────────────────────

@app.get("/", summary="Public welcome page")
def root():
    return {
        "message": "Welcome to the Shopping Cart API!",
        "login_hint": "POST to /login with form fields: username and password",
    }


# ── Auth routes ───────────────────────────────────────────────────────────────

@app.post("/login", summary="Log in and start a session")
def login(
    request: Request,
    username: Annotated[str, Form()],
    password: Annotated[str, Form()],
):
    """
    Accepts form data (not JSON).
    On success: creates a session ID, stores it, sets a cookie.
    """
    stored_password = USERS.get(username)
    if not stored_password or password != stored_password:
        raise HTTPException(status_code=401, detail="Invalid username or password")

    session_id = secrets.token_urlsafe(32)
    _sessions[session_id] = username
    request.session["session_id"] = session_id

    if username not in _carts:
        _carts[username] = []

    return {"message": f"Logged in as {username}", "username": username}


@app.post("/logout", summary="Log out and clear the session")
def logout(request: Request, username: str = Depends(get_session_user)):
    session_id = request.session.get("session_id")
    if session_id in _sessions:
        del _sessions[session_id]
    request.session.clear()
    return {"message": "Logged out successfully"}


# ── Cart routes ───────────────────────────────────────────────────────────────

def _get_cart(username: str) -> CartResponse:
    items = _carts.get(username, [])
    return CartResponse(
        username=username,
        items=[CartItemResponse(**i) for i in items],
    )


@app.get("/cart", response_model=CartResponse, summary="View your cart")
def view_cart(username: str = Depends(get_session_user)):
    return _get_cart(username)


@app.post("/cart/items", response_model=CartResponse, summary="Add item to cart")
def add_item(body: CartItem, username: str = Depends(get_session_user)):
    cart = _carts.setdefault(username, [])
    # If item already exists, increase quantity
    for item in cart:
        if item["product_name"] == body.product_name:
            item["quantity"] += body.quantity
            return _get_cart(username)
    cart.append(body.model_dump())
    return _get_cart(username)


@app.put(
    "/cart/items/{product_name}",
    response_model=CartResponse,
    summary="Update item quantity",
)
def update_item(
    product_name: str,
    body: QuantityUpdate,
    username: str = Depends(get_session_user),
):
    cart = _carts.get(username, [])
    for item in cart:
        if item["product_name"] == product_name:
            item["quantity"] = body.quantity
            return _get_cart(username)
    raise HTTPException(status_code=404, detail=f"'{product_name}' not in cart")


@app.delete(
    "/cart/items/{product_name}",
    response_model=CartResponse,
    summary="Remove item from cart",
)
def remove_item(product_name: str, username: str = Depends(get_session_user)):
    cart = _carts.get(username, [])
    original_len = len(cart)
    _carts[username] = [i for i in cart if i["product_name"] != product_name]
    if len(_carts[username]) == original_len:
        raise HTTPException(status_code=404, detail=f"'{product_name}' not in cart")
    return _get_cart(username)
