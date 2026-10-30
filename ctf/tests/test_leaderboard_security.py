"""Regression tests for the leaderboard-spoofing fix.

The leaderboard marker (ctf.leaderboard.format_leaderboard_marker) is a
static, public string, so a player can ask the model to repeat it verbatim.
Credit must therefore only ever be granted by
ctf.agents.tools._record_leaderboard_progress, invoked from a genuine
submit_answer_func tool call using the ADK-session-bound identity. The web
app (web/) only strips markers for display; its tests cover that side.
"""

import asyncio
from pathlib import Path

import pytest

from ctf import leaderboard as lb
from ctf.agents import tools as tools_module
from ctf.app_config import settings


@pytest.fixture(autouse=True)
def isolated_leaderboard_db(tmp_path: Path):  # noqa: F811
    db_path = tmp_path / "leaderboard.db"
    lb.configure_db_uri(f"sqlite:///{db_path}")
    yield
    lb.reset_db_uri_override()


class _FakeSession:
    def __init__(self, user_id: str):
        self.user_id = user_id


class _FakeToolContext:
    """Minimal duck-typed stand-in for google.adk's ToolContext, exposing
    only what _get_username_from_context reads (session.user_id)."""

    def __init__(self, user_id: str):
        self.session = _FakeSession(user_id)


def test_submit_answer_func_still_credits_independently_of_chat_py():
    """Legitimate crediting happens through a real submit_answer_func call."""
    fake_ctx = _FakeToolContext("realplayer")

    result = asyncio.run(
        tools_module.submit_answer_func(
            answer=settings.PASSWORDS[0],
            level=0,
            tool_context=fake_ctx,
        )
    )

    assert "❌" not in result

    leaderboard = lb.get_leaderboard()
    entry = next(
        (row for row in leaderboard if row["username"] == "realplayer"),
        None,
    )
    assert entry is not None
    assert entry["highest_level"] == 0
