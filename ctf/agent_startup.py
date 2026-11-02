"""
Start-up work for the agent container, run before `adk web`.

These used to run inside the FastAPI frontend; the Next.js web app can't do
them, and the agent is the only thing that uses the guard models and the
LanceDB flags anyway.

- PREPARE_FLAGS (unset by default): seed the LanceDB RAG store and the
  level 5 users.db with the level passwords.
- DOWNLOAD_MODELS (on by default): pre-download the Hugging Face guard
  models so the first guarded request doesn't stall on a download.
- Always: create the leaderboard tables and apply pending migrations (such as
  moving old Hold the Fort solves to its new level), so the web app's
  leaderboard is right before anyone submits.
"""

import logging
import os

logger = logging.getLogger(__name__)


def _enabled(name: str, default: str) -> bool:
    return os.getenv(name, default).strip().lower() not in (
        "",
        "0",
        "false",
        "no",
    )


def warn_about_shared_passwords(passwords: dict[int, str]) -> list[str]:
    """Warn when levels share a password: one would solve the other."""
    levels_by_password: dict[str, list[int]] = {}
    for level, password in passwords.items():
        levels_by_password.setdefault(password, []).append(level)
    warnings = [
        f"Levels {', '.join(map(str, levels))} share a password"
        for levels in levels_by_password.values()
        if len(levels) > 1
    ]
    for warning in warnings:
        logger.warning("%s; give each level its own PASSWORD_*.", warning)
    return warnings


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    from ctf.app_config import settings

    warn_about_shared_passwords(settings.PASSWORDS)
    try:
        from ctf.leaderboard import prepare_database

        prepare_database()
    except (
        Exception
    ) as e:  # the agent still serves; the leaderboard retries later
        logger.error("Could not prepare the leaderboard database: %s", e)
    if _enabled("PREPARE_FLAGS", ""):
        from ctf.agents.tools import db_path
        from ctf.prepare_flags import prepare_flags

        logger.info("Seeding level flags into %s", db_path)
        prepare_flags(lancedb_persistent=True, db_path=db_path)
    if _enabled("DOWNLOAD_MODELS", "1"):
        from ctf.prepare_hf_models import download_models

        logger.info("Downloading guard models")
        download_models()


if __name__ == "__main__":
    main()
