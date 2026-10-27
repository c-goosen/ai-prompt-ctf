"""Deterministic level routing for the coordinator.

Small models such as qwen3:0.6b reason about calling transfer_to_agent and
then never emit the call, so "level N" requests are routed here without
asking the model.
"""

import re
from typing import Any, Optional

from google.adk.models import LlmRequest, LlmResponse
from google.genai import types

MAX_LEVEL = 10

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


def route_level_request(
    llm_request: LlmRequest | None = None, **_: Any
) -> Optional[LlmResponse]:
    """before_model_callback that transfers "level N" requests directly."""
    if not llm_request or not llm_request.contents:
        return None

    # Only the user's own turn: after a tool call the last content is a
    # function response, and re-routing then would loop.
    last = llm_request.contents[-1]
    if last.role != "user" or not last.parts:
        return None
    text = "\n".join(part.text for part in last.parts if part.text)
    level = requested_level(text)
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
