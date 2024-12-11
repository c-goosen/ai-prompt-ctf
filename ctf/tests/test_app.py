from fastapi.testclient import TestClient
import pytest
from app import app

client = TestClient(app)


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"health": "ok"}


def test_root():
    response = client.get("/")
    assert response.status_code == 200
    # assert response.json() == {"health": "ok"}


def test_challenge_description():
    response = client.get("/challenges")
    assert response.status_code == 200
    # assert response.json() == {"health": "ok"}


@pytest.mark.parametrize("level", [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10])
def test_challenges(level):
    response = client.get(f"/level/{level}")
    assert response.status_code == 200
    assert f"Level {level}" in response.text
    # assert response.json() == {"health": "ok"}
