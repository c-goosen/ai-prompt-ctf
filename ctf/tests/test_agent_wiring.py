"""Each level agent keeps the guards and router order its challenge relies on."""

from functools import partial

import pytest

from ctf.agents.sub_agents.agent import root_agent
from ctf.agents.sub_agents.guard_rails import (
    guard_rail_input_injection,
    guard_rail_output_injection,
)
from ctf.agents.sub_agents.protection_utils import ProtectionUtils
from ctf.app_config import settings

AGENTS = {agent.name: agent for agent in root_agent.sub_agents}

ROUTERS = [
    "level_greeting.<locals>.greet",
    "route_level_change.<locals>.route",
    "route_submit_request.<locals>.route",
]

INPUT_GUARDS = {
    1: [guard_rail_input_injection],
    6: [ProtectionUtils.llm_guard_prompt_injection_meta],
    7: [ProtectionUtils.llm_guard_prompt_injection_goose],
    10: [
        guard_rail_input_injection,
        ProtectionUtils.llm_guard_prompt_injection_meta,
        ProtectionUtils.llm_guard_prompt_injection_goose,
    ],
}

OUTPUT_GUARDS = {
    2: [guard_rail_output_injection],
    10: [ProtectionUtils.detect_password_leak],
}

LEVELS = range(settings.FINAL_LEVEL + 1)


def _callbacks(value) -> list:
    if value is None:
        return []
    return value if isinstance(value, list) else [value]


def _guards(value, level: int) -> list:
    """The level-bound guard functions among the callbacks, in order."""
    guards = []
    for callback in _callbacks(value):
        if isinstance(callback, partial):
            assert callback.keywords == {"level": level}
            guards.append(callback.func)
    return guards


def test_every_level_has_an_agent():
    assert sorted(AGENTS) == sorted(f"Level{level}Agent" for level in LEVELS)


@pytest.mark.parametrize("level", LEVELS)
def test_routers_run_before_the_guards(level):
    callbacks = _callbacks(AGENTS[f"Level{level}Agent"].before_model_callback)
    names = [getattr(callback, "__qualname__", "") for callback in callbacks]
    assert names[: len(ROUTERS)] == ROUTERS


@pytest.mark.parametrize("level", LEVELS)
def test_input_guards(level):
    agent = AGENTS[f"Level{level}Agent"]
    assert _guards(agent.before_model_callback, level) == INPUT_GUARDS.get(
        level, []
    )


@pytest.mark.parametrize("level", LEVELS)
def test_output_guards_screen_model_and_tool_output(level):
    agent = AGENTS[f"Level{level}Agent"]
    expected = OUTPUT_GUARDS.get(level, [])
    assert _guards(agent.after_model_callback, level) == expected
    assert _guards(agent.after_tool_callback, level) == expected


@pytest.mark.xfail(
    strict=True,
    raises=AttributeError,
    reason="BaseCTFAgent sets _level before pydantic's __init__, which drops it",
)
def test_level_property():
    assert AGENTS["Level1Agent"].level == 1
