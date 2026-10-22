import os
from typing import AsyncGenerator

from google.adk.models import Gemini, LlmRequest, LlmResponse
from google.adk.models.lite_llm import LiteLlm
from google.adk.planners import BuiltInPlanner
from google.genai import types

from ctf.app_config import settings


def thinking_planner(thinking_budget: int = 1024) -> BuiltInPlanner:
    """Planner that asks the model to return its thoughts with each response."""
    return BuiltInPlanner(
        thinking_config=types.ThinkingConfig(
            include_thoughts=True,
            thinking_budget=thinking_budget,
        )
    )


class ThinkingLiteLlm(LiteLlm):
    """LiteLlm that honours thinking_config.include_thoughts.

    ADK doesn't map thinking_config to LiteLLM, and reasoning models such as
    qwen3 on Ollama think by default, so drop thought parts unless asked for.
    """

    async def generate_content_async(
        self, llm_request: LlmRequest, stream: bool = False
    ) -> AsyncGenerator[LlmResponse, None]:
        thinking = llm_request.config.thinking_config
        include_thoughts = bool(thinking and thinking.include_thoughts)
        async for response in super().generate_content_async(
            llm_request, stream
        ):
            if not include_thoughts and response.content:
                response.content.parts = [
                    part
                    for part in response.content.parts or []
                    if not part.thought
                ]
            yield response


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
    model = ThinkingLiteLlm(model=litellm_model, api_base=ollama_base)
