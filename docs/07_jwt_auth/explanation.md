# API 7 — OAuth2 + JWT Authentication

## What You Will Learn

- Why stateless token-based authentication is useful
- How the OAuth2 Password Flow works step-by-step
- What a JWT is and how to read one
- How `bcrypt` protects stored passwords
- How to scope data access per user (each user only sees their own notes)

---

## Running the API

```bash
uvicorn apis.api7_jwt_auth.main:app --reload --port 8007
```

Visit `http://127.0.0.1:8007/docs` — you will see an **Authorize** button. This is the OAuth2 login built directly into Swagger UI.

---

## The Problem With Basic Auth

HTTP Basic Auth (API 6) works but has limitations:
- Your password travels over the wire with **every single request**
- There is no expiry — a leaked credential works forever until you change it
- There is no real logout — the browser caches credentials
- You cannot attach extra information to the credential (like a role or permissions)

**JWT tokens** solve all of these:
- You send your password **once** to get a token
- The token expires after a set time (30 minutes in this API)
- Leaking a token is bad, but it stops working at expiry
- The token itself contains your username and role — no database lookup needed

---

## The OAuth2 Password Flow — Step by Step

```
1. Client sends: POST /token
                 username=alice&password=alice123   (form data, not JSON)

2. Server checks credentials against USERS_DB
   Verifies password with bcrypt

3. Server creates a JWT:
   {"sub": "alice", "role": "user", "exp": 1234567890}
   Signs it with a secret key → produces a token string

4. Server returns:
   {"access_token": "eyJ...", "token_type": "bearer"}

5. Client stores the token

6. Client uses token for all future requests:
   Authorization: Bearer eyJ...

7. Server decodes the token (no database lookup!)
   Checks expiry, extracts username and role
   Allows or denies the request
```

---

## What is a JWT?

A **JWT** (JSON Web Token) looks like this:

```
eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJhbGljZSIsInJvbGUiOiJ1c2VyIiwiZXhwIjoxNjk5OTk5OTk5fQ.abc123
```

It has three parts separated by dots:

| Part | Contains | Example |
|------|----------|---------|
| **Header** (base64url) | Algorithm | `{"alg": "HS256", "typ": "JWT"}` |
| **Payload** (base64url) | Claims (your data) | `{"sub": "alice", "role": "user", "exp": 1699999999}` |
| **Signature** | Cryptographic proof | `HMAC-SHA256(header + "." + payload, secret_key)` |

The payload is **base64url encoded** — not encrypted. Anyone can decode it. But the **signature** proves the server created it and no one tampered with it.

You can decode any JWT at `https://jwt.io` to see its contents.

### Claims in This API

| Claim | Meaning |
|-------|---------|
| `sub` | Subject — the username (`"alice"`) |
| `role` | The user's role (`"user"` or `"admin"`) |
| `exp` | Expiry — Unix timestamp after which the token is invalid |

---

## Password Hashing with bcrypt

**Never store passwords as plain text.** If your database is leaked, every user's password is exposed.

Instead, store a **bcrypt hash** — a one-way transformation:

```python
import bcrypt

# When user registers or password is set:
hashed = bcrypt.hashpw("alice123".encode(), bcrypt.gensalt())
# hashed = b"$2b$12$..." (looks like random garbage)

# When user logs in:
bcrypt.checkpw("alice123".encode(), hashed)  # True
bcrypt.checkpw("wrongpass".encode(), hashed)  # False
```

You cannot reverse a bcrypt hash to get the original password. The only way to check is to run `checkpw`.

In this API, the passwords are pre-hashed in `USERS_DB` — they were computed once and pasted in, which is fine for a learning project.

---

## OAuth2PasswordBearer

```python
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/token")
```

This does two things:
1. Tells FastAPI where clients get tokens (`/token` endpoint)
2. Extracts the `Authorization: Bearer <token>` header from requests automatically
3. Adds an **Authorize** button to `/docs` so you can log in interactively in the browser

---

## The `Depends()` Chain for JWT

```python
def get_current_user(token: str = Depends(oauth2_scheme)) -> TokenData:
    try:
        payload = jwt_decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        role = payload.get("role")
        if username is None or role is None:
            raise HTTPException(401, ...)
        return TokenData(username=username, role=role)
    except JWTError:
        raise HTTPException(401, ...)
```

- `Depends(oauth2_scheme)` extracts the token string from the header
- `jwt_decode()` verifies the signature and checks expiry
- Returns `TokenData(username="alice", role="user")`

Every protected endpoint uses this dependency:
```python
@app.get("/notes")
def list_notes(current_user: TokenData = Depends(get_current_user)):
    # current_user.username = "alice"
    # current_user.role = "user"
```

---

## Per-User Data and the 403 for Other Users' Notes

Each note stores its `owner`:
```python
note = {
    "id": 1,
    "owner": "alice",   # ← who created it
    "title": "My Note",
    "content": "...",
}
```

When fetching a specific note:
```python
@app.get("/notes/{note_id}")
def get_note(note_id: int, current_user: TokenData = Depends(get_current_user)):
    if note_id not in _notes:
        raise HTTPException(status_code=404, detail="Note not found")
    note = _notes[note_id]
    if note["owner"] != current_user.username:
        raise HTTPException(status_code=403, detail="Access denied")  # ← 403, not 404!
    return note
```

Why **403** instead of 404? If you returned 404, an attacker could discover which IDs exist (by getting 404 vs 403). Returning 403 for both "exists but not yours" and "exists but not yours" prevents this **enumeration attack**.

---

## Code Walkthrough

### `POST /token` — login

```python
@app.post("/token", response_model=Token)
def login(form_data: Annotated[OAuth2PasswordRequestForm, Depends()]):
    user = USERS_DB.get(form_data.username)
    if not user or not verify_password(form_data.password, user["hashed_password"]):
        raise HTTPException(401, ...)
    token = create_access_token({"sub": user["username"], "role": user["role"]})
    return {"access_token": token, "token_type": "bearer"}
```

Note: `OAuth2PasswordRequestForm` reads **form data** (`username=alice&password=alice123`), not JSON. In Postman, use the `x-www-form-urlencoded` body type, not `raw JSON`.

### `create_access_token()` — builds the JWT

```python
def create_access_token(data: dict) -> str:
    import time
    to_encode = data.copy()
    expire = time.time() + ACCESS_TOKEN_EXPIRE_MINUTES * 60  # Unix timestamp
    to_encode["exp"] = expire
    return jwt_encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
```

---

## Testing in Postman

**Step 1:** `POST /token` — Body → x-www-form-urlencoded → `username: alice`, `password: alice123`
- Copy the `access_token` value from the response

**Step 2:** All subsequent requests → Authorization tab → Bearer Token → paste the token

**Step 3:** `GET /notes` → empty list (you have no notes yet)

**Step 4:** `POST /notes` with body `{"title": "Hello", "content": "World"}` → 201, note created

**Step 5:** Login as `bob` with a new request, get bob's token, then `GET /notes/{alice's note id}` → 403

**Swagger shortcut:** Open `/docs`, click **Authorize**, enter username and password — Swagger handles the token for all requests automatically.
