# Exercises — API 6: HTTP Basic Auth

Run the API while working: `uvicorn apis.api6_basic_auth.main:app --reload --port 8006`

Use these credentials in Postman (Authorization tab → Basic Auth):
- Reader: `alice` / `alicepass`
- Librarian: `admin` / `adminpass`

---

## Exercise 1 (Easy) — List only available books

**Task:** Add `GET /books/available` that returns only books where `available=True`. Requires any valid user (reader or librarian).

**Important:** Declare this route **above** `GET /books/{book_id}` in the file — otherwise FastAPI will try to match "available" as an integer book ID and fail.

**Hint:** Filter `_books.values()` with a list comprehension.

<details>
<summary>Answer</summary>

```python
# Add this BEFORE the get_book endpoint:
@app.get("/books/available", response_model=list[Book], summary="List available books")
def list_available_books(user: dict = Depends(get_current_user)):
    return [b for b in _books.values() if b["available"]]
```

**Test it:** Add 2 books, check one out, then `GET /books/available` — only the unchecked book appears.

</details>

---

## Exercise 2 (Medium) — Add a `GET /me` endpoint

**Task:** Add `GET /me` that returns the currently authenticated user's username and role.

**Hint:** Use `Depends(get_current_user)` — the user dict already has `username` and `role`.

<details>
<summary>Answer</summary>

```python
@app.get("/me", summary="Get your own profile")
def get_me(user: dict = Depends(get_current_user)):
    return {"username": user["username"], "role": user["role"]}
```

**Test it in Postman:**
- With alice's credentials → `{"username": "alice", "role": "reader"}`
- With admin's credentials → `{"username": "admin", "role": "librarian"}`
- Without credentials → 401

</details>

---

## Exercise 3 (Medium) — Add a `manager` role

**Task:** Add a third role `"manager"` with a new user `"manager"` / `"managerpass"`. Managers can:
- Do everything readers can (view, search, checkout, return)
- Create new books (like librarians)
- But **cannot** delete books

**Hint:** Add to `USERS`, create a new `require_manager_or_librarian` dependency for `POST /books`, and keep `DELETE /books/{id}` using `require_librarian` only.

<details>
<summary>Answer</summary>

```python
# 1. Add the user
USERS: dict[str, dict] = {
    "alice":   {"password": "alicepass",   "role": "reader"},
    "bob":     {"password": "bobpass",     "role": "reader"},
    "admin":   {"password": "adminpass",   "role": "librarian"},
    "manager": {"password": "managerpass", "role": "manager"},  # ← new
}

# 2. Add a new dependency
def require_manager_or_librarian(user: dict = Depends(get_current_user)) -> dict:
    if user["role"] not in ("manager", "librarian"):
        raise HTTPException(status_code=403, detail="Manager or librarian access required")
    return user

# 3. Change POST /books to use the new dependency
@app.post("/books", response_model=Book, status_code=201)
def create_book(body: BookCreate, user: dict = Depends(require_manager_or_librarian)):
    ...

# DELETE /books/{id} stays with require_librarian (no change)
```

**Test it:** Manager can `POST /books` (201) but not `DELETE /books/{id}` (403).

</details>

---

## Exercise 4 (Hard) — Why doesn't Basic Auth have a logout?

**Task:** This is a conceptual exercise — no new code to write, but a `POST /logout` to implement and think through.

Try adding this endpoint:

```python
@app.post("/logout")
def logout(user: dict = Depends(get_current_user)):
    return {"message": f"Goodbye, {user['username']}!"}
```

1. Call `POST /logout` successfully in Postman.
2. Now try `GET /books` with the same credentials. Does it still work?

**Why does it still work?** Basic Auth sends credentials with **every request** — the server never "remembers" you between requests. There is no session to destroy. Real logout requires either:
- Removing the key from `USERS` (for API keys)
- Using sessions or tokens (APIs 7 and 8)

**Document your findings:** Add a comment in the code explaining why the "logout" is just cosmetic for Basic Auth:

<details>
<summary>Answer</summary>

```python
@app.post("/logout", summary="Logout (cosmetic only for Basic Auth)")
def logout(user: dict = Depends(get_current_user)):
    # NOTE: This logout is cosmetic only.
    # HTTP Basic Auth is stateless — credentials are sent with every request.
    # The server has no session to destroy. The browser caches credentials
    # and will continue to send them until the browser is closed or the
    # user manually clears the saved password.
    # For real logout capability, use sessions (API 8) or tokens (API 7).
    return {"message": f"Goodbye, {user['username']}! (credentials still active)"}
```

</details>

---

## Exercise 5 (Hard) — Partial book update for librarians

**Task:** Add `PATCH /books/{book_id}` for librarians to partially update a book's `title`, `author`, or `isbn`. Only fields provided should change. The `available` field cannot be changed via this endpoint (use `/checkout` and `/return` for that).

<details>
<summary>Answer</summary>

```python
class BookPatch(BaseModel):
    title: Optional[str] = Field(default=None, min_length=1)
    author: Optional[str] = Field(default=None, min_length=1)
    isbn: Optional[str] = Field(default=None, min_length=1)

@app.patch("/books/{book_id}", response_model=Book, summary="Partially update a book (librarian)")
def patch_book(book_id: int, body: BookPatch, user: dict = Depends(require_librarian)):
    if book_id not in _books:
        raise HTTPException(status_code=404, detail=f"Book {book_id} not found")
    updates = body.model_dump(exclude_none=True)
    _books[book_id].update(updates)
    return _books[book_id]
```

**Test it:**
```json
PATCH /books/1  (with admin credentials)
{"title": "New Title"}
```
Only the title changes. Author and ISBN stay the same.

</details>
