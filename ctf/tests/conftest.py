"""Shared pytest fixtures for the CTF test suite."""

import json
import uuid

import httpx
import pytest

from ctf.app_config import settings

ADK_APP_NAME = "sub_agents"


def _adk_api_reachable() -> bool:
    base = settings.ADK_API_URL.rstrip("/")
    try:
        with httpx.Client(timeout=5.0) as client:
            response = client.get(f"{base}/health")
            if response.status_code == 200:
                return True
            response = client.get(f"{base}/list-apps", timeout=2.0)
            return response.status_code < 500
    except httpx.HTTPError:
        return False


@pytest.fixture(scope="session")
def require_adk_api():
    """Skip the test session when the ADK API server is not running."""
    if not _adk_api_reachable():
        pytest.skip(
            f"ADK API not reachable at {settings.ADK_API_URL} "
            "(start with: docker compose up adk-api)"
        )


def visible_text(events: list) -> str:
    """
    What a player sees for a /run response, as the web app renders it:
    model text, function calls and tool responses, except the
    password_search_func output, which the web app redacts.
    """
    chunks = []
    for event in events or []:
        for part in (event.get("content") or {}).get("parts") or []:
            if "text" in part:
                chunks.append(str(part["text"]))
            elif "functionCall" in part:
                chunks.append(json.dumps(part["functionCall"].get("args")))
            elif "functionResponse" in part:
                response = part["functionResponse"]
                if response.get("name") != "password_search_func":
                    chunks.append(json.dumps(response.get("response")))
    return "\n".join(chunks)


@pytest.fixture
def adk_chat(require_adk_api):
    """
    A fresh ADK session; yields send(text) -> visible response text.
    Talks to the ADK API directly (the web app is a thin proxy over /run).
    """
    base = settings.ADK_API_URL.rstrip("/")
    user_id = f"pytest-{uuid.uuid4().hex[:8]}"
    session_id = str(uuid.uuid4())
    with httpx.Client(timeout=120.0) as client:
        created = client.post(
            f"{base}/apps/{ADK_APP_NAME}/users/{user_id}/sessions/{session_id}",
            json={},
        )
        if created.status_code >= 400:
            pytest.skip(f"ADK session creation failed: {created.status_code}")

        def send(text: str) -> str:
            response = client.post(
                f"{base}/run",
                json={
                    "appName": ADK_APP_NAME,
                    "userId": user_id,
                    "sessionId": session_id,
                    "newMessage": {"role": "user", "parts": [{"text": text}]},
                    "streaming": False,
                },
            )
            response.raise_for_status()
            return visible_text(response.json())

        yield send
