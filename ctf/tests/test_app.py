import pytest
from fastapi.testclient import TestClient

from ctf.frontend.app import app

client = TestClient(app)


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["health"] == "ok"
    assert "status" in data
    assert "services" in data


def test_root():
    response = client.get("/")
    assert response.status_code == 200
    # assert response.json() == {"health": "ok"}


def test_challenge_description():
    response = client.get("/challenges")
    assert response.status_code == 200
    # assert response.json() == {"health": "ok"}


def test_chat_screen():
    response = client.get("/chat")
    assert response.status_code == 200
    assert "Agent Arena" in response.text
