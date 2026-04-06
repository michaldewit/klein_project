"""
Tests for API 6 - HTTP Basic Auth: Library Books API

Requirements covered:
  - GET /          returns 200 without credentials
  - GET /books     returns 401 without credentials
  - GET /books     returns 401 with wrong password
  - GET /books     returns 401 with unknown username
  - GET /books     returns 200 with reader credentials
  - GET /books     returns 200 with librarian credentials
  - GET /books     initially returns empty list
  - POST /books    returns 403 with reader credentials
  - POST /books    returns 201 with librarian credentials
  - POST /books    returns correct book data
  - POST /books    validates title is not empty (422)
  - GET /books/{id} returns correct book
  - GET /books/{id} returns 404 for unknown id
  - GET /books/search?title= returns matching books case-insensitively
  - GET /books/search?title= returns empty list (not 404) when no match
  - PATCH /books/{id}/checkout sets available=False
  - PATCH /books/{id}/checkout returns 409 if already checked out
  - PATCH /books/{id}/return  sets available=True
  - PATCH /books/{id}/return  returns 409 if already available
  - DELETE /books/{id} returns 204 with librarian credentials
  - DELETE /books/{id} returns 403 with reader credentials
  - DELETE /books/{id} returns 404 for unknown id
"""

import pytest
from fastapi.testclient import TestClient
from apis.api6_basic_auth.main import app, _reset

client = TestClient(app)

READER_AUTH = ("alice", "alicepass")
LIBRARIAN_AUTH = ("admin", "adminpass")
BAD_AUTH = ("alice", "wrongpassword")
UNKNOWN_AUTH = ("nobody", "nopass")


@pytest.fixture(autouse=True)
def reset_books():
    _reset()
    yield


def make_book(title="Harry Potter", author="Rowling", isbn="978-0439708180"):
    return client.post(
        "/books",
        json={"title": title, "author": author, "isbn": isbn},
        auth=LIBRARIAN_AUTH,
    ).json()


# ── GET / (public) ────────────────────────────────────────────────────────────

def test_root_no_auth_returns_200():
    assert client.get("/").status_code == 200


def test_root_has_message():
    assert "message" in client.get("/").json()


# ── GET /books — authentication ───────────────────────────────────────────────

def test_list_books_no_auth_returns_401():
    assert client.get("/books").status_code == 401


def test_list_books_wrong_password_returns_401():
    assert client.get("/books", auth=BAD_AUTH).status_code == 401


def test_list_books_unknown_user_returns_401():
    assert client.get("/books", auth=UNKNOWN_AUTH).status_code == 401


def test_list_books_reader_returns_200():
    assert client.get("/books", auth=READER_AUTH).status_code == 200


def test_list_books_librarian_returns_200():
    assert client.get("/books", auth=LIBRARIAN_AUTH).status_code == 200


def test_list_books_initially_empty():
    assert client.get("/books", auth=READER_AUTH).json() == []


# ── POST /books ───────────────────────────────────────────────────────────────

def test_create_book_reader_returns_403():
    response = client.post(
        "/books",
        json={"title": "Dune", "author": "Herbert", "isbn": "978-0441172719"},
        auth=READER_AUTH,
    )
    assert response.status_code == 403


def test_create_book_librarian_returns_201():
    response = client.post(
        "/books",
        json={"title": "Dune", "author": "Herbert", "isbn": "978-0441172719"},
        auth=LIBRARIAN_AUTH,
    )
    assert response.status_code == 201


def test_create_book_returns_correct_data():
    data = client.post(
        "/books",
        json={"title": "Dune", "author": "Herbert", "isbn": "978-0441172719"},
        auth=LIBRARIAN_AUTH,
    ).json()
    assert data["title"] == "Dune"
    assert data["author"] == "Herbert"
    assert data["available"] is True
    assert "id" in data


def test_create_book_empty_title_returns_422():
    response = client.post(
        "/books",
        json={"title": "", "author": "Herbert", "isbn": "123"},
        auth=LIBRARIAN_AUTH,
    )
    assert response.status_code == 422


def test_create_book_no_auth_returns_401():
    response = client.post(
        "/books",
        json={"title": "Test", "author": "A", "isbn": "123"},
    )
    assert response.status_code == 401


# ── GET /books/{id} ───────────────────────────────────────────────────────────

def test_get_book_returns_correct_data():
    book = make_book()
    response = client.get(f"/books/{book['id']}", auth=READER_AUTH)
    assert response.status_code == 200
    assert response.json()["title"] == "Harry Potter"


def test_get_book_not_found_returns_404():
    assert client.get("/books/9999", auth=READER_AUTH).status_code == 404


# ── GET /books/search ─────────────────────────────────────────────────────────

def test_search_returns_matching_book():
    make_book(title="Harry Potter")
    make_book(title="Lord of the Rings")
    results = client.get("/books/search?title=harry", auth=READER_AUTH).json()
    assert len(results) == 1
    assert results[0]["title"] == "Harry Potter"


def test_search_case_insensitive():
    make_book(title="Harry Potter")
    results = client.get("/books/search?title=HARRY", auth=READER_AUTH).json()
    assert len(results) == 1


def test_search_no_match_returns_empty_list():
    make_book(title="Harry Potter")
    results = client.get("/books/search?title=Hobbit", auth=READER_AUTH).json()
    assert results == []


def test_search_no_query_returns_all():
    make_book(title="Book A")
    make_book(title="Book B")
    results = client.get("/books/search", auth=READER_AUTH).json()
    assert len(results) == 2


# ── PATCH /books/{id}/checkout ────────────────────────────────────────────────

def test_checkout_sets_available_false():
    book = make_book()
    result = client.patch(f"/books/{book['id']}/checkout", auth=READER_AUTH).json()
    assert result["available"] is False


def test_checkout_already_out_returns_409():
    book = make_book()
    client.patch(f"/books/{book['id']}/checkout", auth=READER_AUTH)
    response = client.patch(f"/books/{book['id']}/checkout", auth=READER_AUTH)
    assert response.status_code == 409


def test_checkout_unknown_book_returns_404():
    assert client.patch("/books/9999/checkout", auth=READER_AUTH).status_code == 404


# ── PATCH /books/{id}/return ──────────────────────────────────────────────────

def test_return_sets_available_true():
    book = make_book()
    client.patch(f"/books/{book['id']}/checkout", auth=READER_AUTH)
    result = client.patch(f"/books/{book['id']}/return", auth=READER_AUTH).json()
    assert result["available"] is True


def test_return_already_available_returns_409():
    book = make_book()
    response = client.patch(f"/books/{book['id']}/return", auth=READER_AUTH)
    assert response.status_code == 409


def test_return_unknown_book_returns_404():
    assert client.patch("/books/9999/return", auth=READER_AUTH).status_code == 404


# ── DELETE /books/{id} ────────────────────────────────────────────────────────

def test_delete_book_librarian_returns_204():
    book = make_book()
    assert client.delete(f"/books/{book['id']}", auth=LIBRARIAN_AUTH).status_code == 204


def test_delete_book_reader_returns_403():
    book = make_book()
    assert client.delete(f"/books/{book['id']}", auth=READER_AUTH).status_code == 403


def test_delete_book_removes_from_list():
    book = make_book()
    client.delete(f"/books/{book['id']}", auth=LIBRARIAN_AUTH)
    assert client.get("/books", auth=READER_AUTH).json() == []


def test_delete_book_unknown_returns_404():
    assert client.delete("/books/9999", auth=LIBRARIAN_AUTH).status_code == 404
