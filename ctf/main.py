import os.path
import sys

sys.path.append(
    os.path.abspath(os.path.join(os.path.dirname(__file__), os.path.pardir))
)
import uvicorn  # noqa
from llm_guard.llm_guard import PromptGuardMeta  # noqa

import ssl

ssl._create_default_https_context = ssl._create_unverified_context

os.environ["CURL_CA_BUNDLE"] = ""
os.environ["REQUESTS_CA_BUNDLE"] = ""
if __name__ == "__main__":
    # if bool(os.getenv("PREPARE_FLAGS", False)):
    #     prepare_flags()
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        log_level="info",
        reload=os.getenv("RELOAD", True),
        port=8100,
        loop="asyncio",
    )
