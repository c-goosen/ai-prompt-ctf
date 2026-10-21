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


def test_resubmitting_a_level_keeps_first_completion_time():  # noqa: F841
    lb.record_level_completion("dana", 1)
    first = lb.get_recent_completions()[0]["completed_at"]

    lb.record_level_completion("dana", 1)
    recent = lb.get_recent_completions()

    assert len(recent) == 1
    assert recent[0]["completed_at"] == first


def test_postgres_uri_uses_psycopg2_driver(monkeypatch):  # noqa: F841
    lb.reset_db_uri_override()
    monkeypatch.setenv("POSTGRES_DB_URI", "postgresql://u:p@db:5432/ctf")
    assert lb._db_uri() == "postgresql+psycopg2://u:p@db:5432/ctf"
    monkeypatch.setenv("POSTGRES_DB_URI", "postgres://u:p@db/ctf")
    assert lb._db_uri() == "postgresql+psycopg2://u:p@db/ctf"
