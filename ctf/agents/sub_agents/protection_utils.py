"""
Enhanced protection utilities for CTF agents
"""

import json
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

llm_guard_meta = PromptGuardMeta()
llm_guard_goose_modernbert = PromptGuardGooseModernBERT()


def _extract_last_user_message(llm_request: LlmRequest) -> str:
    """Return the most recent user text from the request contents."""
    if not llm_request or not llm_request.contents:
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
        **_: Any,
    ) -> Optional[LlmResponse]:
        """Detect whether response text contains the level password.

        Wired as both an ``after_model_callback`` (ADK passes
        ``llm_response``) and an ``after_tool_callback`` (ADK passes
        ``tool_response``, a plain dict/value rather than an LlmResponse).
        """
        if llm_response:
            text = _extract_response_text(llm_response)
        elif tool_response is not None:
            text = json.dumps(tool_response, ensure_ascii=False)
        else:
            return None

        if not text:
            return None

        password = settings.PASSWORDS.get(level)
        if not password:
            return None

        if password.lower() in text.lower():
            return LlmResponse(
                content=types.Content(
                    role="model",
                    parts=[
                        types.Part(
                            text="LLM call was blocked by detect_password_leak."
                        )
                    ],
                )
            )

        return None
