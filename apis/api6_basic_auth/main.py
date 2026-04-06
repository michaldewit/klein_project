"""
API 6 - HTTP Basic Authentication: Library Books API
Goal: Learn HTTP Basic Auth — credentials in every request header, role-based access.

How it works:
  The client sends "Authorization: Basic <base64(username:password)>" with every request.
  FastAPI's HTTPBasic extracts and decodes this automatically.
  We compare the password safely using secrets.compare_digest() to prevent timing attacks.

Roles:
  reader    — can view and search books, check out / return books
  librarian — everything a reader can do, plus add and delete books

Users (for learning — in real apps, store hashed passwords in a database):
  alice / alicepass   -> reader
  bob   / bobpass     -> reader
  admin / adminpass   -> librarian

Endpoints:
  GET  /                              - public welcome message
  GET  /books                        - list all books (reader+)
  GET  /books/search?title=          - search by title substring (reader+)
  GET  /books/{book_id}              - get a single book (reader+)
  POST /books                        - add a book (librarian only)
  DELETE /books/{book_id}            - remove a book (librarian only)
  PATCH /books/{book_id}/checkout    - mark as checked out (reader+)
  PATCH /books/{book_id}/return      - mark as available (reader+)
"""

import secrets
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from pydantic import BaseModel, Field

app = FastAPI(
    title="API 6 - HTTP Basic Auth",
    description="Library Books API secured with HTTP Basic Authentication.",
    version="1.0.0",
)

security = HTTPBasic()

# ── User store ────────────────────────────────────────────────────────────────

USERS: dict[str, dict] = {
    "alice": {"password": "alicepass", "role": "reader"},
    "bob":   {"password": "bobpass",   "role": "reader"},
    "admin": {"password": "adminpass", "role": "librarian"},
}

# ── In-memory book store ──────────────────────────────────────────────────────

_books: dict[int, dict] = {}
_book_id: int = 1


def _reset():
    """Reset state (used in tests)."""
    global _books, _book_id
    _books = {}
    _book_id = 1


# ── Models ────────────────────────────────────────────────────────────────────

class BookCreate(BaseModel):
    title: str = Field(..., min_length=1)
    author: str = Field(..., min_length=1)
    isbn: str = Field(..., min_length=1)
    available: bool = True


class Book(BaseModel):
    id: int
    title: str
    author: str
    isbn: str
    available: bool


# ── Dependencies ──────────────────────────────────────────────────────────────

def get_current_user(
    credentials: Annotated[HTTPBasicCredentials, Depends(security)],
) -> dict:
    """
    Validate Basic Auth credentials.
    Uses secrets.compare_digest() to prevent timing attacks — never use == for passwords.
    Raises 401 with WWW-Authenticate header so browsers show a login dialog.
    """
    user = USERS.get(credentials.username)
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Invalid username or password",
            headers={"WWW-Authenticate": "Basic"},
        )
    password_correct = secrets.compare_digest(
        credentials.password.encode("utf-8"),
        user["password"].encode("utf-8"),
    )
    if not password_correct:
        raise HTTPException(
            status_code=401,
            detail="Invalid username or password",
            headers={"WWW-Authenticate": "Basic"},
        )
    return {"username": credentials.username, "role": user["role"]}


def require_librarian(user: dict = Depends(get_current_user)) -> dict:
    """Only librarians may proceed. Readers get 403 Forbidden."""
    if user["role"] != "librarian":
        raise HTTPException(status_code=403, detail="Librarian access required")
    return user


# ── Public routes ─────────────────────────────────────────────────────────────

@app.get("/", summary="Public welcome")
def root():
    return {
        "message": "Welcome to the Library API!",
        "hint": "Use Basic Auth with username:password. Try alice:alicepass or admin:adminpass",
    }


# ── Reader+ routes ────────────────────────────────────────────────────────────

@app.get("/books", response_model=list[Book], summary="List all books")
def list_books(user: dict = Depends(get_current_user)):
    return list(_books.values())


# IMPORTANT: /books/search must be declared BEFORE /books/{book_id}
# Otherwise FastAPI would match the literal string "search" as a book_id.
@app.get("/books/search", response_model=list[Book], summary="Search books by title")
def search_books(
    title: str = "",
    user: dict = Depends(get_current_user),
):
    """Case-insensitive substring search on title. Returns empty list (not 404) if no matches."""
    results = [
        b for b in _books.values()
        if title.lower() in b["title"].lower()
    ]
    return results


@app.get("/books/{book_id}", response_model=Book, summary="Get a single book")
def get_book(book_id: int, user: dict = Depends(get_current_user)):
    if book_id not in _books:
        raise HTTPException(status_code=404, detail=f"Book {book_id} not found")
    return _books[book_id]


@app.patch("/books/{book_id}/checkout", response_model=Book, summary="Check out a book")
def checkout_book(book_id: int, user: dict = Depends(get_current_user)):
    if book_id not in _books:
        raise HTTPException(status_code=404, detail=f"Book {book_id} not found")
    if not _books[book_id]["available"]:
        raise HTTPException(status_code=409, detail="Book is already checked out")
    _books[book_id]["available"] = False
    return _books[book_id]


@app.patch("/books/{book_id}/return", response_model=Book, summary="Return a book")
def return_book(book_id: int, user: dict = Depends(get_current_user)):
    if book_id not in _books:
        raise HTTPException(status_code=404, detail=f"Book {book_id} not found")
    if _books[book_id]["available"]:
        raise HTTPException(status_code=409, detail="Book is already available")
    _books[book_id]["available"] = True
    return _books[book_id]


# ── Librarian-only routes ─────────────────────────────────────────────────────

@app.post("/books", response_model=Book, status_code=201, summary="Add a book (librarian)")
def create_book(body: BookCreate, user: dict = Depends(require_librarian)):
    global _book_id
    book = {"id": _book_id, **body.model_dump()}
    _books[_book_id] = book
    _book_id += 1
    return book


@app.delete("/books/{book_id}", status_code=204, summary="Delete a book (librarian)")
def delete_book(book_id: int, user: dict = Depends(require_librarian)):
    if book_id not in _books:
        raise HTTPException(status_code=404, detail=f"Book {book_id} not found")
    del _books[book_id]
