from pathlib import Path

import pytest

from ctf import leaderboard as lb


@pytest.fixture(autouse=True)
def isolated_leaderboard_db(tmp_path: Path):  # noqa: F811
    db_path = tmp_path / "leaderboard.db"
    db_uri = f"sqlite:///{db_path}"
    lb.configure_db_uri(db_uri)
    yield
    lb.reset_db_uri_override()


def test_strip_leaderboard_markers():  # noqa: F841
    marker = lb.format_leaderboard_marker(level=3)
    text = f"Congrats! {marker}"
    cleaned, markers = lb.strip_leaderboard_markers(text)
    assert cleaned == "Congrats!"
    assert markers and markers[0]["level"] == 3
    assert markers[0]["status"] == "correct"


def test_record_and_fetch_leaderboard():  # noqa: F841
    lb.record_level_completion("alice", 1)
    lb.record_level_completion("alice", 2)
    lb.record_level_completion("bob", 1)

    leaderboard = lb.get_leaderboard()
    assert leaderboard
    assert leaderboard[0]["username"] == "alice"
    assert leaderboard[0]["levels_completed"] == 2
    assert leaderboard[0]["highest_level"] == 2

    recent = lb.get_recent_completions(limit=2)
    assert len(recent) == 2


def test_ensure_leaderboard_user_adds_level_zero_entry():  # noqa: F841
    lb.ensure_leaderboard_user("charlie")
    rows = lb.get_leaderboard()
    assert rows
    usernames = {row["username"] for row in rows}
    assert "charlie" in usernames
