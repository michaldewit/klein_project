# Exercises — API 8: Session Auth

Run the API: `uvicorn apis.api8_session_auth.main:app --reload --port 8008`

Credentials: `alice` / `alicepass`, `bob` / `bobpass`

---

## Exercise 1 (Easy) — Cart item count

**Task:** Add `GET /cart/count` that returns two numbers:
- `item_count` — the number of **distinct products** in the cart
- `total_quantity` — the sum of all quantities across all products

Response: `{"item_count": 2, "total_quantity": 7}`

<details>
<summary>Answer</summary>

```python
@app.get("/cart/count", summary="Count items in cart")
def cart_count(username: str = Depends(get_session_user)):
    cart = _carts.get(username, [])
    return {
        "item_count": len(cart),
        "total_quantity": sum(item["quantity"] for item in cart),
    }
```

</details>

---

## Exercise 2 (Easy) — Empty the cart

**Task:** Add `DELETE /cart` (no product name) that removes **all** items from the cart but keeps the user logged in. Return a confirmation message.

Response: `{"message": "Cart cleared", "username": "alice"}`

<details>
<summary>Answer</summary>

```python
@app.delete("/cart", summary="Clear the entire cart")
def clear_cart(username: str = Depends(get_session_user)):
    _carts[username] = []
    return {"message": "Cart cleared", "username": username}
```

**Test it:** Add some items → `DELETE /cart` → `GET /cart` → empty list, but `GET /cart` still works (still logged in).

</details>

---

## Exercise 3 (Medium) — Maximum quantity limit

**Task:** Add a validation rule: a single product cannot have more than **99** units in the cart. If adding an item would exceed this, raise a 400 Bad Request with a helpful message.

This should work both when:
- Adding a new item with `quantity > 99`
- Adding to an existing item where the **total** would exceed 99

<details>
<summary>Answer</summary>

```python
MAX_QUANTITY = 99

@app.post("/cart/items", response_model=CartResponse, summary="Add item to cart")
def add_item(body: CartItem, username: str = Depends(get_session_user)):
    cart = _carts.setdefault(username, [])

    for item in cart:
        if item["product_name"] == body.product_name:
            new_quantity = item["quantity"] + body.quantity
            if new_quantity > MAX_QUANTITY:          # ← add this check
                raise HTTPException(
                    status_code=400,
                    detail=f"Cannot exceed {MAX_QUANTITY} units of '{body.product_name}'"
                )
            item["quantity"] = new_quantity
            return _get_cart(username)

    if body.quantity > MAX_QUANTITY:                 # ← and this one
        raise HTTPException(
            status_code=400,
            detail=f"Cannot exceed {MAX_QUANTITY} units of '{body.product_name}'"
        )

    cart.append(body.model_dump())
    return _get_cart(username)
```

</details>

---

## Exercise 4 (Medium) — Checkout

**Task:** Add `POST /cart/checkout` that:
1. Requires the user to be logged in (session cookie)
2. Returns 400 if the cart is empty
3. Calculates the total price
4. Clears the cart (but does NOT log out)
5. Returns a checkout summary

Response:
```json
{
  "message": "Purchase complete!",
  "username": "alice",
  "items_purchased": 3,
  "total_paid": 12.50
}
```

<details>
<summary>Answer</summary>

```python
@app.post("/cart/checkout", summary="Purchase cart contents")
def checkout(username: str = Depends(get_session_user)):
    cart = _carts.get(username, [])
    if not cart:
        raise HTTPException(status_code=400, detail="Cart is empty — nothing to purchase")

    total = round(sum(i["quantity"] * i["price"] for i in cart), 2)
    items_purchased = sum(i["quantity"] for i in cart)

    # Clear the cart after checkout
    _carts[username] = []

    return {
        "message": "Purchase complete!",
        "username": username,
        "items_purchased": items_purchased,
        "total_paid": total,
    }
```

**Test it:** Add several items → `POST /cart/checkout` → `GET /cart` shows empty cart, but `GET /cart` still works (session active).

</details>

---

## Exercise 5 (Hard) — Sessions vs JWT: understanding the tradeoff

**Task:** This is a conceptual exercise with code.

Currently, `POST /logout` deletes the session from `_sessions`:

```python
if session_id in _sessions:
    del _sessions[session_id]
```

**Question:** If the server restarts (or crashes), what happens to all active sessions? Try it:

1. Login → get session cookie
2. Stop the server (`Ctrl+C`)
3. Restart the server
4. Try `GET /cart` with the same cookie

**Expected result:** 401 — because `_sessions` is an in-memory dict that was wiped when the server stopped. The cookie still exists in Postman but the server no longer recognizes the session ID.

**Now compare with JWT (API 7):**

1. Login → get a JWT token
2. Stop the server
3. Restart the server
4. Try `GET /users/me` with the same token

**Expected result:** 200 — because JWTs are self-contained. The server doesn't store anything. Any server that knows the `SECRET_KEY` can verify the token.

**Write a comment** in `apis/api8_session_auth/main.py` explaining this tradeoff:

<details>
<summary>Answer (comment to add to main.py)</summary>

```python
# _sessions stores active sessions in memory.
# TRADEOFF vs JWT:
#
# Sessions (this API):
#   + Instant logout: delete from _sessions and the session is immediately invalid
#   + Session data (e.g. the cart) stays on the server — the cookie is just an ID
#   - Server restart clears all sessions — users must log in again
#   - Harder to scale: multiple servers need a shared session store (e.g. Redis)
#
# JWT (API 7):
#   + Stateless: any server can verify any token — easy to scale
#   + Server restart has no effect on tokens
#   - No instant logout: a stolen token stays valid until it expires
#   - Token data is client-side — anyone can decode it (but not forge it)
#
# Real-world choice:
#   - Use sessions for traditional web apps where instant logout matters
#   - Use JWTs for APIs, mobile apps, microservices where scalability matters
_sessions: dict[str, str] = {}
```

</details>
