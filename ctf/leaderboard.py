"""
SQLite-backed leaderboard helpers shared between the frontend and agent tools.
"""

from __future__ import annotations

import json
import logging
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator

from sqlalchemy import (
    Column,
    DateTime,
    Integer,
    String,
    distinct,
    func,
    select,
    text,
)
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, declarative_base, sessionmaker

from ctf.app_config import settings

logger = logging.getLogger(__name__)

LEADERBOARD_MARKER_PREFIX = "<!--LEADERBOARD:"
LEADERBOARD_MARKER_SUFFIX = "-->"
LEADERBOARD_MARKER_PATTERN = r"<!--LEADERBOARD:(?P<payload>{.*?})-->"

_DB_PATH_OVERRIDE: Path | None = None
_ENGINE: Engine | None = None
_SESSION_FACTORY: sessionmaker | None = None
_SCHEMA_INITIALIZED: bool = False

Base = declarative_base()


class LeaderboardEntry(Base):
    __tablename__ = "leaderboard_entries"

    username = Column(String, primary_key=True)
    level = Column(Integer, primary_key=True)
    completed_at = Column(DateTime(timezone=True), nullable=False, index=True)


def configure_db_path(path: Path) -> None:
    """
    Allow tests to override the storage path without mutating global settings.
    """
    global _DB_PATH_OVERRIDE
    _DB_PATH_OVERRIDE = Path(path)
    _reset_engine()


def reset_db_path_override() -> None:
    global _DB_PATH_OVERRIDE
    _DB_PATH_OVERRIDE = None
    _reset_engine()


def _db_path() -> Path:
    if _DB_PATH_OVERRIDE is not None:
        return _DB_PATH_OVERRIDE
    return Path(settings.LEADERBOARD_DB_PATH).expanduser().resolve()


def _ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def _reset_engine() -> None:
    global _ENGINE, _SESSION_FACTORY, _SCHEMA_INITIALIZED
    if _ENGINE is not None:
        _ENGINE.dispose()
    _ENGINE = None
    _SESSION_FACTORY = None
    _SCHEMA_INITIALIZED = False


CREATE_TABLE_SQL = """
    CREATE TABLE IF NOT EXISTS leaderboard_entries (
        username TEXT NOT NULL,
        level INTEGER NOT NULL,
        completed_at TEXT NOT NULL,
        PRIMARY KEY (username, level)
    )
"""


def _get_engine() -> Engine:
    global _ENGINE
    path = _db_path()
    _ensure_parent(path)
    if _ENGINE is None:
        _ENGINE = create_engine(
            f"sqlite:///{path}",
            future=True,
            connect_args={"check_same_thread": False},
        )
    _ensure_schema(_ENGINE)
    return _ENGINE


def _ensure_schema(engine: Engine) -> None:
    global _SCHEMA_INITIALIZED
    if _SCHEMA_INITIALIZED:
        return
    _migrate_legacy_tables(engine)
    Base.metadata.create_all(engine)
    _SCHEMA_INITIALIZED = True


def _migrate_legacy_tables(engine: Engine) -> None:
    """
    Standardize historical schemas (session_id or user_id based) to username-only.
    """
    with engine.begin() as conn:
        rows = (
            conn.execute(text("PRAGMA table_info(leaderboard_entries)"))
            .mappings()
            .all()
        )
    column_names = {row["name"] for row in rows} if rows else set()
    if not column_names:
        return
    expected = {"username", "level", "completed_at"}
    if column_names == expected:
        return

    with engine.begin() as conn:
        conn.execute(
            text(
                "ALTER TABLE leaderboard_entries RENAME TO leaderboard_entries_old"
            )
        )
        conn.execute(text(CREATE_TABLE_SQL))

    username_column = "username"
    if "username" not in column_names:
        if "user_id" in column_names:
            username_column = "user_id"
        elif "session_id" in column_names:
            username_column = "session_id"
        else:
            username_column = "'unknown'"

    level_column = "level" if "level" in column_names else "0"
    completed_column = (
        "completed_at" if "completed_at" in column_names else "datetime('now')"
    )

    with engine.begin() as conn:
        conn.execute(
            text(
                f"""
                INSERT OR IGNORE INTO leaderboard_entries (username, level, completed_at)
                SELECT {username_column} AS username,
                       {level_column} AS level,
                       {completed_column} AS completed_at
                FROM leaderboard_entries_old
                WHERE {username_column} IS NOT NULL
                """
            )
        )
        conn.execute(text("DROP TABLE leaderboard_entries_old"))


@contextmanager
def _session_scope() -> Iterator[Session]:
    engine = _get_engine()
    global _SESSION_FACTORY
    if _SESSION_FACTORY is None:
        _SESSION_FACTORY = sessionmaker(
            engine, expire_on_commit=False, future=True
        )
    session: Session = _SESSION_FACTORY()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def _to_iso(value: datetime | None) -> str | None:
    return value.isoformat() if value is not None else None


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
            logger.debug(
                "Failed to decode leaderboard marker payload: %s", payload
            )
        return ""

    import re

    pattern = re.compile(LEADERBOARD_MARKER_PATTERN)
    cleaned = pattern.sub(_replace, text)
    return cleaned.strip(), markers


def record_level_completion(username: str, level: int) -> None:
    if not username:
        return
    timestamp = datetime.now(timezone.utc)
    try:
        with _session_scope() as session:
            entry = session.get(LeaderboardEntry, (username, level))
            if entry is None:
                entry = LeaderboardEntry(
                    username=username, level=level, completed_at=timestamp
                )
            else:
                entry.completed_at = timestamp
            session.add(entry)
    except SQLAlchemyError as exc:
        logger.warning("Failed to record leaderboard entry: %s", exc)


def ensure_leaderboard_user(username: str) -> None:
    if not username:
        return
    timestamp = datetime.now(timezone.utc)
    try:
        with _session_scope() as session:
            entry = session.get(LeaderboardEntry, (username, 0))
            if entry is None:
                session.add(
                    LeaderboardEntry(
                        username=username, level=0, completed_at=timestamp
                    )
                )
    except SQLAlchemyError as exc:
        logger.warning("Failed to ensure leaderboard user: %s", exc)


def get_leaderboard(limit: int = 25) -> list[dict]:
    try:
        with _session_scope() as session:
            stmt = (
                select(
                    LeaderboardEntry.username,
                    func.count().label("levels_completed"),
                    func.max(LeaderboardEntry.level).label("highest_level"),
                    func.max(LeaderboardEntry.completed_at).label(
                        "last_completed_at"
                    ),
                    func.min(LeaderboardEntry.completed_at).label(
                        "first_completed_at"
                    ),
                )
                .group_by(LeaderboardEntry.username)
                .order_by(
                    func.max(LeaderboardEntry.level).desc(),
                    func.min(LeaderboardEntry.completed_at).asc(),
                )
                .limit(limit)
            )
            rows = session.execute(stmt).all()
            return [
                {
                    "username": row.username,
                    "levels_completed": row.levels_completed,
                    "highest_level": row.highest_level,
                    "last_completed_at": _to_iso(row.last_completed_at),
                    "first_completed_at": _to_iso(row.first_completed_at),
                }
                for row in rows
            ]
    except SQLAlchemyError as exc:
        logger.warning("Failed to load leaderboard: %s", exc)
        return []


def get_recent_completions(limit: int = 10) -> list[dict]:
    try:
        with _session_scope() as session:
            stmt = (
                select(
                    LeaderboardEntry.username,
                    LeaderboardEntry.level,
                    LeaderboardEntry.completed_at,
                )
                .order_by(LeaderboardEntry.completed_at.desc())
                .limit(limit)
            )
            rows = session.execute(stmt).all()
            return [
                {
                    "username": row.username,
                    "level": row.level,
                    "completed_at": _to_iso(row.completed_at),
                }
                for row in rows
            ]
    except SQLAlchemyError as exc:
        logger.warning("Failed to load recent completions: %s", exc)
        return []


def get_leaderboard_summary() -> dict:
    try:
        with _session_scope() as session:
            stmt = select(
                func.count(distinct(LeaderboardEntry.username)).label(
                    "players"
                ),
                func.count().label("total_completions"),
            )
            row = session.execute(stmt).one()
            return {
                "players": row.players or 0,
                "total_completions": row.total_completions or 0,
            }
    except SQLAlchemyError as exc:
        logger.warning("Failed to load leaderboard summary: %s", exc)
        return {"players": 0, "total_completions": 0}
