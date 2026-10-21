import os.path
import sys

# Add the project root to Python path
project_root = os.path.abspath(
    os.path.join(os.path.dirname(__file__), os.path.pardir, os.path.pardir)
)
sys.path.insert(0, project_root)
import uvicorn  # noqa
from ctf.llm_guard.llm_guard import PromptGuardMeta  # noqa


def _reload_enabled() -> bool:
    reload = os.getenv("RELOAD")
    if reload is not None:
        return reload.lower() in ("1", "true", "yes")
    return os.getenv("FASTAPI_ENV", "").lower() != "production"


if __name__ == "__main__":
    # if bool(os.getenv("PREPARE_FLAGS", False)):
    #     prepare_flags()
    uvicorn.run(
        "ctf.frontend.app:app",
        host="0.0.0.0",
        log_level="info",
        reload=_reload_enabled(),
        port=8100,
        loop="asyncio",
    )
