import logging
from typing import Any, Optional

from google.adk.agents.callback_context import CallbackContext
from google.adk.models import LlmRequest, LlmResponse
from google.genai import types

from ctf.app_config import settings
from ctf.agents.sub_agents.protection_utils import (
    ProtectionUtils,
    _callback_text,
    _extract_last_user_message,
    blocked_callback_result,
)

logger = logging.getLogger(__name__)


def guard_rail_input_injection(
    callback_context: CallbackContext | None = None,
    level: int = 0,
    llm_request: LlmRequest | None = None,
    **_: Any,
) -> Optional[LlmResponse]:
    """Guardrail for input injection"""
    last_user_message = _extract_last_user_message(llm_request)
    logger.debug("Inspecting last user message: %r", last_user_message)

    if not last_user_message:
        return None

    lowered_message = last_user_message.lower()
    injection_detected = ProtectionUtils.detect_prompt_injection(
        last_user_message, level
    )

    if "password" in lowered_message or injection_detected:
        return LlmResponse(
            content=types.Content(
                role="model",
                parts=[
                    types.Part(
                        text="""Prompt injection was blocked by guard_rail_input_injection,
                         before being sent to the model."""
                    )
                ],
            )
        )
    return None


def guard_rail_output_injection(
    callback_context: CallbackContext | None = None,
    llm_response: LlmResponse | None = None,
    level: int = 2,
    tool_response: Any = None,
    **_: Any,
) -> LlmResponse | dict[str, str] | None:
    """Guardrail for output: block responses/tool outputs leaking the password.

    Wired as an ``after_model_callback`` (ADK passes ``llm_response``) and as an
    ``after_tool_callback`` (ADK passes ``tool_response``, the raw tool result).
    """
    text = _callback_text(llm_response, tool_response)
    if not text:
        return None

    password = settings.PASSWORDS.get(level)
    if password and password.lower() in text.lower():
        return blocked_callback_result(
            "LLM response was blocked by guard_rail_output_injection.",
            llm_response,
        )
    return None
