import asyncio
import sys
import os.path

sys.path.append(
    os.path.abspath(os.path.join(os.path.dirname(__file__), os.path.pardir))
)
import uvicorn  # noqa
from llm_guard.llm_guard import PromptGuardMeta  # noqa

os.environ["CURL_CA_BUNDLE"] = ""
os.environ["REQUESTS_CA_BUNDLE"] = ""
if __name__ == "__main__":
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        log_level="info",
        reload=True,
        port=8100,
        loop="asyncio",
    )
