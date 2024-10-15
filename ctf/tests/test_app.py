from fastapi.testclient import TestClient
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


