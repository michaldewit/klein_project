# API 6 — HTTP Basic Authentication

## What You Will Learn

By the end of this guide you will understand:

- What HTTP Basic Auth is and exactly how it travels over the wire
- Why Base64 is **not** encryption and why that matters
- How FastAPI's `HTTPBasic` and `HTTPBasicCredentials` handle all the boilerplate for you
- Why `secrets.compare_digest()` exists and why `==` is dangerous for passwords
- What the `WWW-Authenticate` response header does in browsers
- How to build a dependency chain for role-based access control (reader vs. librarian)
- Why route declaration order matters when you have path parameters

---

## How HTTP Basic Auth Works

Every single HTTP request that uses Basic Auth carries the credentials directly in a header:

```
Authorization: Basic YWxpY2U6YWxpY2VwYXNz
```

That long string after `Basic` is just the username and password joined with a colon, then encoded as Base64:

```
alice:alicepass  →  base64  →  YWxpY2U6YWxpY2VwYXNz
```

**A good analogy:** Imagine every letter you send has a sticky note on the envelope that says "From: alice, Password: alicepass". You write that note on *every* letter, not just the first one. The recipient reads the note, checks it against their records, and only then opens the envelope.

This means:
- No login page — credentials go with every request.
- No session — the server never remembers you between requests.
- Every request is independently authenticated.

---

## Base64 is NOT Encryption

This is the most important safety point in this whole guide. Base64 is a *text encoding*, not a security mechanism. Anyone who can see the header can decode it in seconds.

Try it yourself in Python:

```python
import base64

# Decode the example from the Authorization header
encoded = "YWxpY2U6YWxpY2VwYXNz"
decoded = base64.b64decode(encoded).decode("utf-8")
print(decoded)   # alice:alicepass
```

The password is right there, completely readable.

**This is why HTTPS is non-negotiable.** HTTPS encrypts the entire HTTP request (including all headers) in transit so that only the server can read it. If you run Basic Auth over plain HTTP, anyone sitting between the client and server — on the same Wi-Fi network, for example — can read your users' passwords.

> Rule of thumb: Basic Auth + HTTPS = acceptable for simple APIs. Basic Auth + HTTP = never do this.

---

## FastAPI's HTTPBasic

FastAPI makes Basic Auth almost effortless. You declare a security scheme once and then request credentials in any dependency.

```python
from fastapi.security import HTTPBasic, HTTPBasicCredentials

security = HTTPBasic()
```

That one line creates the scheme. FastAPI uses it to:
1. Parse the `Authorization: Basic ...` header on incoming requests.
2. Decode the Base64 string and split on the colon.
3. Populate an `HTTPBasicCredentials` object with `.username` and `.password`.

You access those credentials by declaring them as a dependency parameter:

```python
from typing import Annotated
from fastapi import Depends

def get_current_user(
    credentials: Annotated[HTTPBasicCredentials, Depends(security)],
) -> dict:
    # credentials.username  →  "alice"
    # credentials.password  →  "alicepass"
    ...
```

FastAPI handles the header parsing, the Base64 decoding, and the error response if the header is missing — you just write the logic that decides whether the credentials are valid.

---

## `secrets.compare_digest()` vs `==`

Here is the validation code from the API:

```python
password_correct = secrets.compare_digest(
    credentials.password.encode("utf-8"),
    user["password"].encode("utf-8"),
)
```

Why not just write `credentials.password == user["password"]`? Because `==` is vulnerable to a **timing attack**.

Here is the simple explanation:

- Python's `==` operator compares strings character by character and *stops as soon as it finds a mismatch*.
- Comparing `"wrong"` against `"alicepass"` returns `False` after checking only the first character.
- Comparing `"alicepasy"` (one character off at the end) returns `False` much later.

A sophisticated attacker can send thousands of password guesses and measure how long each comparison takes. A slightly slower response means they got more characters right. Over many attempts they can figure out the correct password one character at a time — without ever triggering a lockout.

`secrets.compare_digest()` **always takes exactly the same amount of time** regardless of where the first mismatch is. The timing signal disappears completely.

> Simple rule: for any security-critical comparison (passwords, tokens, API keys), always use `secrets.compare_digest()`.

Note that `compare_digest` requires `bytes` arguments, which is why both strings are `.encode("utf-8")` first.

---

## The WWW-Authenticate Header

When credentials are wrong (or missing), the API raises a `401` with a special header:

```python
raise HTTPException(
    status_code=401,
    detail="Invalid username or password",
    headers={"WWW-Authenticate": "Basic"},
)
```

The `WWW-Authenticate: Basic` header is a standardised signal to the HTTP client that says: "I need credentials, and Basic Auth is the method I accept."

Web browsers react to this header by automatically popping up a login dialog box — the old-school grey popup asking for username and password. Once you fill it in, the browser attaches the `Authorization: Basic ...` header to the request automatically.

Non-browser clients (Postman, Python scripts, mobile apps) simply read the header and know they need to add credentials. Without this header, many clients would not know what kind of authentication is required.

---

## Role-Based Access with Basic Auth

This API has two roles: `reader` (can view books) and `librarian` (can also add and delete books). The `USERS` dictionary stores both the password and the role:

```python
USERS: dict[str, dict] = {
    "alice": {"password": "alicepass", "role": "reader"},
    "bob":   {"password": "bobpass",   "role": "reader"},
    "admin": {"password": "adminpass", "role": "librarian"},
}
```

The role-checking logic is split into two layered dependencies:

**Layer 1 — `get_current_user`:** validates credentials and returns the user dict (including their role). Any authenticated user passes this check.

**Layer 2 — `require_librarian`:** calls `get_current_user` as its own dependency, then checks the role. If the role is not `"librarian"`, it raises `403 Forbidden`.

```python
def require_librarian(user: dict = Depends(get_current_user)) -> dict:
    if user["role"] != "librarian":
        raise HTTPException(status_code=403, detail="Librarian access required")
    return user
```

Endpoint usage is then clean and self-documenting:

```python
# Any authenticated user can list books
@app.get("/books")
def list_books(user: dict = Depends(get_current_user)):
    ...

# Only librarians can add books
@app.post("/books")
def create_book(body: BookCreate, user: dict = Depends(require_librarian)):
    ...
```

This pattern — a chain of `Depends()` calls — is one of FastAPI's most powerful features. You can build up as many layers as you need (`require_admin`, `require_premium`, etc.) and each layer simply wraps the one below it.

---

## Route Declaration Order Matters

The API has both `/books/search` and `/books/{book_id}`. Notice the comment in the source:

```python
# IMPORTANT: /books/search must be declared BEFORE /books/{book_id}
# Otherwise FastAPI would match the literal string "search" as a book_id.
@app.get("/books/search", ...)
def search_books(...):
    ...

@app.get("/books/{book_id}", ...)
def get_book(book_id: int, ...):
    ...
```

FastAPI (and the underlying Starlette router) tests routes in the order they were registered. When a request arrives for `GET /books/search`, FastAPI tries each route pattern top to bottom:

1. `/books/search` — matches! Use `search_books`.
2. Never reaches `/books/{book_id}`.

If you declared them in the *wrong* order:

1. `/books/{book_id}` — matches `search` as a book ID, tries to convert `"search"` to `int`, and raises a `422 Unprocessable Entity`.
2. Never reaches the intended search handler.

**General rule:** always declare specific (literal) paths before parameterised paths that share the same prefix.

---

## Code Walkthrough

Let's trace a complete request through the system.

### Dependency chain

```
HTTPBasic (scheme)
    └── get_current_user (validates credentials, returns user dict)
            └── require_librarian (checks role, used by librarian-only routes)
```

### GET /books/search?title=harry (reader request)

1. FastAPI receives the request and sees that `search_books` needs `Depends(get_current_user)`.
2. It reads the `Authorization` header and calls `HTTPBasic` to parse it.
3. `get_current_user` runs: looks up `credentials.username` in `USERS`, calls `secrets.compare_digest()` to check the password.
4. If valid, returns `{"username": "alice", "role": "reader"}`.
5. `search_books` receives the user dict (it does not use it, but the dependency ran — request is authenticated).
6. Filters `_books` for entries where `"harry"` appears (case-insensitive) in the title.
7. Returns the matching list.

### POST /books (librarian request)

1. FastAPI sees that `create_book` needs `Depends(require_librarian)`.
2. `require_librarian` itself depends on `get_current_user`, so that runs first (same credential check as above).
3. `require_librarian` receives the user dict and checks `user["role"] == "librarian"`.
4. If role is `"reader"`, raises `403` immediately — `create_book` never runs.
5. If role is `"librarian"`, returns the user dict.
6. `create_book` runs, assigns the next `_book_id`, stores the new book, returns it.

### DELETE /books/{book_id} (reader attempt)

Same flow as POST, but `require_librarian` raises `403` at step 4. The book is never touched.

---

## Testing in Postman

1. **Open Postman** and create a new request.
2. Set the method and URL, for example: `GET http://localhost:8000/books`.
3. Click the **Authorization** tab.
4. In the **Type** dropdown, select **Basic Auth**.
5. Enter `alice` in the **Username** field and `alicepass` in the **Password** field.
6. Click **Send**. Postman automatically encodes the credentials and adds the `Authorization: Basic ...` header.

Try a librarian action with a reader account:
- Change the URL to `POST http://localhost:8000/books`.
- Keep the same alice credentials.
- Add a JSON body: `{"title": "Dune", "author": "Herbert", "isbn": "123", "available": true}`.
- Send — you should receive a `403 Forbidden`.

Now switch credentials to `admin` / `adminpass` and send again — the book is created.

To see the raw header Postman is sending, click **Code** (the `</>` icon) and choose **HTTP** — you will see the `Authorization: Basic ...` line at the top.
