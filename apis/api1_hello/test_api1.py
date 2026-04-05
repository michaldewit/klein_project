"""
Tests for API 1 - Hello World

Requirements covered:
  - GET /           returns 200 with welcome message
  - GET /hello/{name} returns 200 with correct greeting
  - GET /hello/{name}?lang=nl returns Dutch greeting
  - GET /hello/{name}?lang=unknown falls back to English
  - POST /echo      returns 200 and echoes body data
  - POST /echo      returns correct keys_received and count
  - POST /echo      with empty dict returns count 0
"""

import pytest
from fastapi.testclient import TestClient
from apis.api1_hello.main import app

client = TestClient(app)


# ── GET / ────────────────────────────────────────────────────────────────────

def test_root_status_code():
    response = client.get("/")
    assert response.status_code == 200


def test_root_returns_message():
    response = client.get("/")
    assert "message" in response.json()


def test_root_message_content():
    response = client.get("/")
    assert "Welcome" in response.json()["message"]


# ── GET /hello/{name} ────────────────────────────────────────────────────────

def test_hello_status_code():
    response = client.get("/hello/Alice")
    assert response.status_code == 200


def test_hello_contains_name():
    response = client.get("/hello/Alice")
    assert "Alice" in response.json()["message"]


def test_hello_default_lang_english():
    response = client.get("/hello/Bob")
    data = response.json()
    assert data["lang"] == "en"
    assert "Hello" in data["message"]


def test_hello_dutch_greeting():
    response = client.get("/hello/Bob?lang=nl")
    data = response.json()
    assert data["lang"] == "nl"
    assert "Hallo" in data["message"]
    assert "Bob" in data["message"]


def test_hello_unknown_lang_falls_back_to_english():
    response = client.get("/hello/Bob?lang=fr")
    data = response.json()
    assert "Hello" in data["message"]


def test_hello_returns_name_field():
    response = client.get("/hello/Charlie")
    assert response.json()["name"] == "Charlie"


# ── POST /echo ───────────────────────────────────────────────────────────────

def test_echo_status_code():
    response = client.post("/echo", json={"data": {"key": "value"}})
    assert response.status_code == 200


def test_echo_returns_echoed_data():
    payload = {"data": {"fruit": "apple", "color": "red"}}
    response = client.post("/echo", json=payload)
    assert response.json()["echoed"] == payload["data"]


def test_echo_keys_received():
    payload = {"data": {"a": 1, "b": 2, "c": 3}}
    response = client.post("/echo", json=payload)
    assert sorted(response.json()["keys_received"]) == ["a", "b", "c"]


def test_echo_count():
    payload = {"data": {"x": 10, "y": 20}}
    response = client.post("/echo", json=payload)
    assert response.json()["count"] == 2


def test_echo_empty_dict():
    response = client.post("/echo", json={"data": {}})
    data = response.json()
    assert data["count"] == 0
    assert data["echoed"] == {}


def test_echo_missing_body_returns_422():
    response = client.post("/echo", json={})
    assert response.status_code == 422
