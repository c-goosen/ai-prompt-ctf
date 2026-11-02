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


def _seed_old_numbering(db_path, rows):
    """A database from before levels 10-14 were added (no migrations table)."""
    import sqlite3

    connection = sqlite3.connect(db_path)
    connection.execute(
        "CREATE TABLE leaderboard_entries (username VARCHAR(255) NOT NULL, "
        "level INTEGER NOT NULL, completed_at TIMESTAMP NOT NULL, "
        "PRIMARY KEY (username, level))"
    )
    connection.executemany(
        "INSERT INTO leaderboard_entries VALUES (?, ?, '2025-11-01T10:00:00+00:00')",
        rows,
    )
    connection.commit()
    connection.close()


def test_old_hold_the_fort_solves_move_to_level_15(tmp_path: Path):
    db_path = tmp_path / "old.db"
    _seed_old_numbering(
        db_path, [("ann", 9), ("ann", 10), ("bo", 10), ("bo", 15)]
    )
    lb.configure_db_uri(f"sqlite:///{db_path}")

    rows = {row["username"]: row for row in lb.get_leaderboard()}
    assert rows["ann"]["highest_level"] == 15
    assert rows["ann"]["levels_completed"] == 2
    # bo already had 15: the old level 10 row is dropped, not duplicated.
    assert rows["bo"]["highest_level"] == 15
    assert rows["bo"]["levels_completed"] == 1


def test_renumbering_runs_only_once(tmp_path: Path):
    db_path = tmp_path / "old.db"
    _seed_old_numbering(db_path, [("ann", 10)])
    lb.configure_db_uri(f"sqlite:///{db_path}")
    lb.get_leaderboard()

    # A solve of the new level 10 after the migration stays at level 10.
    lb.record_level_completion("cy", 10)
    lb.reset_db_uri_override()
    lb.configure_db_uri(f"sqlite:///{db_path}")

    levels = {
        row["username"]: row["highest_level"] for row in lb.get_leaderboard()
    }
    assert levels == {"ann": 15, "cy": 10}


def test_startup_warns_about_shared_passwords():
    from ctf.agent_startup import warn_about_shared_passwords

    assert warn_about_shared_passwords(
        {10: "Woohoo", 11: "x", 15: "Woohoo"}
    ) == ["Levels 10, 15 share a password"]
    assert warn_about_shared_passwords({0: "a", 1: "b"}) == []
