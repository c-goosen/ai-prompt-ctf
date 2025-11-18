"""
SQLite-backed leaderboard helpers shared between the frontend and agent tools.
"""

from __future__ import annotations

import json
import logging
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

from ctf.app_config import settings

logger = logging.getLogger(__name__)

LEADERBOARD_MARKER_PREFIX = "<!--LEADERBOARD:"
LEADERBOARD_MARKER_SUFFIX = "-->"
LEADERBOARD_MARKER_PATTERN = r"<!--LEADERBOARD:(?P<payload>{.*?})-->"

_DB_PATH_OVERRIDE: Path | None = None


def configure_db_path(path: Path) -> None:
    """
    Allow tests to override the storage path without mutating global settings.
    """
    global _DB_PATH_OVERRIDE
    _DB_PATH_OVERRIDE = Path(path)


def reset_db_path_override() -> None:
    global _DB_PATH_OVERRIDE
    _DB_PATH_OVERRIDE = None


def _db_path() -> Path:
    if _DB_PATH_OVERRIDE is not None:
        return _DB_PATH_OVERRIDE
    return Path(settings.LEADERBOARD_DB_PATH).expanduser().resolve()


def _ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


@contextmanager
def _get_connection() -> Iterable[sqlite3.Connection]:
    path = _db_path()
    _ensure_parent(path)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    try:
        _ensure_tables(conn)
        yield conn
        conn.commit()
    except sqlite3.Error:
        conn.rollback()
        raise
    finally:
        conn.close()


CREATE_TABLE_SQL = """
    CREATE TABLE IF NOT EXISTS leaderboard_entries (
        username TEXT NOT NULL,
        level INTEGER NOT NULL,
        completed_at TEXT NOT NULL,
        PRIMARY KEY (username, level)
    )
"""


def _ensure_tables(conn: sqlite3.Connection) -> None:
    conn.execute(CREATE_TABLE_SQL)
    _migrate_legacy_tables(conn)


def _migrate_legacy_tables(conn: sqlite3.Connection) -> None:
    """
    Standardize historical schemas (session_id or user_id based) to username-only.
    """
    rows = conn.execute("PRAGMA table_info(leaderboard_entries)").fetchall()
    column_names = {row["name"] for row in rows} if rows else set()
    if not column_names:
        return
    expected = {"username", "level", "completed_at"}
    if column_names == expected:
        return

    conn.execute("ALTER TABLE leaderboard_entries RENAME TO leaderboard_entries_old")
    conn.execute(CREATE_TABLE_SQL)

    username_column = "username"
    if "username" not in column_names:
        if "user_id" in column_names:
            username_column = "user_id"
        elif "session_id" in column_names:
            username_column = "session_id"
        else:
            username_column = "'unknown'"

    level_column = "level" if "level" in column_names else "0"
    completed_column = "completed_at" if "completed_at" in column_names else "datetime('now')"

    conn.execute(
        f"""
        INSERT OR IGNORE INTO leaderboard_entries (username, level, completed_at)
        SELECT {username_column} AS username,
               {level_column} AS level,
               {completed_column} AS completed_at
        FROM leaderboard_entries_old
        WHERE {username_column} IS NOT NULL
        """
    )
    conn.execute("DROP TABLE leaderboard_entries_old")


def format_leaderboard_marker(level: int, status: str = "correct") -> str:
    payload = json.dumps({"status": status, "level": level})
    return f"{LEADERBOARD_MARKER_PREFIX}{payload}{LEADERBOARD_MARKER_SUFFIX}"


def strip_leaderboard_markers(text: str) -> tuple[str, list[dict]]:
    """
    Remove leaderboard markers from a string and return structured payloads.
    """
    if not text:
        return text, []

    markers: list[dict] = []

    def _replace(match):
        payload = match.group("payload")
        try:
            markers.append(json.loads(payload))
        except json.JSONDecodeError:
            logger.debug("Failed to decode leaderboard marker payload: %s", payload)
        return ""

    import re

    pattern = re.compile(LEADERBOARD_MARKER_PATTERN)
    cleaned = pattern.sub(_replace, text)
    return cleaned.strip(), markers


def record_level_completion(username: str, level: int) -> None:
    if not username:
        return
    timestamp = datetime.now(timezone.utc).isoformat()
    try:
        with _get_connection() as conn:
            conn.execute(
                """
                INSERT INTO leaderboard_entries (username, level, completed_at)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(username, level) DO UPDATE SET
                    completed_at=excluded.completed_at
                """,
                (username, level, timestamp),
            )
    except sqlite3.Error as exc:
        logger.warning("Failed to record leaderboard entry: %s", exc)


def get_leaderboard(limit: int = 25) -> list[dict]:
    try:
        with _get_connection() as conn:
            rows = conn.execute(
                """
                SELECT
                    username,
                    COUNT(*) AS levels_completed,
                    MAX(level) AS highest_level,
                    MAX(completed_at) AS last_completed_at,
                    MIN(completed_at) AS first_completed_at
                FROM leaderboard_entries
                GROUP BY username
                ORDER BY highest_level DESC, first_completed_at ASC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
            return [dict(row) for row in rows]
    except sqlite3.Error as exc:
        logger.warning("Failed to load leaderboard: %s", exc)
        return []


def get_recent_completions(limit: int = 10) -> list[dict]:
    try:
        with _get_connection() as conn:
            rows = conn.execute(
                """
                SELECT username, level, completed_at
                FROM leaderboard_entries
                ORDER BY completed_at DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
            return [dict(row) for row in rows]
    except sqlite3.Error as exc:
        logger.warning("Failed to load recent completions: %s", exc)
        return []


def get_leaderboard_summary() -> dict:
    try:
        with _get_connection() as conn:
            row = conn.execute(
                """
                SELECT
                    COUNT(DISTINCT username) AS players,
                    COUNT(*) AS total_completions
                FROM leaderboard_entries
                """
            ).fetchone()
            if row is None:
                return {"players": 0, "total_completions": 0}
            return dict(row)
    except sqlite3.Error as exc:
        logger.warning("Failed to load leaderboard summary: %s", exc)
        return {"players": 0, "total_completions": 0}

