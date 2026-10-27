"""Deterministic level routing for the coordinator.

Small models such as qwen3:0.6b reason about calling transfer_to_agent and
then never emit the call, so "level N" requests are routed here without
asking the model. Likewise the level agent greets the player on arrival
without a model call, instead of mistaking the transfer for a request, and
answers hint requests with a real hints_func call (the model sometimes
writes the call out as text instead).
"""

import re
from typing import Any, Optional

from google.adk.agents.callback_context import CallbackContext
from google.adk.models import LlmRequest, LlmResponse
from google.genai import types

MAX_LEVEL = 10

LEVEL_TITLES = {
    0: "Basic Prompt Injection",
    1: "Input Protection",
    2: "Output Protection",
    3: "Advanced Prompt Engineering & Thinking Protection",
    4: "Multi-Modal Injection",
    5: "Function Calling Injection",
    6: "Prompt-Guard Protection",
    7: "Prompt-Goose Protection",
    8: "Excessive Agency Code Generation",
    9: "Web Page Injection",
    10: "Hold the Fort",
}

_LEVEL_REQUEST = re.compile(
    r"""
    (?:
        (?:i\s+(?:want|would\s+like|wanna)\s+to\s+|let'?s\s+|can\s+i\s+)?
        (?:try|start|play|attempt|do|go\s+to|switch\s+to|move\s+to|
           take\s+me\s+to|start\s+me\s+on|put\s+me\s+on)\s+
    )?
    (?:on\s+)?(?:the\s+)?
    (?:level|lvl|lv)\s*\#?\s*(?P<level>\d{1,2})
    (?:\s+please)?
    """,
    re.IGNORECASE | re.VERBOSE,
)

# The web app's /hint command sends "Give me a hint for the current level."
# (or "...level: <question>"); players also just type "hint".
_HINT_REQUEST = re.compile(
    r"""
    (?:(?:give\s+me|can\s+i\s+(?:get|have)|i\s+(?:want|need))\s+)?
    (?:a\s+|another\s+)?hint
    (?:\s+for\s+(?:the\s+)?(?:current|this)\s+level)?
    (?:\s+please)?
    (?:\s*:\s*.*)?
    """,
    re.IGNORECASE | re.VERBOSE | re.DOTALL,
)


def requested_level(text: str) -> Optional[int]:
    """Return N when the whole message asks to play level N, else None.

    Only short, unambiguous requests match, so "hint for level 3" or
    "submit answer for level 2: ..." still go to the model.
    """
    cleaned = text.strip().rstrip("!.?").strip()
    match = _LEVEL_REQUEST.fullmatch(cleaned)
    if not match:
        return None
    level = int(match.group("level"))
    return level if level <= MAX_LEVEL else None


def _user_text(llm_request: LlmRequest | None) -> Optional[str]:
    """The text of the user's own turn, or None after a tool call."""
    if not llm_request or not llm_request.contents:
        return None
    last = llm_request.contents[-1]
    if last.role != "user" or not last.parts:
        return None
    return "\n".join(part.text for part in last.parts if part.text)


def route_level_request(
    llm_request: LlmRequest | None = None, **_: Any
) -> Optional[LlmResponse]:
    """before_model_callback that transfers "level N" requests directly."""
    # Only the user's own turn: after a tool call the last content is a
    # function response, and re-routing then would loop.
    text = _user_text(llm_request)
    level = requested_level(text) if text else None
    if level is None:
        return None

    return LlmResponse(
        content=types.Content(
            role="model",
            parts=[
                types.Part.from_function_call(
                    name="transfer_to_agent",
                    args={"agent_name": f"Level{level}Agent"},
                )
            ],
        )
    )


def level_greeting(level: int):
    """before_model_callback that greets the player right after a transfer."""

    def greet(
        callback_context: CallbackContext | None = None, **_: Any
    ) -> Optional[LlmResponse]:
        if not callback_context or not callback_context.session.events:
            return None
        last = callback_context.session.events[-1]
        if last.actions.transfer_to_agent != callback_context.agent_name:
            return None
        return LlmResponse(
            content=types.Content(
                role="model",
                parts=[types.Part(text=greeting_text(level))],
            )
        )

    return greet


def route_hint_request(level: int):
    """before_model_callback that turns a hint request into hints_func."""

    def route(
        llm_request: LlmRequest | None = None, **_: Any
    ) -> Optional[LlmResponse]:
        text = _user_text(llm_request)
        if not text or not _HINT_REQUEST.fullmatch(text.strip().rstrip("!.?")):
            return None
        return LlmResponse(
            content=types.Content(
                role="model",
                parts=[
                    types.Part.from_function_call(
                        name="hints_func",
                        args={"hint": text.strip(), "level": level},
                    )
                ],
            )
        )

    return route


def greeting_text(level: int) -> str:
    return (
        f"🎯 **Level {level}: {LEVEL_TITLES[level]}**\n\n"
        "You're now talking to this level's agent. Get it to reveal the "
        "password.\n\n"
        "Ask for a hint any time, and submit what you find with "
        '"submit answer: <password>".'
    )
