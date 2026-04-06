"""
API 7 - OAuth2 Password Flow + JWT: Personal Notes API
Goal: Learn the industry-standard token-based authentication pattern.

How it works:
  1. Client sends username + password to POST /token (one time only)
  2. Server verifies credentials and issues a short-lived JWT token
  3. Client includes token in all future requests: "Authorization: Bearer <token>"
  4. Server decodes and validates the token — NO database lookup needed (stateless!)
  5. Token expires after 30 minutes; client must log in again to get a fresh one

What is a JWT?
  A JWT has three parts separated by dots: header.payload.signature
  - header: algorithm used (HS256)
  - payload: claims like {"sub": "alice", "role": "user", "exp": 1234567890}
  - signature: cryptographic proof the server issued this token
  You can decode the first two parts at https://jwt.io (for learning purposes only!)

Users (passwords hashed with bcrypt — never store plain-text passwords):
  alice / alice123  -> role: user
  bob   / bob123   -> role: user
  admin / admin123  -> role: admin

Notes ownership:
  - Each user can only see and edit their own notes
  - Accessing another user's note returns 403 Forbidden (not 404 — prevents enumeration)
  - Admin can see ALL notes via GET /admin/notes

Endpoints:
  POST /token              - exchange credentials for JWT token (form data)
  GET  /users/me           - get your own profile from the token
  GET  /notes              - list your notes
  GET  /notes/{id}         - get a note (403 if not yours)
  POST /notes              - create a note
  PATCH /notes/{id}        - partially update your note
  DELETE /notes/{id}       - delete your note
  GET  /admin/notes        - list ALL notes (admin only)
"""

import bcrypt
from typing import Optional, Annotated

from fastapi import Depends, FastAPI, HTTPException
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel, Field

from apis.api7_jwt_auth.jwt_utils import JWTError, decode as jwt_decode, encode as jwt_encode

app = FastAPI(
    title="API 7 - OAuth2 + JWT Auth",
    description="Personal Notes API secured with OAuth2 Password Flow and JWT tokens.",
    version="1.0.0",
)

# ── Config ────────────────────────────────────────────────────────────────────

SECRET_KEY = "dev-secret-key-change-in-production-never-commit-real-keys"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# ── User store ────────────────────────────────────────────────────────────────
# Passwords are bcrypt hashes. Plain-text passwords for testing:
#   alice / alice123, bob / bob123, admin / admin123

USERS_DB: dict[str, dict] = {
    "alice": {
        "username": "alice",
        "hashed_password": "$2b$12$xMySQeVVxy/wP69mIRslku9R9Nrw43/k9NkowDtmu11.4CANvTP5W",
        "role": "user",
    },
    "bob": {
        "username": "bob",
        "hashed_password": "$2b$12$hbbAuHLka5Nrq91/DO3i8OuvCVSAadRM7Ql09mZe2hFLri5jUkgnW",
        "role": "user",
    },
    "admin": {
        "username": "admin",
        "hashed_password": "$2b$12$vhwKfrZgPtua5kjUJAZgduU4uJncQcVxjStVdCpT4SNcA.pu/YbXe",
        "role": "admin",
    },
}

# ── In-memory notes store ─────────────────────────────────────────────────────

_notes: dict[int, dict] = {}
_note_id: int = 1


def _reset():
    """Reset state (used in tests)."""
    global _notes, _note_id
    _notes = {}
    _note_id = 1


# ── Models ────────────────────────────────────────────────────────────────────

class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: str
    role: str


class NoteCreate(BaseModel):
    title: str = Field(..., min_length=1)
    content: str = ""


class Note(BaseModel):
    id: int
    owner: str
    title: str
    content: str


class NotePatch(BaseModel):
    title: Optional[str] = Field(default=None, min_length=1)
    content: Optional[str] = None


# ── Auth helpers ──────────────────────────────────────────────────────────────

def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode(), hashed.encode())


def create_access_token(data: dict) -> str:
    import time
    to_encode = data.copy()
    expire = time.time() + ACCESS_TOKEN_EXPIRE_MINUTES * 60
    to_encode["exp"] = expire
    return jwt_encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


# ── OAuth2 scheme — tells FastAPI where to look for the token ─────────────────

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/token")


# ── Dependencies ──────────────────────────────────────────────────────────────

def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]) -> TokenData:
    """Decode and validate the JWT. Raises 401 on any failure."""
    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt_decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        role: str = payload.get("role")
        if username is None or role is None:
            raise credentials_exception
        return TokenData(username=username, role=role)
    except JWTError:
        raise credentials_exception


def require_admin(current_user: TokenData = Depends(get_current_user)) -> TokenData:
    """Only admins may proceed."""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user


# ── Endpoints ─────────────────────────────────────────────────────────────────

@app.post("/token", response_model=Token, summary="Exchange credentials for a JWT token")
def login(form_data: Annotated[OAuth2PasswordRequestForm, Depends()]):
    """
    Accepts form data (not JSON): username and password fields.
    Returns a JWT bearer token valid for 30 minutes.
    """
    user = USERS_DB.get(form_data.username)
    if not user or not verify_password(form_data.password, user["hashed_password"]):
        raise HTTPException(
            status_code=401,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = create_access_token({"sub": user["username"], "role": user["role"]})
    return {"access_token": token, "token_type": "bearer"}


@app.get("/users/me", summary="Get your own profile")
def get_me(current_user: TokenData = Depends(get_current_user)):
    return {"username": current_user.username, "role": current_user.role}


@app.get("/notes", response_model=list[Note], summary="List your notes")
def list_notes(current_user: TokenData = Depends(get_current_user)):
    return [n for n in _notes.values() if n["owner"] == current_user.username]


@app.get("/notes/{note_id}", response_model=Note, summary="Get a single note")
def get_note(note_id: int, current_user: TokenData = Depends(get_current_user)):
    if note_id not in _notes:
        raise HTTPException(status_code=404, detail="Note not found")
    note = _notes[note_id]
    if note["owner"] != current_user.username:
        # Return 403, not 404 — prevents attackers from guessing which IDs exist
        raise HTTPException(status_code=403, detail="Access denied")
    return note


@app.post("/notes", response_model=Note, status_code=201, summary="Create a note")
def create_note(body: NoteCreate, current_user: TokenData = Depends(get_current_user)):
    global _note_id
    note = {
        "id": _note_id,
        "owner": current_user.username,
        "title": body.title,
        "content": body.content,
    }
    _notes[_note_id] = note
    _note_id += 1
    return note


@app.patch("/notes/{note_id}", response_model=Note, summary="Partially update your note")
def patch_note(
    note_id: int,
    body: NotePatch,
    current_user: TokenData = Depends(get_current_user),
):
    if note_id not in _notes:
        raise HTTPException(status_code=404, detail="Note not found")
    note = _notes[note_id]
    if note["owner"] != current_user.username:
        raise HTTPException(status_code=403, detail="Access denied")
    updates = body.model_dump(exclude_none=True)
    note.update(updates)
    return note


@app.delete("/notes/{note_id}", status_code=204, summary="Delete your note")
def delete_note(note_id: int, current_user: TokenData = Depends(get_current_user)):
    if note_id not in _notes:
        raise HTTPException(status_code=404, detail="Note not found")
    note = _notes[note_id]
    if note["owner"] != current_user.username:
        raise HTTPException(status_code=403, detail="Access denied")
    del _notes[note_id]


@app.get("/admin/notes", response_model=list[Note], summary="List all notes (admin only)")
def admin_list_notes(current_user: TokenData = Depends(require_admin)):
    return list(_notes.values())
