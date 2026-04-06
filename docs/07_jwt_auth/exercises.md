# Exercises — API 7: OAuth2 + JWT

Run the API: `uvicorn apis.api7_jwt_auth.main:app --reload --port 8007`

Credentials: `alice` / `alice123` (user), `bob` / `bob123` (user), `admin` / `admin123` (admin)

---

## Exercise 1 (Easy) — Note count endpoint

**Task:** Add `GET /notes/count` that returns how many notes the current user has.

Response: `{"count": 3}`

**Hint:** Declare this route **above** `GET /notes/{note_id}`. Use `Depends(get_current_user)` and filter `_notes` by owner.

<details>
<summary>Answer</summary>

```python
# Add BEFORE the get_note endpoint:
@app.get("/notes/count", summary="Count your notes")
def count_notes(current_user: TokenData = Depends(get_current_user)):
    count = sum(1 for n in _notes.values() if n["owner"] == current_user.username)
    return {"count": count}
```

</details>

---

## Exercise 2 (Medium) — Search notes

**Task:** Add `?search=` query parameter to `GET /notes` that filters notes by a case-insensitive substring match in either the `title` or `content`.

Example: `GET /notes?search=python` returns notes where title or content contains "python".

Without `?search=`, return all notes as before.

<details>
<summary>Answer</summary>

```python
@app.get("/notes", response_model=list[Note])
def list_notes(
    current_user: TokenData = Depends(get_current_user),
    search: Optional[str] = Query(default=None),    # ← add this
):
    user_notes = [n for n in _notes.values() if n["owner"] == current_user.username]
    if search:                                       # ← add this block
        q = search.lower()
        user_notes = [
            n for n in user_notes
            if q in n["title"].lower() or q in n["content"].lower()
        ]
    return user_notes
```

</details>

---

## Exercise 3 (Medium) — Add tags to notes

**Task:** Add a `tags: list[str] = []` field to `NoteCreate` and `Note`. Notes can be created with tags like `{"title": "Python Tips", "tags": ["python", "programming"]}`.

Add `GET /notes/tagged?tag=python` that returns your notes containing that tag.

<details>
<summary>Answer</summary>

```python
class NoteCreate(BaseModel):
    title: str = Field(..., min_length=1)
    content: str = ""
    tags: list[str] = []                 # ← add this

class Note(BaseModel):
    id: int
    owner: str
    title: str
    content: str
    tags: list[str] = []                 # ← add this

# In create_note, include tags:
note = {
    "id": _note_id,
    "owner": current_user.username,
    "title": body.title,
    "content": body.content,
    "tags": body.tags,                   # ← add this
}

# New endpoint (above get_note):
@app.get("/notes/tagged", response_model=list[Note], summary="Notes by tag")
def notes_by_tag(
    tag: str = Query(...),
    current_user: TokenData = Depends(get_current_user),
):
    return [
        n for n in _notes.values()
        if n["owner"] == current_user.username and tag in n.get("tags", [])
    ]
```

</details>

---

## Exercise 4 (Hard) — Admin creates users

**Task:** Add `POST /admin/users` (admin only) that creates a new user entry in `USERS_DB` with a bcrypt-hashed password.

Request body:
```json
{"username": "charlie", "password": "charlie123", "role": "user"}
```

Return 409 Conflict if the username already exists.

<details>
<summary>Answer</summary>

```python
class UserCreate(BaseModel):
    username: str = Field(..., min_length=1)
    password: str = Field(..., min_length=6)
    role: str = Field(default="user")

@app.post("/admin/users", status_code=201, summary="Create a new user (admin only)")
def create_user(body: UserCreate, current_user: TokenData = Depends(require_admin)):
    if body.username in USERS_DB:
        raise HTTPException(status_code=409, detail=f"User '{body.username}' already exists")
    hashed = bcrypt.hashpw(body.password.encode(), bcrypt.gensalt()).decode()
    USERS_DB[body.username] = {
        "username": body.username,
        "hashed_password": hashed,
        "role": body.role,
    }
    return {"username": body.username, "role": body.role}
```

**Test it:** Login as admin → `POST /admin/users` with new user → try logging in as that user with `POST /token`.

</details>

---

## Exercise 5 (Hard) — Understand token expiry

**Task:** Demonstrate token expiry through a test (not just by waiting 30 minutes).

In `test_api7.py`, the existing test `test_expired_token_returns_401` uses `monkeypatch` to set `ACCESS_TOKEN_EXPIRE_MINUTES = -1`. Read that test and understand how it works.

Now add a new test: `test_valid_token_not_yet_expired` — create a token with `ACCESS_TOKEN_EXPIRE_MINUTES = 60` and verify it is still accepted.

<details>
<summary>Answer</summary>

```python
def test_valid_token_not_yet_expired(monkeypatch):
    import apis.api7_jwt_auth.main as m
    monkeypatch.setattr(m, "ACCESS_TOKEN_EXPIRE_MINUTES", 60)  # 60 minutes from now
    token = create_access_token({"sub": "alice", "role": "user"})
    response = client.get("/users/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert response.json()["username"] == "alice"
```

**What this teaches:** The `exp` claim in the JWT is a Unix timestamp. `jwt_decode()` in `jwt_utils.py` checks `if time.time() > exp: raise JWTError(...)`. With `-1` minutes, the expiry is in the past. With `60` minutes, it is in the future.

</details>
