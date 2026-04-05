"""
API 4 - Auth-Protected API
Goal: Learn API security with API key authentication via request headers.

Concept: Some routes are public, others require a valid X-API-Key header.
         Roles: "reader" key has read-only access; "admin" key has full access.

Endpoints (public):
  GET  /public          - no auth needed
  GET  /public/info     - no auth needed

Endpoints (reader or admin key required):
  GET  /protected/data  - returns protected data

Endpoints (admin key only):
  POST /admin/notes     - create a note
  GET  /admin/notes     - list all notes
  DELETE /admin/notes/{id} - delete a note

HTTP responses:
  401 Unauthorized - missing or invalid API key
  403 Forbidden    - valid key but insufficient role
"""

from fastapi import FastAPI, Header, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Optional, Annotated

app = FastAPI(
    title="API 4 - Auth Protected",
    description="Learn API key authentication, roles, and header-based security.",
    version="1.0.0",
)

# ── Config ─────────────────────────────────────────────────────────────────────

# In real applications these would come from environment variables / a database
VALID_KEYS: dict[str, str] = {
    "reader-key-123": "reader",
    "admin-key-456": "admin",
}

# In-memory note store
_notes: dict[int, dict] = {}
_note_id: int = 1


def _reset():
    """Reset state (used in tests)."""
    global _notes, _note_id
    _notes = {}
    _note_id = 1


# ── Dependencies ──────────────────────────────────────────────────────────────

def get_api_key(x_api_key: Annotated[Optional[str], Header()] = None) -> str:
    """Validate that an API key header is present and known."""
    if not x_api_key:
        raise HTTPException(status_code=401, detail="Missing X-API-Key header")
    if x_api_key not in VALID_KEYS:
        raise HTTPException(status_code=401, detail="Invalid API key")
    return x_api_key


def require_reader(x_api_key: str = Depends(get_api_key)) -> str:
    """Allow both reader and admin roles."""
    role = VALID_KEYS[x_api_key]
    if role not in ("reader", "admin"):
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    return x_api_key


def require_admin(x_api_key: str = Depends(get_api_key)) -> str:
    """Allow only admin role."""
    role = VALID_KEYS[x_api_key]
    if role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return x_api_key


# ── Models ────────────────────────────────────────────────────────────────────

class NoteCreate(BaseModel):
    title: str = Field(..., min_length=1)
    body: str = Field(default="")


class Note(BaseModel):
    id: int
    title: str
    body: str


# ── Public routes ─────────────────────────────────────────────────────────────

@app.get("/public", summary="Public endpoint - no auth")
def public():
    return {"message": "This is public. Anyone can read this."}


@app.get("/public/info", summary="Public info - no auth")
def public_info():
    return {
        "api": "API 4 - Auth Protected",
        "auth_header": "X-API-Key",
        "roles": ["reader", "admin"],
    }


# ── Protected routes (reader+) ────────────────────────────────────────────────

@app.get("/protected/data", summary="Protected data - reader or admin")
def protected_data(api_key: str = Depends(require_reader)):
    role = VALID_KEYS[api_key]
    return {
        "secret": "Here is your protected data!",
        "accessed_with_role": role,
    }


# ── Admin routes ──────────────────────────────────────────────────────────────

@app.get("/admin/notes", response_model=list[Note], summary="List all notes - admin only")
def list_notes(api_key: str = Depends(require_admin)):
    return list(_notes.values())


@app.post("/admin/notes", response_model=Note, status_code=201, summary="Create a note - admin only")
def create_note(body: NoteCreate, api_key: str = Depends(require_admin)):
    global _note_id
    note = {"id": _note_id, "title": body.title, "body": body.body}
    _notes[_note_id] = note
    _note_id += 1
    return note


@app.delete("/admin/notes/{note_id}", status_code=204, summary="Delete a note - admin only")
def delete_note(note_id: int, api_key: str = Depends(require_admin)):
    if note_id not in _notes:
        raise HTTPException(status_code=404, detail=f"Note {note_id} not found")
    del _notes[note_id]
