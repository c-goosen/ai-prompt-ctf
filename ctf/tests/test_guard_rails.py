"""Output guardrails, wired as both after_model and after_tool callbacks."""

import pytest
from google.adk.models import LlmResponse
from google.genai import types

from ctf.agents.sub_agents.guard_rails import guard_rail_output_injection
from ctf.agents.sub_agents.protection_utils import ProtectionUtils
from ctf.app_config import settings

GUARDS = [
    (guard_rail_output_injection, 2),
    (ProtectionUtils.detect_password_leak, 10),
]


def _model_response(text: str) -> LlmResponse:
    return LlmResponse(
        content=types.Content(role="model", parts=[types.Part(text=text)])
    )


@pytest.mark.parametrize("guard,level", GUARDS)
def test_string_tool_result_without_leak_passes(guard, level):
    assert guard(tool_response="Here is a hint.", level=level) is None


@pytest.mark.parametrize("guard,level", GUARDS)
def test_tool_result_with_leak_returns_dict(guard, level):
    password = settings.PASSWORDS[level]
    for tool_response in (f"it is {password}", {"result": password}):
        blocked = guard(tool_response=tool_response, level=level)
        assert isinstance(blocked, dict)
        assert password not in blocked["result"]


@pytest.mark.parametrize("guard,level", GUARDS)
def test_model_response_with_leak_returns_llm_response(guard, level):
    password = settings.PASSWORDS[level]
    blocked = guard(llm_response=_model_response(password), level=level)
    assert isinstance(blocked, LlmResponse)
    assert password not in blocked.content.parts[0].text


@pytest.mark.parametrize("guard,level", GUARDS)
def test_model_response_without_leak_passes(guard, level):
    assert guard(llm_response=_model_response("hello"), level=level) is None
