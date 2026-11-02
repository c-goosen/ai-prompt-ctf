"""
Enhanced protection utilities for CTF agents
"""

import json
import logging
import re
from typing import Optional, Any

from google.adk.agents.callback_context import CallbackContext
from google.adk.models import LlmResponse, LlmRequest
from google.genai import types

from ctf.app_config import settings
from ctf.llm_guard import (
    PromptGuardMeta,
    PromptGuardGooseModernBERT,
)
from ctf.llm_guard.decision import attack_probability

logger = logging.getLogger(__name__)

llm_guard_meta = PromptGuardMeta()
llm_guard_goose_modernbert = PromptGuardGooseModernBERT()


def _extract_last_user_message(llm_request: LlmRequest) -> str:
    """Return the most recent user text from the request contents.

    Empty after a tool call: the model is called again within the same turn,
    and the player's message was already screened (or, for a submit, routed
    past the guards) when the turn began. Screening it again would block the
    model's reply to the tool result.
    """
    if not llm_request or not llm_request.contents:
        return ""
    if any(
        part.function_response for part in llm_request.contents[-1].parts or []
    ):
        return ""

    for content in reversed(llm_request.contents):
        if content.role != "user":
            continue

        if not content.parts:
            continue

        text_parts = [
            part.text.strip()
            for part in content.parts
            if getattr(part, "text", None)
        ]
        if text_parts:
            return "\n".join(text_parts)

    return ""


def _extract_response_text(llm_response: LlmResponse) -> str:
    """Return the text from the response contents."""
    if not llm_response or not llm_response.content:
        return ""

    if not llm_response.content.parts:
        return ""

    text_parts = [
        part.text.strip()
        for part in llm_response.content.parts
        if getattr(part, "text", None)
    ]
    if text_parts:
        return "\n".join(text_parts)

    return ""


def _callback_text(llm_response: LlmResponse | None, tool_response: Any) -> str:
    """Text to inspect in an after_model or after_tool callback.

    ADK passes ``llm_response`` to after_model callbacks and the raw tool
    result (usually a str) as ``tool_response`` to after_tool callbacks.
    """
    if llm_response:
        return _extract_response_text(llm_response)
    if tool_response is None:
        return ""
    if isinstance(tool_response, str):
        return tool_response
    return json.dumps(tool_response, ensure_ascii=False, default=str)


def player_sent(context: Any, password: str) -> bool:
    """Whether the player's own message this turn contains the password.

    Echoing a password the player just typed (say, in a submit) leaks nothing.
    `context` is the callback's CallbackContext or ToolContext.
    """
    content = getattr(context, "user_content", None)
    text = " ".join(
        part.text
        for part in (content.parts if content else None) or []
        if part.text
    )
    return password.lower() in text.lower()


def blocked_callback_result(
    message: str, llm_response: LlmResponse | None
) -> LlmResponse | dict[str, str]:
    """Replacement for a blocked response, in the shape the callback returns.

    An after_tool callback's return value becomes the tool's result, which
    must be a dict; an after_model callback returns an LlmResponse.
    """
    if llm_response is None:
        return {"result": message}
    return LlmResponse(
        content=types.Content(role="model", parts=[types.Part(text=message)])
    )


def _blocked(message: str) -> LlmResponse:
    return LlmResponse(
        content=types.Content(role="model", parts=[types.Part(text=message)])
    )


class ProtectionUtils:
    """Utility class for implementing various protection mechanisms"""

    @staticmethod
    async def llm_guard_prompt_injection_meta(
        *args: Any,
        level: int = 0,
        callback_context: CallbackContext | None = None,
        llm_request: LlmRequest | None = None,
        **_: Any,
    ) -> Optional[LlmResponse]:
        """Detect prompt injection patterns using Prompt-Guard Meta model"""
        if callback_context is None and args:
            callback_context = args[0]
        if llm_request is None and len(args) > 1:
            llm_request = args[1]
        last_user_message = _extract_last_user_message(llm_request)

        if not last_user_message:
            return None

        resp = await llm_guard_meta.query(last_user_message)
        is_injection = bool(
            resp["label"] == "INJECTION" and resp["score"] > 0.8
        )

        if is_injection:
            return LlmResponse(
                content=types.Content(
                    role="model",
                    parts=[
                        types.Part(
                            text="""LLM call was blocked by
                            https://huggingface.co/protectai/deberta-v3-base-prompt-injection-v2."""
                        )
                    ],
                )
            )

        return None

    @staticmethod
    async def llm_guard_prompt_injection_goose(
        *args: Any,
        level: int = 0,
        callback_context: CallbackContext | None = None,
        llm_request: LlmRequest | None = None,
        **_: Any,
    ) -> Optional[LlmResponse]:
        """Detect prompt injection patterns using Prompt-Goose fine-tuned model"""
        if callback_context is None and args:
            callback_context = args[0]
        if llm_request is None and len(args) > 1:
            llm_request = args[1]
        last_user_message = _extract_last_user_message(llm_request)

        if not last_user_message:
            return None

        resp = await llm_guard_goose_modernbert.query(last_user_message)
        is_injection = bool(
            resp["label"] == "INJECTION" and resp["score"] > 0.8
        )

        if is_injection:
            return LlmResponse(
                content=types.Content(
                    role="model",
                    parts=[
                        types.Part(
                            text="""LLM call was blocked by
                            https://huggingface.co/cgoosen/prompt-tackler_modernbert."""
                        )
                    ],
                )
            )

        return None

    @staticmethod
    async def decision_model_guard(
        *args: Any,
        level: int = 0,
        callback_context: CallbackContext | None = None,
        llm_request: LlmRequest | None = None,
        **_: Any,
    ) -> Optional[LlmResponse]:
        """Block prompts an Ollama decision model judges to be an attack.

        Fails closed: if the decision model can't be asked, the prompt is
        blocked, so an outage never leaves the level unguarded.
        """
        if callback_context is None and args:
            callback_context = args[0]
        if llm_request is None and len(args) > 1:
            llm_request = args[1]
        last_user_message = _extract_last_user_message(llm_request)

        if not last_user_message:
            return None

        try:
            probability = await attack_probability(last_user_message)
        except Exception as e:
            logger.error(
                f"Decision model {settings.DECISION_MODEL} failed: {e}"
            )
            return _blocked(
                f"LLM call was blocked: the decision model "
                f"{settings.DECISION_MODEL} is unavailable. Try again shortly."
            )

        if probability >= settings.DECISION_THRESHOLD:
            return _blocked(
                f"LLM call was blocked by the decision model "
                f"{settings.DECISION_MODEL}: it judged your message an attack "
                f"(p={probability:.2f}, threshold "
                f"{settings.DECISION_THRESHOLD:.2f})."
            )

        return None

    @staticmethod
    def detect_prompt_injection(text: str, level: int = 0) -> Optional[str]:
        """Detect prompt injection patterns based on level"""
        text_lower = text.lower()

        # Basic patterns for all levels
        basic_patterns = [
            r"ignore\s+(previous|all)\s+instructions",
            r"forget\s+(everything|all)",
            r"you\s+are\s+now",
            r"pretend\s+to\s+be",
            r"act\s+as\s+if",
            r"system\s+prompt",
            r"jailbreak",
            r"override",
            r"bypass",
            r"exploit",
        ]

        # Advanced patterns for higher levels
        advanced_patterns = [
            r"roleplay",
            r"simulation",
            r"hypothetical",
            r"what\s+if",
            r"imagine",
            r"suppose",
            r"assume",
            r"let's\s+pretend",
            r"in\s+a\s+world",
            r"if\s+you\s+were",
        ]

        # Check basic patterns
        for pattern in basic_patterns:
            if re.search(pattern, text_lower):
                return f"Basic injection pattern detected: '{pattern}'"

        # Check advanced patterns for higher levels
        if level >= 3:
            for pattern in advanced_patterns:
                if re.search(pattern, text_lower):
                    return f"Advanced injection pattern detected: '{pattern}'"

        return None

    @staticmethod
    def detect_password_leak(
        callback_context: CallbackContext | None = None,
        llm_response: LlmResponse | None = None,
        level: int = 0,
        tool_response: Any = None,
        tool_context: Any = None,
        **_: Any,
    ) -> LlmResponse | dict[str, str] | None:
        """Detect whether response text contains the level password.

        Wired as both an ``after_model_callback`` (ADK passes
        ``llm_response``) and an ``after_tool_callback`` (ADK passes
        ``tool_response``, a plain dict/value rather than an LlmResponse).
        A password the player typed this turn isn't a leak.
        """
        text = _callback_text(llm_response, tool_response)
        if not text:
            return None

        password = settings.PASSWORDS.get(level)
        if not password:
            return None

        if password.lower() in text.lower() and not player_sent(
            callback_context or tool_context, password
        ):
            return blocked_callback_result(
                "LLM call was blocked by detect_password_leak.", llm_response
            )

        return None
