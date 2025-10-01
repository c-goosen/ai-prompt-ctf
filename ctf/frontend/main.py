import os.path
import sys

# Add the project root to Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), os.path.pardir, os.path.pardir))
sys.path.insert(0, project_root)
import uvicorn  # noqa
from ctf.llm_guard.llm_guard import PromptGuardMeta  # noqa

import ssl

ssl._create_default_https_context = ssl._create_unverified_context

os.environ["CURL_CA_BUNDLE"] = ""
os.environ["REQUESTS_CA_BUNDLE"] = ""
if __name__ == "__main__":
    # if bool(os.getenv("PREPARE_FLAGS", False)):
    #     prepare_flags()
    uvicorn.run(
        "ctf.frontend.app:app",
        host="0.0.0.0",
        log_level="info",
        reload=os.getenv("RELOAD", True),
        port=8100,
        loop="asyncio",
    )
