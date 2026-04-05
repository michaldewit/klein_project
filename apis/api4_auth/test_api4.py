"""
Tests for API 4 - Auth-Protected API

Requirements covered:
  - GET /public                 returns 200 without any key
  - GET /public/info            returns 200 without any key
  - GET /protected/data         returns 401 without key
  - GET /protected/data         returns 401 with invalid key
  - GET /protected/data         returns 200 with reader key
  - GET /protected/data         returns 200 with admin key
  - GET /admin/notes            returns 401 without key
  - GET /admin/notes            returns 403 with reader key
  - GET /admin/notes            returns 200 with admin key
  - POST /admin/notes           returns 401 without key
  - POST /admin/notes           returns 403 with reader key
  - POST /admin/notes           returns 201 with admin key
  - DELETE /admin/notes/{id}    returns 401 without key
  - DELETE /admin/notes/{id}    returns 403 with reader key
  - DELETE /admin/notes/{id}    returns 204 with admin key
  - DELETE /admin/notes/{id}    returns 404 for unknown note id
  - POST /admin/notes           validates title is not empty
"""

import pytest
from fastapi.testclient import TestClient
from apis.api4_auth.main import app, _reset

client = TestClient(app)

READER_KEY = "reader-key-123"
ADMIN_KEY = "admin-key-456"
BAD_KEY = "not-a-valid-key"


@pytest.fixture(autouse=True)
def reset_notes():
    _reset()
    yield


# ── Public routes ─────────────────────────────────────────────────────────────

def test_public_returns_200():
    assert client.get("/public").status_code == 200


def test_public_no_key_required():
    response = client.get("/public")
    assert "message" in response.json()


def test_public_info_returns_200():
    assert client.get("/public/info").status_code == 200


def test_public_info_shows_roles():
    data = client.get("/public/info").json()
    assert "roles" in data
    assert "reader" in data["roles"]
    assert "admin" in data["roles"]


# ── GET /protected/data ───────────────────────────────────────────────────────

def test_protected_data_no_key_returns_401():
    assert client.get("/protected/data").status_code == 401


def test_protected_data_invalid_key_returns_401():
    response = client.get("/protected/data", headers={"X-API-Key": BAD_KEY})
    assert response.status_code == 401


def test_protected_data_reader_key_returns_200():
    response = client.get("/protected/data", headers={"X-API-Key": READER_KEY})
    assert response.status_code == 200


def test_protected_data_admin_key_returns_200():
    response = client.get("/protected/data", headers={"X-API-Key": ADMIN_KEY})
    assert response.status_code == 200


def test_protected_data_shows_role():
    response = client.get("/protected/data", headers={"X-API-Key": READER_KEY})
    assert response.json()["accessed_with_role"] == "reader"


def test_protected_data_admin_shows_admin_role():
    response = client.get("/protected/data", headers={"X-API-Key": ADMIN_KEY})
    assert response.json()["accessed_with_role"] == "admin"


# ── GET /admin/notes ──────────────────────────────────────────────────────────

def test_list_notes_no_key_returns_401():
    assert client.get("/admin/notes").status_code == 401


def test_list_notes_reader_key_returns_403():
    response = client.get("/admin/notes", headers={"X-API-Key": READER_KEY})
    assert response.status_code == 403


def test_list_notes_admin_key_returns_200():
    response = client.get("/admin/notes", headers={"X-API-Key": ADMIN_KEY})
    assert response.status_code == 200


def test_list_notes_initially_empty():
    response = client.get("/admin/notes", headers={"X-API-Key": ADMIN_KEY})
    assert response.json() == []


# ── POST /admin/notes ─────────────────────────────────────────────────────────

def test_create_note_no_key_returns_401():
    response = client.post("/admin/notes", json={"title": "Test"})
    assert response.status_code == 401


def test_create_note_reader_key_returns_403():
    response = client.post(
        "/admin/notes", json={"title": "Test"}, headers={"X-API-Key": READER_KEY}
    )
    assert response.status_code == 403


def test_create_note_admin_key_returns_201():
    response = client.post(
        "/admin/notes", json={"title": "My Note"}, headers={"X-API-Key": ADMIN_KEY}
    )
    assert response.status_code == 201


def test_create_note_returns_correct_data():
    response = client.post(
        "/admin/notes",
        json={"title": "Hello", "body": "World"},
        headers={"X-API-Key": ADMIN_KEY},
    )
    data = response.json()
    assert data["title"] == "Hello"
    assert data["body"] == "World"
    assert "id" in data


def test_create_note_empty_title_returns_422():
    response = client.post(
        "/admin/notes",
        json={"title": ""},
        headers={"X-API-Key": ADMIN_KEY},
    )
    assert response.status_code == 422


def test_create_note_appears_in_list():
    client.post("/admin/notes", json={"title": "Note 1"}, headers={"X-API-Key": ADMIN_KEY})
    notes = client.get("/admin/notes", headers={"X-API-Key": ADMIN_KEY}).json()
    assert len(notes) == 1
    assert notes[0]["title"] == "Note 1"


# ── DELETE /admin/notes/{id} ──────────────────────────────────────────────────

def test_delete_note_no_key_returns_401():
    assert client.delete("/admin/notes/1").status_code == 401


def test_delete_note_reader_key_returns_403():
    response = client.delete("/admin/notes/1", headers={"X-API-Key": READER_KEY})
    assert response.status_code == 403


def test_delete_note_admin_returns_204():
    note = client.post(
        "/admin/notes", json={"title": "To Delete"}, headers={"X-API-Key": ADMIN_KEY}
    ).json()
    response = client.delete(f"/admin/notes/{note['id']}", headers={"X-API-Key": ADMIN_KEY})
    assert response.status_code == 204


def test_delete_note_removes_from_list():
    note = client.post(
        "/admin/notes", json={"title": "Gone"}, headers={"X-API-Key": ADMIN_KEY}
    ).json()
    client.delete(f"/admin/notes/{note['id']}", headers={"X-API-Key": ADMIN_KEY})
    notes = client.get("/admin/notes", headers={"X-API-Key": ADMIN_KEY}).json()
    assert len(notes) == 0


def test_delete_note_unknown_id_returns_404():
    response = client.delete("/admin/notes/9999", headers={"X-API-Key": ADMIN_KEY})
    assert response.status_code == 404
