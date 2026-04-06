# API 8 — Session-Based Authentication with Cookies

## What You Will Learn

- How HTTP cookies work and why browsers send them automatically
- The difference between stateful (session) and stateless (JWT) authentication
- How `SessionMiddleware` manages session data in FastAPI/Starlette
- How to store and retrieve user data across multiple requests
- How a shopping cart persists without the client re-sending cart contents each time

---

## Running the API

```bash
uvicorn apis.api8_session_auth.main:app --reload --port 8008
```

---

## How Cookies Work

A **cookie** is a small piece of data that the server sends to the browser, and the browser automatically includes in every subsequent request to the same server.

**Step 1 — Server sets a cookie in the response:**
```
HTTP/1.1 200 OK
Set-Cookie: session=abc123xyz; HttpOnly; Path=/
```

**Step 2 — Browser stores it automatically**

**Step 3 — Browser sends it with every future request:**
```
GET /cart HTTP/1.1
Cookie: session=abc123xyz
```

You do not need JavaScript to use cookies — the browser handles everything.

**Analogy:** A loyalty card that your wallet presents automatically every time you enter the shop.

---

## Sessions vs JWT Tokens

Both sessions and JWTs authenticate users, but they store state differently:

| | Session Cookie | JWT Token |
|--|--|--|
| **Where data lives** | On the server (in `_sessions` dict) | In the token (client-side) |
| **What cookie/header contains** | An opaque ID (a random string) | The actual user data (encoded) |
| **Server state needed** | Yes — must look up session ID | No — token is self-contained |
| **Logout** | Instant — delete the session from server | Difficult — token stays valid until expiry |
| **Scalability** | Harder (all servers need to share sessions) | Easier (any server can verify any token) |
| **Best for** | Traditional web apps, when you need instant revocation | APIs, SPAs, mobile apps |

---

## SessionMiddleware

```python
from starlette.middleware.sessions import SessionMiddleware

app.add_middleware(SessionMiddleware, secret_key="dev-session-secret-change-me")
```

This **middleware** wraps every request and response:
- On every **request**: reads the `session` cookie, decodes and verifies its signature using `secret_key`, and makes the data available as `request.session` (a dictionary)
- On every **response**: if `request.session` was modified, encodes it, signs it, and sets the `Set-Cookie` header

The `secret_key` is used to sign the cookie with HMAC. If someone tampers with the cookie, the signature check fails and the session is ignored.

> **Important:** Change the `secret_key` in production! Anyone who knows the key can forge sessions.

---

## The `request.session` Dictionary

Once `SessionMiddleware` is added, any route handler that takes a `Request` parameter can use `request.session`:

```python
# On login — store data in the session:
request.session["session_id"] = session_id
request.session["username"] = "alice"

# On a protected route — read from the session:
session_id = request.session.get("session_id")

# On logout — clear everything:
request.session.clear()
```

The session dictionary is automatically saved to the cookie when the response is sent.

---

## The Session Store Pattern

In this API, session IDs are stored in a server-side dict as well:

```python
_sessions: dict[str, str] = {}   # session_id -> username
```

```python
@app.post("/login")
def login(request: Request, username: str = Form(...), password: str = Form(...)):
    # 1. Verify credentials
    ...
    # 2. Create a random, unpredictable session ID
    session_id = secrets.token_urlsafe(32)
    # 3. Store it server-side
    _sessions[session_id] = username
    # 4. Write it into the cookie
    request.session["session_id"] = session_id
    return {"message": f"Logged in as {username}"}
```

The dependency that protects routes:

```python
def get_session_user(request: Request) -> str:
    session_id = request.session.get("session_id")
    if not session_id or session_id not in _sessions:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return _sessions[session_id]  # returns "alice"
```

---

## Form Data vs JSON

The `POST /login` endpoint accepts **form data**, not JSON:

```python
@app.post("/login")
def login(
    request: Request,
    username: Annotated[str, Form()],     # form field, not JSON
    password: Annotated[str, Form()],     # form field, not JSON
):
```

Form data looks like `username=alice&password=alicepass` in the request body. This is the standard format for HTML login forms.

In Postman: Body → **x-www-form-urlencoded** (not `raw JSON`).

> `python-multipart` must be installed for FastAPI to parse form data. We installed it at the start of this project.

---

## Shopping Cart Persistence

The cart is stored in `_carts[username]` on the server:

```python
_carts: dict[str, list] = {}   # username -> list of cart items
```

Because the session tells the server who you are on every request, the cart persists automatically:

```
Request 1: POST /cart/items  (cookie: session=abc)
           server: who is abc? → alice
           server: add apple to _carts["alice"]

Request 2: GET /cart  (cookie: session=abc — browser sent it automatically!)
           server: who is abc? → alice
           server: return _carts["alice"]  → [apple]
```

The client never needs to re-send the cart contents — the server remembers.

---

## Code Walkthrough

### `POST /login`

```python
@app.post("/login")
def login(request: Request, username: str = Form(...), password: str = Form(...)):
    stored_password = USERS.get(username)
    if not stored_password or password != stored_password:
        raise HTTPException(status_code=401, detail="Invalid username or password")

    session_id = secrets.token_urlsafe(32)   # random, unpredictable ID
    _sessions[session_id] = username         # server remembers: this ID = alice
    request.session["session_id"] = session_id  # write to cookie

    if username not in _carts:
        _carts[username] = []               # initialize empty cart

    return {"message": f"Logged in as {username}", "username": username}
```

### `POST /cart/items` — add to cart

```python
@app.post("/cart/items", response_model=CartResponse)
def add_item(body: CartItem, username: str = Depends(get_session_user)):
    cart = _carts.setdefault(username, [])
    # If item already exists, increase quantity
    for item in cart:
        if item["product_name"] == body.product_name:
            item["quantity"] += body.quantity
            return _get_cart(username)
    cart.append(body.model_dump())
    return _get_cart(username)
```

---

## Testing in Postman

**Step 1:** `POST /login` — Body → x-www-form-urlencoded → `username: alice`, `password: alicepass`
- Check the **Cookies** panel (bottom right of response area)
- You should see a `session` cookie has been set

**Step 2:** `POST /cart/items` with body:
```json
{"product_name": "Apple", "quantity": 2, "price": 1.50}
```
- The session cookie is sent automatically — you don't need to set any headers

**Step 3:** `GET /cart` — the Apple appears

**Step 4:** Open a **new request tab** with the SAME collection — the cart still shows Apple (same session)

**Step 5:** `POST /logout` — `GET /cart` in the same tab → 401

> Postman maintains a **cookie jar** per collection. Cookies received from the server are automatically sent on subsequent requests, just like a browser.
