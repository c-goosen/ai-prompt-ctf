"""Regression tests for the register/session ownership fix.

Previously:
- POST /register let anyone claim any username, including one already
  claimed by someone else (username squatting / account takeover).
- GET /session/{username}/{session_id} had no ownership check at all, so
  any player could read any other player's ADK chat history.

These tests seed ctf.leaderboard's PlayerIdentity table directly via
claim_or_verify_username rather than going through a real /register call,
so they don't require a live ADK API server - the ownership checks in both
routes are designed to short-circuit before ever reaching ADK.
"""

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from ctf import leaderboard as lb
from ctf.frontend.app import app
from ctf.frontend.routes import challenges as challenges_module
from ctf.frontend.routes import chat as chat_module

client = TestClient(app)


@pytest.fixture(autouse=True)
def isolated_leaderboard_db(tmp_path: Path):  # noqa: F811
    db_path = tmp_path / "leaderboard.db"
    lb.configure_db_uri(f"sqlite:///{db_path}")
    yield
    lb.reset_db_uri_override()


def test_register_rejects_username_takeover():
    # Simulate alice already being registered (owns the username).
    lb.claim_or_verify_username("alice", None)

    # A different client, with no player_token cookie, tries to claim the
    # same username.
    response = client.post("/register", json={"username": "alice"})

    assert response.status_code == 409


def test_register_allows_owner_to_reregister_with_correct_token():
    _, token = lb.claim_or_verify_username("alice", None)

    ok, new_token = lb.claim_or_verify_username("alice", token)
    assert ok is True
    # No new token minted - the owner already proved ownership.
    assert new_token is None


def test_session_endpoint_requires_ownership():
    _, alice_token = lb.claim_or_verify_username("alice", None)
    _, bob_token = lb.claim_or_verify_username("bob", None)

    # Bob tries to read alice's session using his own (valid) identity and
    # token, just pointed at alice's username in the path.
    response = TestClient(
        app,
        cookies={
            "anon_user_identity": "bob",
            "player_token": bob_token,
        },
    ).get("/session/alice/some-session-id")
    assert response.status_code == 403

    # Forging the identity cookie alone (no correct token) must also fail.
    response = TestClient(
        app,
        cookies={
            "anon_user_identity": "alice",
            "player_token": "totally-guessed-token",
        },
    ).get("/session/alice/some-session-id")
    assert response.status_code == 403

    # The real owner, with the correct cookies, must not be blocked by the
    # ownership check (a downstream ADK-connectivity error is fine in this
    # test environment, but it must not be a 403).
    response = TestClient(
        app,
        cookies={
            "anon_user_identity": "alice",
            "player_token": alice_token,
        },
    ).get("/session/alice/some-session-id")
    assert response.status_code != 403


@pytest.fixture
def adk_calls(monkeypatch):
    """Record (instead of performing) every ADK call the chat routes make."""
    calls: list[tuple[str, str]] = []

    async def fake_get_session_history(app_name, user_id, session_id):
        calls.append(("history", user_id))
        return []

    async def fake_call_adk_api(user_id, session_id, message, **_kwargs):
        calls.append(("run", user_id))
        return []

    monkeypatch.setattr(
        challenges_module, "get_session_history", fake_get_session_history
    )
    monkeypatch.setattr(chat_module, "call_adk_api", fake_call_adk_api)
    return calls


def _hit_chat_endpoints(cookies: dict) -> None:
    spoof_client = TestClient(app, cookies=cookies)
    assert spoof_client.get("/ctf").status_code == 200
    assert spoof_client.get("/chat/history").status_code == 200
    response = spoof_client.post(
        "/v1/chat/completions", data={"text_input": "hi"}
    )
    assert response.status_code == 200


@pytest.mark.parametrize(
    "player_token", [None, "totally-guessed-token", "bobs-token"]
)
def test_chat_routes_reject_forged_identity(adk_calls, player_token):
    lb.claim_or_verify_username("alice", None)
    _, bob_token = lb.claim_or_verify_username("bob", None)
    if player_token == "bobs-token":
        player_token = bob_token

    cookies = {"anon_user_identity": "alice", "session_id": "alice-session"}
    if player_token:
        cookies["player_token"] = player_token
    _hit_chat_endpoints(cookies)

    # Neither alice's history nor a chat run as alice may reach ADK.
    assert adk_calls == []


def test_chat_routes_allow_owner(adk_calls):
    _, alice_token = lb.claim_or_verify_username("alice", None)
    _hit_chat_endpoints(
        {
            "anon_user_identity": "alice",
            "session_id": "alice-session",
            "player_token": alice_token,
        }
    )
    assert adk_calls == [
        ("history", "alice"),
        ("history", "alice"),
        ("run", "alice"),
    ]


def test_chat_routes_reject_path_like_session_id(adk_calls):
    _, alice_token = lb.claim_or_verify_username("alice", None)
    _hit_chat_endpoints(
        {
            "anon_user_identity": "alice",
            "session_id": "../../bob/sessions/x",
            "player_token": alice_token,
        }
    )
    assert adk_calls == []
