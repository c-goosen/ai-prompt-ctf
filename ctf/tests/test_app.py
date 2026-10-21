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


@pytest.fixture
def isolated_leaderboard_db(tmp_path):
    from ctf import leaderboard as lb

    lb.configure_db_uri(f"sqlite:///{tmp_path / 'leaderboard.db'}")
    yield
    lb.reset_db_uri_override()


@pytest.mark.parametrize(
    "username", ["../x", "a/b", "..", ".hidden", "x" * 33, "a b", "a?b=c"]
)
def test_register_rejects_unsafe_usernames(isolated_leaderboard_db, username):
    response = client.post("/register", json={"username": username})
    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid username"


def test_register_rejects_unsafe_session_id(isolated_leaderboard_db):
    response = client.post(
        "/register", json={"username": "erin", "session_id": "../escape"}
    )
    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid session ID"


def test_register_missing_username_returns_plain_400(isolated_leaderboard_db):
    response = client.post("/register", json={})
    assert response.status_code == 400
    assert response.json()["detail"] == "Username is required"


def test_register_htmx_rejects_unsafe_username(isolated_leaderboard_db):
    response = client.post(
        "/register",
        data={"username": "../x"},
        headers={"HX-Request": "true"},
    )
    assert response.status_code == 200
    assert "Invalid username" in response.text


def test_route_rate_limits_are_enforced():
    # Regression: "N/min" / "N/sec" strings silently failed to parse with
    # limits>=5, leaving every per-route limit unregistered.
    statuses = [client.get("/faq").status_code for _ in range(2)]
    assert statuses == [200, 429]


def test_chat_page_loads_watermelon_animations():
    response = client.get("/ctf")
    assert response.status_code == 200
    assert "/assets/css/animations.css" in response.text
    assert "/assets/js/animations.js" in response.text
    assert 'class="loader-label"' in response.text
