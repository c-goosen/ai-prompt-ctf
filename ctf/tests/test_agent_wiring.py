"""Each level agent keeps the guards and router order its challenge relies on."""

from functools import partial

import pytest

from ctf.agents.sub_agents.agent import root_agent
from ctf.agents.sub_agents.guard_rails import (
    guard_rail_input_injection,
    guard_rail_output_injection,
)
from ctf.agents.sub_agents.level_12_agent import guard_other_tools
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
    10: [ProtectionUtils.decision_model_guard],
    12: [guard_rail_input_injection],
    15: [
        guard_rail_input_injection,
        ProtectionUtils.llm_guard_prompt_injection_meta,
        ProtectionUtils.llm_guard_prompt_injection_goose,
        ProtectionUtils.decision_model_guard,
    ],
}

OUTPUT_GUARDS = {
    2: [guard_rail_output_injection],
    12: [ProtectionUtils.detect_password_leak],
    14: [ProtectionUtils.detect_password_leak],
    15: [ProtectionUtils.detect_password_leak],
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
    # Level 14's defence is all on the way in, so only its tools are guarded.
    model_expected = [] if level == 14 else expected
    assert _guards(agent.after_model_callback, level) == model_expected
    # Level 12 guards every tool but call_plugin, its way in (see below).
    tool_expected = [] if level == 12 else expected
    assert _guards(agent.after_tool_callback, level) == tool_expected


def test_poisoned_plugin_leaves_only_the_plugin_call_unguarded():
    callbacks = _callbacks(AGENTS["Level12Agent"].after_tool_callback)
    assert callbacks == [guard_other_tools]


@pytest.mark.xfail(
    strict=True,
    raises=AttributeError,
    reason="BaseCTFAgent sets _level before pydantic's __init__, which drops it",
)
def test_level_property():
    assert AGENTS["Level1Agent"].level == 1
