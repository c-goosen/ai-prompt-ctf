"""
Start-up work for the agent container, run before `adk web`.

These used to run inside the FastAPI frontend; the Next.js web app can't do
them, and the agent is the only thing that uses the guard models and the
LanceDB flags anyway.

- PREPARE_FLAGS (unset by default): seed the LanceDB RAG store and the
  level 5 users.db with the level passwords.
- DOWNLOAD_MODELS (on by default): pre-download the Hugging Face guard
  models so the first guarded request doesn't stall on a download.
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


def main() -> None:
    logging.basicConfig(level=logging.INFO)
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
