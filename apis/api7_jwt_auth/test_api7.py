"""
Tests for API 7 - OAuth2 + JWT: Personal Notes API

Requirements covered:
  - POST /token    returns 200 with access_token and token_type for valid credentials
  - POST /token    returns 401 for wrong password
  - POST /token    returns 401 for unknown username
  - GET  /users/me returns correct username and role with valid token
  - GET  /users/me returns 401 without token
  - GET  /users/me returns 401 with malformed token
  - POST /notes    creates note owned by current user (201)
  - POST /notes    returns 401 without token
  - POST /notes    returns 422 for empty title
  - GET  /notes    returns only current user's notes
  - GET  /notes    does not include other users' notes
  - GET  /notes/{id} returns 403 when note belongs to another user (not 404)
  - GET  /notes/{id} returns 404 for completely unknown note
  - PATCH /notes/{id} updates only fields provided
  - PATCH /notes/{id} returns 403 for another user's note
  - DELETE /notes/{id} returns 204 for own note
  - DELETE /notes/{id} returns 403 for another user's note
  - GET /admin/notes  returns all notes with admin token
  - GET /admin/notes  returns 403 with non-admin token
  - Expired token returns 401
"""

import pytest
from datetime import timedelta
from fastapi.testclient import TestClient
import apis.api7_jwt_auth.main as m
from apis.api7_jwt_auth.main import app, _reset, create_access_token, TokenData

client = TestClient(app)


@pytest.fixture(autouse=True)
def reset_notes():
    _reset()
    yield


def get_token(username: str, password: str) -> str:
    """Helper: exchange credentials for a bearer token."""
    response = client.post(
        "/token",
        data={"username": username, "password": password},
    )
    assert response.status_code == 200, f"Login failed: {response.json()}"
    return response.json()["access_token"]


def auth_header(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


# ── POST /token ───────────────────────────────────────────────────────────────

def test_login_valid_credentials_returns_200():
    response = client.post("/token", data={"username": "alice", "password": "alice123"})
    assert response.status_code == 200


def test_login_returns_access_token():
    response = client.post("/token", data={"username": "alice", "password": "alice123"})
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_login_wrong_password_returns_401():
    response = client.post("/token", data={"username": "alice", "password": "wrong"})
    assert response.status_code == 401


def test_login_unknown_user_returns_401():
    response = client.post("/token", data={"username": "nobody", "password": "pass"})
    assert response.status_code == 401


# ── GET /users/me ─────────────────────────────────────────────────────────────

def test_get_me_returns_correct_username():
    token = get_token("alice", "alice123")
    data = client.get("/users/me", headers=auth_header(token)).json()
    assert data["username"] == "alice"
    assert data["role"] == "user"


def test_get_me_no_token_returns_401():
    assert client.get("/users/me").status_code == 401


def test_get_me_malformed_token_returns_401():
    assert client.get("/users/me", headers={"Authorization": "Bearer not.a.token"}).status_code == 401


def test_get_me_admin_role():
    token = get_token("admin", "admin123")
    data = client.get("/users/me", headers=auth_header(token)).json()
    assert data["role"] == "admin"


# ── POST /notes ───────────────────────────────────────────────────────────────

def test_create_note_returns_201():
    token = get_token("alice", "alice123")
    response = client.post(
        "/notes",
        json={"title": "My Note", "content": "Hello"},
        headers=auth_header(token),
    )
    assert response.status_code == 201


def test_create_note_owner_is_current_user():
    token = get_token("alice", "alice123")
    note = client.post(
        "/notes",
        json={"title": "Alice Note"},
        headers=auth_header(token),
    ).json()
    assert note["owner"] == "alice"


def test_create_note_no_token_returns_401():
    assert client.post("/notes", json={"title": "Test"}).status_code == 401


def test_create_note_empty_title_returns_422():
    token = get_token("alice", "alice123")
    response = client.post("/notes", json={"title": ""}, headers=auth_header(token))
    assert response.status_code == 422


# ── GET /notes ────────────────────────────────────────────────────────────────

def test_list_notes_only_own_notes():
    alice_token = get_token("alice", "alice123")
    bob_token = get_token("bob", "bob123")
    client.post("/notes", json={"title": "Alice Note"}, headers=auth_header(alice_token))
    client.post("/notes", json={"title": "Bob Note"}, headers=auth_header(bob_token))

    alice_notes = client.get("/notes", headers=auth_header(alice_token)).json()
    assert len(alice_notes) == 1
    assert alice_notes[0]["title"] == "Alice Note"


def test_list_notes_excludes_other_users_notes():
    alice_token = get_token("alice", "alice123")
    bob_token = get_token("bob", "bob123")
    client.post("/notes", json={"title": "Bob Note"}, headers=auth_header(bob_token))

    alice_notes = client.get("/notes", headers=auth_header(alice_token)).json()
    assert alice_notes == []


# ── GET /notes/{id} ───────────────────────────────────────────────────────────

def test_get_note_own_note_returns_200():
    alice_token = get_token("alice", "alice123")
    note = client.post("/notes", json={"title": "Mine"}, headers=auth_header(alice_token)).json()
    response = client.get(f"/notes/{note['id']}", headers=auth_header(alice_token))
    assert response.status_code == 200


def test_get_note_other_users_note_returns_403():
    alice_token = get_token("alice", "alice123")
    bob_token = get_token("bob", "bob123")
    note = client.post("/notes", json={"title": "Bob's"}, headers=auth_header(bob_token)).json()
    response = client.get(f"/notes/{note['id']}", headers=auth_header(alice_token))
    assert response.status_code == 403


def test_get_note_unknown_returns_404():
    alice_token = get_token("alice", "alice123")
    assert client.get("/notes/9999", headers=auth_header(alice_token)).status_code == 404


# ── PATCH /notes/{id} ────────────────────────────────────────────────────────

def test_patch_note_updates_title():
    alice_token = get_token("alice", "alice123")
    note = client.post("/notes", json={"title": "Old", "content": "Keep"}, headers=auth_header(alice_token)).json()
    updated = client.patch(
        f"/notes/{note['id']}",
        json={"title": "New"},
        headers=auth_header(alice_token),
    ).json()
    assert updated["title"] == "New"
    assert updated["content"] == "Keep"  # unchanged


def test_patch_note_other_user_returns_403():
    alice_token = get_token("alice", "alice123")
    bob_token = get_token("bob", "bob123")
    note = client.post("/notes", json={"title": "Bob's"}, headers=auth_header(bob_token)).json()
    response = client.patch(f"/notes/{note['id']}", json={"title": "Hack"}, headers=auth_header(alice_token))
    assert response.status_code == 403


# ── DELETE /notes/{id} ───────────────────────────────────────────────────────

def test_delete_own_note_returns_204():
    alice_token = get_token("alice", "alice123")
    note = client.post("/notes", json={"title": "Delete me"}, headers=auth_header(alice_token)).json()
    response = client.delete(f"/notes/{note['id']}", headers=auth_header(alice_token))
    assert response.status_code == 204


def test_delete_own_note_removes_from_list():
    alice_token = get_token("alice", "alice123")
    note = client.post("/notes", json={"title": "Gone"}, headers=auth_header(alice_token)).json()
    client.delete(f"/notes/{note['id']}", headers=auth_header(alice_token))
    assert client.get("/notes", headers=auth_header(alice_token)).json() == []


def test_delete_other_users_note_returns_403():
    alice_token = get_token("alice", "alice123")
    bob_token = get_token("bob", "bob123")
    note = client.post("/notes", json={"title": "Bob's"}, headers=auth_header(bob_token)).json()
    response = client.delete(f"/notes/{note['id']}", headers=auth_header(alice_token))
    assert response.status_code == 403


# ── GET /admin/notes ──────────────────────────────────────────────────────────

def test_admin_sees_all_notes():
    alice_token = get_token("alice", "alice123")
    bob_token = get_token("bob", "bob123")
    admin_token = get_token("admin", "admin123")

    client.post("/notes", json={"title": "Alice"}, headers=auth_header(alice_token))
    client.post("/notes", json={"title": "Bob"}, headers=auth_header(bob_token))

    all_notes = client.get("/admin/notes", headers=auth_header(admin_token)).json()
    assert len(all_notes) == 2


def test_admin_notes_non_admin_returns_403():
    alice_token = get_token("alice", "alice123")
    response = client.get("/admin/notes", headers=auth_header(alice_token))
    assert response.status_code == 403


def test_admin_notes_no_token_returns_401():
    assert client.get("/admin/notes").status_code == 401


# ── Expired token ─────────────────────────────────────────────────────────────

def test_expired_token_returns_401(monkeypatch):
    monkeypatch.setattr(m, "ACCESS_TOKEN_EXPIRE_MINUTES", -1)
    expired_token = create_access_token({"sub": "alice", "role": "user"})
    response = client.get("/users/me", headers=auth_header(expired_token))
    assert response.status_code == 401
