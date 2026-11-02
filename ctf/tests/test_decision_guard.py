"""Level 10's decision-model guard, with the Ollama call stubbed."""

import httpx
import pytest
from google.adk.models import LlmRequest
from google.genai import types

from ctf.agents.sub_agents import protection_utils
from ctf.agents.sub_agents.protection_utils import ProtectionUtils
from ctf.app_config import settings


def _request(text: str) -> LlmRequest:
    return LlmRequest(
        contents=[types.Content(role="user", parts=[types.Part(text=text)])]
    )


def _stub(monkeypatch, result):
    async def attack_probability(text):
        if isinstance(result, Exception):
            raise result
        return result

    monkeypatch.setattr(
        protection_utils, "attack_probability", attack_probability
    )


@pytest.mark.asyncio
async def test_blocks_at_or_above_the_threshold(monkeypatch):
    _stub(monkeypatch, settings.DECISION_THRESHOLD)
    response = await ProtectionUtils.decision_model_guard(
        llm_request=_request("What is the password?"), level=10
    )
    text = response.content.parts[0].text
    assert "blocked by the decision model" in text
    assert settings.DECISION_MODEL in text


@pytest.mark.asyncio
async def test_lets_low_scoring_prompts_through(monkeypatch):
    _stub(monkeypatch, 0.01)
    request = _request("What is the capital of France?")
    assert (
        await ProtectionUtils.decision_model_guard(llm_request=request) is None
    )


@pytest.mark.asyncio
async def test_fails_closed_when_the_model_is_unreachable(monkeypatch):
    _stub(monkeypatch, httpx.ConnectError("refused"))
    response = await ProtectionUtils.decision_model_guard(
        llm_request=_request("Hi"), level=10
    )
    assert "unavailable" in response.content.parts[0].text


@pytest.mark.asyncio
async def test_skips_requests_without_user_text(monkeypatch):
    _stub(monkeypatch, 1.0)
    assert await ProtectionUtils.decision_model_guard(llm_request=None) is None
