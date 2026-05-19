"""Shared pytest fixtures for the CTF test suite."""

import uuid

import httpx
import pytest
from fastapi.testclient import TestClient

from ctf.app_config import settings
from ctf.frontend.app import app


def _adk_api_reachable() -> bool:
    base = settings.ADK_API_URL.rstrip("/")
    try:
        with httpx.Client(timeout=5.0) as client:
            response = client.get(f"{base}/health")
            if response.status_code == 200:
                return True
            response = client.get(f"{base}/apps", timeout=2.0)
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


@pytest.fixture
def chat_client(require_adk_api):
    """
    FastAPI test client with a fresh user/session registered against ADK.

    Yields (client, cookies) where cookies must be passed to /v1/chat/completions.
    """
    user_id = f"pytest-{uuid.uuid4().hex[:8]}"
    session_id = str(uuid.uuid4())
    client = TestClient(app)
    register = client.post(
        "/register",
        json={"username": user_id, "session_id": session_id},
    )
    if register.status_code >= 400:
        pytest.skip(
            f"ADK registration failed ({register.status_code}): {register.text}"
        )
    cookies = {
        "anon_user_identity": user_id,
        "session_id": session_id,
    }
    yield client, cookies
