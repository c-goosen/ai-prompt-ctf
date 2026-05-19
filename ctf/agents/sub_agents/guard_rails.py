from typing import Any, Optional

from google.adk.agents.callback_context import CallbackContext
from google.adk.models import LlmRequest, LlmResponse
from google.genai import types

from ctf.agents.sub_agents.protection_utils import (
    ProtectionUtils,
    _extract_last_user_message,
)


def guard_rail_input_injection(
    callback_context: CallbackContext | None = None,
    level: int = 0,
    llm_request: LlmRequest | None = None,
    **_: Any,
) -> Optional[LlmResponse]:
    """Guardrail for input injection"""
    last_user_message = _extract_last_user_message(llm_request)
    print(f"[Callback] Inspecting last user message: '{last_user_message}'")

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
    llm_request: LlmRequest | None = None,
    **_: Any,
) -> Optional[LlmResponse]:
    """Guardrail for output injection"""
    last_user_message = _extract_last_user_message(llm_request)
    if "password" in last_user_message.lower():
        return LlmResponse(
            content=types.Content(
                role="model",
                parts=[
                    types.Part(
                        text="LLM response was blocked by guard_rail_output_injection."
                    )
                ],
            )
        )
    return None
