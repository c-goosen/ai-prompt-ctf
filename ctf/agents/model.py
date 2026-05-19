import os

from google.adk.models import Gemini
from google.adk.models.lite_llm import LiteLlm
from google.genai import types

from ctf.app_config import settings


def _use_gemini() -> bool:
    """Use Gemini when USE_GEMINI is truthy or GEMINI_MODEL_NAME is set."""
    flag = os.getenv("USE_GEMINI", "").lower()
    if flag in ("1", "true", "yes"):
        return True
    if flag in ("0", "false", "no"):
        return False
    return bool(os.getenv("GEMINI_MODEL_NAME"))


if _use_gemini():
    model_name = os.getenv("GEMINI_MODEL_NAME", "gemini-2.5-flash-lite")
    model = Gemini(
        retry_options=types.HttpRetryOptions(initial_delay=1, attempts=3),
        model=model_name,
    )
else:
    model_tag = settings.OPENSOURCE_LLM_MODEL
    litellm_model = (
        model_tag if "/" in model_tag else f"ollama_chat/{model_tag}"
    )
    ollama_base = settings.OLLAMA_API_BASE.rstrip("/")
    model = LiteLlm(model=litellm_model, api_base=ollama_base)
